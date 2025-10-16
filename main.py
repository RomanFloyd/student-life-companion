from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import json, sqlite3, time, os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Fix OpenMP conflict BEFORE importing sentence-transformers
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
os.environ['OMP_NUM_THREADS'] = '1'

# Semantic search with embeddings
from sentence_transformers import SentenceTransformer, util

# Groq LLM
from groq import Groq

app = FastAPI(title="Student Life Companion")

# Монтируем статику ПЕРЕД middleware
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

KB_PATH = Path("knowledge_base.json")
DB_PATH = Path("notebook.db")

def load_kb():
    with KB_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)

KNOWLEDGE = load_kb()

# Load Sentence Transformer model
print("🚀 Loading Sentence Transformer model (all-MiniLM-L6-v2)...")
try:
    EMBEDDING_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
    print("✅ Model loaded successfully!")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    raise

def build_semantic_index(kb):
    """Create embeddings for all questions in knowledge base"""
    print(f"📊 Creating embeddings for {len(kb)} questions...")
    texts = [f"{item.get('question','')} {item.get('answer','')[:100]}" for item in kb]
    embeddings = EMBEDDING_MODEL.encode(texts, convert_to_tensor=True, show_progress_bar=False)
    print("✅ Embeddings created!")
    return embeddings

KB_EMBEDDINGS = build_semantic_index(KNOWLEDGE)

def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts INTEGER,
        query TEXT,
        answer TEXT,
        matched_question TEXT,
        topic TEXT,
        similarity REAL,
        source TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ratings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts INTEGER,
        question TEXT,
        topic TEXT,
        rating INTEGER,
        user_query TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_profiles (
        user_id TEXT PRIMARY KEY,
        profile_type TEXT,
        created_at INTEGER,
        updated_at INTEGER
    )
    """)
    con.commit(); con.close()

init_db()

class QAResponse(BaseModel):
    answer: str
    matched_question: Optional[str] = None
    topic: Optional[str] = None
    steps: Optional[List[str]] = None
    source_url: Optional[str] = None
    verified: Optional[bool] = None
    similarity: Optional[float] = None
    source: str
    cost: Optional[str] = None
    contacts: Optional[List[dict]] = None
    quick_links: Optional[List[dict]] = None
    deadline: Optional[str] = None
    related_topics: Optional[List[str]] = None

def save_history(row: QAResponse, query: str):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        "INSERT INTO history (ts, query, answer, matched_question, topic, similarity, source) VALUES (?,?,?,?,?,?,?)",
        (int(time.time()), query, row.answer, row.matched_question, row.topic, row.similarity or None, row.source)
    )
    con.commit(); con.close()

@app.get("/")
def home():
    return {"message": "Student Life Companion API is running"}

@app.get("/reload")
def reload_kb():
    global KNOWLEDGE, KB_EMBEDDINGS
    KNOWLEDGE = load_kb()
    KB_EMBEDDINGS = build_semantic_index(KNOWLEDGE)
    return {"status": "reloaded", "items": len(KNOWLEDGE)}

def get_question_rating_boost(question: str) -> float:
    """Get rating boost for a question (0.0 to 0.1)"""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        SELECT SUM(rating) as score, COUNT(*) as total
        FROM ratings
        WHERE question = ?
    """, (question,))
    row = cur.fetchone()
    con.close()
    
    if not row or row[1] == 0:
        return 0.0
    
    score = row[0] or 0
    total = row[1]
    # Boost: +0.05 per positive rating, max +0.1
    boost = min(0.1, (score / total) * 0.05)
    return boost

def check_relevance_with_groq(query: str, matched_question: str, matched_answer: str) -> bool:
    """Ask Groq if the matched answer is relevant to the user's query"""
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        
        prompt = f"""You are a relevance checker. Determine if the ANSWER is relevant to the USER QUERY.

USER QUERY: "{query}"

MATCHED QUESTION: "{matched_question}"
MATCHED ANSWER: "{matched_answer[:200]}..."

Is this answer relevant to the user's query? Answer ONLY with "YES" or "NO".
- YES: if the answer addresses the user's question
- NO: if the answer is about a different topic

Answer:"""
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=10
        )
        
        answer = response.choices[0].message.content.strip().upper()
        return answer == "YES"
        
    except Exception as e:
        print(f"Groq relevance check error: {e}")
        return True  # If error, assume relevant (safer)

