from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import json, sqlite3, time, os
from pathlib import Path

# semantic search
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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

def build_semantic_index(kb):
    texts = [f"{item.get('question','')} {item.get('topic','')}" for item in kb]
    vec = TfidfVectorizer(stop_words="english")
    X = vec.fit_transform(texts)
    return vec, X

VECTORIZER, KB_MATRIX = build_semantic_index(KNOWLEDGE)

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
    global KNOWLEDGE, VECTORIZER, KB_MATRIX
    KNOWLEDGE = load_kb()
    VECTORIZER, KB_MATRIX = build_semantic_index(KNOWLEDGE)
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
            model="llama-3.1-70b-versatile",  # Free, fast model
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

@app.get("/ask", response_model=QAResponse)
def ask(query: str, min_score: float = 0.28, autosave: bool = True):
    q_vec = VECTORIZER.transform([query])
    sims = cosine_similarity(q_vec, KB_MATRIX)[0]
    
    # Apply rating boost to similarity scores
    for idx, item in enumerate(KNOWLEDGE):
        question = item.get("question", "")
        boost = get_question_rating_boost(question)
        sims[idx] += boost
    
    best_idx = int(sims.argmax())
    best_score = float(sims[best_idx])

    if best_score >= min_score:
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