def ask_groq_llm(query: str) -> str:
    """Fallback to Groq LLM when no answer found in knowledge base"""
    try:
        # Get API key from environment variable
        api_key = os.getenv("GROQ_API_KEY")
        
        if not api_key:
            return "I couldn't find an answer in my knowledge base. Please try rephrasing your question or contact student.experience@harbour.space"
        
        client = Groq(api_key=api_key)
        
        # Create context from knowledge base topics
        topics = set(item.get("topic", "") for item in KNOWLEDGE)
        context = f"You are a helpful AI assistant for Harbour.Space University students in Barcelona. You help with: {', '.join(topics)}. Be concise and helpful."
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Free, fast model
            messages=[
                {"role": "system", "content": context},
                {"role": "user", "content": query}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"Groq API error: {e}")
        return "I couldn't find an answer in my knowledge base. Please try rephrasing your question or contact student.experience@harbour.space"

def check_topic_relevance(query: str, matched_item: dict) -> bool:
    """Check if matched question is actually relevant to the query"""
    query_lower = query.lower()
    question_lower = matched_item.get("question", "").lower()
    answer_lower = matched_item.get("answer", "").lower()
    topic = matched_item.get("topic", "")
    
    # Extract key nouns from query (simple approach)
    query_words = set(query_lower.split())
    question_words = set(question_lower.split())
    
    # Check for non-KB query patterns (recommendations, jokes, weather, etc.)
    non_kb_keywords = {'best', 'top', 'recommend', 'suggestion', 'joke', 'funny', 'weather', 'forecast', 'temperature', 'climate'}
    if query_words & non_kb_keywords:
        return False  # These should go to Groq AI
    
    # Remove common words
    stop_words = {'how', 'to', 'what', 'where', 'when', 'why', 'is', 'are', 'the', 'a', 'an', 'in', 'on', 'at', 'for', 'with', 'about', 'tell', 'me', 'can', 'i', 'do', 'does', 'spain', 'spanish', 'barcelona'}
    query_keywords = query_words - stop_words
    question_keywords = question_words - stop_words
    
    # Check if at least one meaningful keyword matches (excluding generic location words)
    common_keywords = query_keywords & question_keywords
    
    # If no common keywords, probably not relevant
    if len(common_keywords) == 0:
        return False
    
    # If only "spanish" or "barcelona" matches, not relevant enough
    if common_keywords <= {'spanish', 'barcelona', 'spain'}:
        return False
    
    # Check topic relevance
    topic_keywords = {
        'visa': {'visa', 'tie', 'residence', 'permit', 'immigration', 'extranjeria'},
        'work': {'work', 'job', 'employment', 'internship', 'salary'},
        'housing': {'housing', 'apartment', 'flat', 'rent', 'empadronamiento', 'landlord'},
        'transport': {'transport', 'metro', 'bus', 'train', 'tjove', 'ticket'},
        'mobile': {'mobile', 'phone', 'sim', 'esim', 'vodafone', 'movistar'},
        'university': {'programming', 'coding', 'computer', 'science', 'capstone', 'module', 'exam', 'grade', 'professor'},
        'life': {'language', 'school', 'course', 'food', 'restaurant', 'beach', 'discount', 'fish', 'seafood'}
    }
    
    # If query has specific topic keywords but matched different topic, reject
    for topic_name, keywords in topic_keywords.items():
        if query_keywords & keywords and topic != topic_name:
            return False
    
    return True

@app.get("/ask", response_model=QAResponse)
def ask(query: str, min_score: float = 0.35, autosave: bool = True):
    # Encode query using Sentence Transformer
    query_embedding = EMBEDDING_MODEL.encode(query, convert_to_tensor=True)
    
    # Calculate cosine similarity with all knowledge base embeddings
    similarities = util.cos_sim(query_embedding, KB_EMBEDDINGS)[0]
    
    # Apply rating boost to similarity scores
    for idx, item in enumerate(KNOWLEDGE):
        question = item.get("question", "")
        boost = get_question_rating_boost(question)
        similarities[idx] += boost
    
    # Find best match
    best_idx = int(similarities.argmax())
    best_score = float(similarities[best_idx])
    best_item = KNOWLEDGE[best_idx]
    
    # Three-tier relevance check:
    # 1. High confidence (>0.6): Use internal answer
    # 2. Medium confidence (0.35-0.6): Ask Groq to verify relevance
    # 3. Low confidence (<0.35): Go straight to Groq
    
    if best_score >= 0.6:
        # High confidence - use internal answer directly
        is_relevant = check_topic_relevance(query, best_item)
    elif best_score >= min_score:
        # Medium confidence - ask Groq to verify
        is_relevant = check_relevance_with_groq(
            query, 
            best_item.get("question", ""),
            best_item.get("answer", "")
        )
    else:
        # Low confidence - skip to Groq
        is_relevant = False

    if best_score >= min_score and is_relevant:
        item = KNOWLEDGE[best_idx]
        resp = QAResponse(
            answer=item.get("answer",""),
            matched_question=item.get("question"),
            topic=item.get("topic"),
            steps=item.get("steps"),
            source_url=item.get("source_url"),
            verified=item.get("verified"),
            similarity=round(best_score, 3),
            source="internal-semantic",
            cost=item.get("cost"),
            contacts=item.get("contacts"),
            quick_links=item.get("quick_links"),
            deadline=item.get("deadline"),
            related_topics=item.get("related_topics")
        )
        if autosave: save_history(resp, query)
        return resp

    # keyword fallback
    ql = query.lower()
    for item in KNOWLEDGE:
        if item.get("topic") and item["topic"] in ql:
            resp = QAResponse(
                answer=item.get("answer",""),
                matched_question=item.get("question"),
                topic=item.get("topic"),
                steps=item.get("steps"),
                source_url=item.get("source_url"),
                verified=item.get("verified"),
                similarity=None,
                source="internal-fallback",
                cost=item.get("cost"),
                contacts=item.get("contacts"),
                quick_links=item.get("quick_links"),
                deadline=item.get("deadline"),
                related_topics=item.get("related_topics")
            )
            if autosave: save_history(resp, query)
            return resp

    # Groq LLM fallback
    llm_answer = ask_groq_llm(query)
    resp = QAResponse(
        answer=llm_answer,
        matched_question=None, 
        topic="general", 
        steps=None, 
        source_url=None,
        verified=False, 
        similarity=None, 
        source="llm-groq",
        cost=None, 
        contacts=[{"type": "email", "label": "Student Experience", "value": "student.experience@harbour.space"}], 
        quick_links=None, 
        deadline=None, 
        related_topics=None
    )
    if autosave: save_history(resp, query)
    return resp

@app.get("/history")
def history(limit: int = 20):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT ts, query, answer, source FROM history ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    con.close()
    return [{"ts": r[0], "query": r[1], "answer": r[2], "source": r[3]} for r in rows]

@app.get("/topics")
def get_topics():
    """Get all unique topics with counts"""
    topics = {}
    for item in KNOWLEDGE:
        topic = item.get("topic", "other")
        topics[topic] = topics.get(topic, 0) + 1
    return {"topics": topics}

@app.get("/questions/{topic}")
def get_questions_by_topic(topic: str):
    """Get all questions for a specific topic"""
    questions = [
        {
            "question": item.get("question"),
            "answer": item.get("answer"),
            "topic": item.get("topic")
        }
        for item in KNOWLEDGE
        if item.get("topic", "").lower() == topic.lower()
    ]
    return {"topic": topic, "count": len(questions), "questions": questions}

class RatingRequest(BaseModel):
    question: str
    topic: Optional[str] = None
    rating: int  # 1 for 👍, -1 for 👎
    user_query: Optional[str] = None

@app.post("/rate")
def rate_answer(req: RatingRequest):
    """Save answer rating"""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        "INSERT INTO ratings (ts, question, topic, rating, user_query) VALUES (?,?,?,?,?)",
        (int(time.time()), req.question, req.topic, req.rating, req.user_query)
    )
    con.commit()
    con.close()
    return {"status": "success", "message": "Rating saved"}

class ProfileRequest(BaseModel):
    user_id: str
    profile_type: str  # student-longterm, teacher-shortterm, exchange-visiting, just-arrived

@app.post("/profile")
def set_user_profile(req: ProfileRequest):
    """Set or update user profile"""
    valid_profiles = ["student-longterm", "teacher-shortterm", "exchange-visiting", "just-arrived"]
    if req.profile_type not in valid_profiles:
        return {"status": "error", "message": f"Invalid profile. Choose from: {valid_profiles}"}
    
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    
    # Check if profile exists
    cur.execute("SELECT user_id FROM user_profiles WHERE user_id = ?", (req.user_id,))
    exists = cur.fetchone()
    
    ts = int(time.time())
    if exists:
        cur.execute(
            "UPDATE user_profiles SET profile_type = ?, updated_at = ? WHERE user_id = ?",
            (req.profile_type, ts, req.user_id)
        )
    else:
        cur.execute(
            "INSERT INTO user_profiles (user_id, profile_type, created_at, updated_at) VALUES (?,?,?,?)",
            (req.user_id, req.profile_type, ts, ts)
        )
    
    con.commit()
    con.close()
    return {"status": "success", "profile": req.profile_type}

@app.get("/profile/{user_id}")
def get_user_profile(user_id: str):
    """Get user profile"""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT profile_type, created_at FROM user_profiles WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    con.close()
    
    if not row:
        return {"status": "not_found", "profile": None}
    
    return {"status": "success", "profile": row[0], "created_at": row[1]}

@app.get("/profiles")
def get_available_profiles():
    """Get list of available profiles"""
    profiles = [
        {
            "id": "student-longterm",
            "name": "📚 Student (long-term)",
            "description": "Full degree program (1-4 years)",
            "topics": ["visa", "housing", "banking", "healthcare", "transport", "mobile", "university", "admin", "work", "life"]
        },
        {
            "id": "teacher-shortterm",
            "name": "👨‍🏫 Teacher (3-9 weeks)",
            "description": "Short-term teaching position",
            "topics": ["housing", "transport", "life", "mobile"]
        },
        {
            "id": "exchange-visiting",
            "name": "🌍 Exchange/Visiting (3-9 weeks)",
            "description": "Exchange student or visiting researcher",
            "topics": ["housing", "transport", "mobile", "life", "university"]
        },
        {
            "id": "just-arrived",
            "name": "🛬 Just Arrived (first week)",
            "description": "Survival guide for your first days",
            "topics": ["transport", "mobile", "life", "housing"]
        }
    ]
    return {"profiles": profiles}

@app.get("/popular")
def get_popular_questions(limit: int = 5):
    """Get most popular questions based on positive ratings"""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        SELECT question, topic, 
               SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) as likes,
               SUM(CASE WHEN rating = -1 THEN 1 ELSE 0 END) as dislikes,
               SUM(rating) as score
        FROM ratings
        GROUP BY question
        ORDER BY score DESC, likes DESC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    con.close()
    return [
        {
            "question": r[0],
            "topic": r[1],
            "likes": r[2],
            "dislikes": r[3],
            "score": r[4]
        }
        for r in rows
    ]

@app.get("/needs-improvement")
def get_needs_improvement(limit: int = 5):
    """Get questions with most negative ratings"""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        SELECT question, topic, 
               SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) as likes,
               SUM(CASE WHEN rating = -1 THEN 1 ELSE 0 END) as dislikes,
               SUM(rating) as score
        FROM ratings
        GROUP BY question
        HAVING dislikes > 0
        ORDER BY score ASC, dislikes DESC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    con.close()
    return [
        {
            "question": r[0],
            "topic": r[1],
            "likes": r[2],
            "dislikes": r[3],
            "score": r[4]
        }
        for r in rows
    ]
