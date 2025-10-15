"""
Student Life Companion API
A FastAPI application providing personal assistant and Q&A services for university students.
"""

# ===================================================================
# STANDARD LIBRARY IMPORTS
# ===================================================================
import json
import os
import sqlite3
import time
from pathlib import Path
from typing import List, Optional

# ===================================================================
# THIRD-PARTY IMPORTS
# ===================================================================
# FastAPI
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Machine Learning
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
import pandas as pd

# Database
from pymongo import MongoClient
from bson.objectid import ObjectId

# LLM
from groq import Groq

# Environment
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Fix OpenMP conflict BEFORE importing sentence-transformers
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
os.environ['OMP_NUM_THREADS'] = '1'

# Semantic search with embeddings
from sentence_transformers import SentenceTransformer, util

# ===================================================================
# CONFIGURATION
# ===================================================================
# MongoDB Configuration
MONGO_URI = "mongodb://admin:admin123@localhost:27017/harbour-space?authSource=admin"
DATABASE_NAME = "harbour-space"

# File Paths
KB_PATH = Path("knowledge_base.json")
DB_PATH = Path("notebook.db")

# Semantic Search Thresholds
DEFAULT_MIN_SCORE = 0.28

# Initialize FastAPI app
app = FastAPI(title="Student Life Companion")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables (initialized later)
KNOWLEDGE = []
KB_EMBEDDINGS = None
VECTORIZER = None
KB_MATRIX = None
EMBEDDING_MODEL = None
personal_intent_clf = None
db = None

# ===================================================================
# PYDANTIC MODELS
# ===================================================================
class QAResponse(BaseModel):
    """Response model for Q&A endpoint."""
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


class PersonalQuery(BaseModel):
    """Request model for personal assistant queries."""
    user_id: str
    query: str


class PersonalResponse(BaseModel):
    """Response model for personal assistant."""
    intent: str
    response: dict | List | str


class RatingRequest(BaseModel):
    """Request model for answer ratings."""
    question: str
    topic: Optional[str] = None
    rating: int  # 1 for 👍, -1 for 👎
    user_query: Optional[str] = None


# ===================================================================
# DATABASE INITIALIZATION
# ===================================================================
def init_mongodb() -> Optional[any]:
    """
    Initialize MongoDB connection.
    
    Returns:
        Database instance if successful, None otherwise
    """
    try:
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        client.admin.command('ping')
        print("✅ MongoDB connection for Personal Assistant successful.")
        return db
    except Exception as e:
        print(f"❌ Error connecting to MongoDB for Personal Assistant: {e}")
        return None


def init_sqlite():
    """Initialize SQLite database for history and ratings."""
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
    con.commit()
    con.close()


def save_history(response: QAResponse, query: str):
    """
    Save query and response to history database.
    
    Args:
        response: QA response object
        query: User's original query
    """
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        "INSERT INTO history (ts, query, answer, matched_question, topic, similarity, source) VALUES (?,?,?,?,?,?,?)",
        (
            int(time.time()),
            query,
            response.answer,
            response.matched_question,
            response.topic,
            response.similarity,
            response.source
        )
    )
    con.commit()
    con.close()


# ===================================================================
# KNOWLEDGE BASE FUNCTIONS
# ===================================================================
def load_kb() -> List[dict]:
    """
    Load knowledge base from JSON file.
    
    Returns:
        List of knowledge base items
    """
    with KB_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_semantic_index(kb: List[dict]) -> tuple:
    """
    Build TF-IDF semantic search index from knowledge base.
    
    Args:
        kb: Knowledge base items
        
    Returns:
        Tuple of (vectorizer, matrix)
    """
    texts = [f"{item.get('question','')} {item.get('topic','')}" for item in kb]
    vec = TfidfVectorizer(stop_words="english")
    X = vec.fit_transform(texts)
    return vec, X


def build_embeddings_index(kb: List[dict]):
    """
    Create embeddings for all questions in knowledge base.
    
    Args:
        kb: Knowledge base items
        
    Returns:
        Tensor of embeddings
    """
    print(f"📊 Creating embeddings for {len(kb)} questions...")
    texts = [f"{item.get('question','')} {item.get('answer','')[:100]}" for item in kb]
    embeddings = EMBEDDING_MODEL.encode(texts, convert_to_tensor=True, show_progress_bar=False)
    print("✅ Embeddings created!")
    return embeddings


# ===================================================================
# PERSONAL ASSISTANT FUNCTIONS
# ===================================================================
def generate_training_data_from_db() -> pd.DataFrame:
    """
    Dynamically creates a training dataset for intents by fetching
    data directly from MongoDB.
    
    Returns:
        DataFrame with question and intent columns
    """
    if db is None:
        print("⚠️ Database connection not available. Cannot generate training data.")
        return pd.DataFrame()

    training_data = []
    
    # --- Intent: get_course_info ---
    courses = db.courses.find({}, {"name": 1, "teacher": 1})
    for course in courses:
        training_data.append({"question": f"Tell me about the {course['name']} course", "intent": "get_course_info"})
        training_data.append({"question": f"Who teaches {course['name']}", "intent": "get_course_info"})
        training_data.append({"question": f"What is {course['name']}", "intent": "get_course_info"})
        training_data.append({"question": f"{course['name']} info", "intent": "get_course_info"})
        training_data.append({"question": f"Information about {course['name']}", "intent": "get_course_info"})

    # --- Intent: get_group_info ---
    groups = db.groups.find({}, {"name": 1})
    for group in groups:
        training_data.append({"question": f"What is the {group['name']} group", "intent": "get_group_info"})
        training_data.append({"question": f"Tell me about the {group['name']}", "intent": "get_group_info"})

    # --- Generic intents for personalized questions ---
    schedule_questions = ["What is my schedule?", "Show me my classes for today", "What's on my calendar?", "When are my classes?", "Do I have class today?"]
    for q in schedule_questions:
        training_data.append({"question": q, "intent": "get_my_schedule"})

    groups_questions = [
        "What groups am I in?", 
        "List my clubs", 
        "Show me my communities",
        "What's my groups?",
        "Which groups am I part of?",
        "Show my group memberships",
        "What communities do I belong to?",
        "Tell me about my groups"
    ]
    for q in groups_questions:
        training_data.append({"question": q, "intent": "list_my_groups"})
        
    # --- Greeting and Goodbye Intents ---
    greetings = ["Hi", "Hello", "Hey there"]
    for q in greetings:
        training_data.append({"question": q, "intent": "greet"})
    
    goodbyes = ["Bye", "Goodbye", "See you later"]
    for q in goodbyes:
        training_data.append({"question": q, "intent": "goodbye"})

    return pd.DataFrame(training_data)


def train_personal_intent_model() -> Optional[Pipeline]:
    """
    Train the personal intent classification model.
    
    Returns:
        Trained pipeline or None if training fails
    """
    print("🚀 Training personal intent model from database data...")
    df_intents = generate_training_data_from_db()
    
    if df_intents.empty:
        print("⚠️ Could not train personal intent model due to lack of data or DB connection.")
        return None
    
    clf = Pipeline([
        ('tfidf', TfidfVectorizer()),
        ('clf', LinearSVC(dual="auto")),
    ])
    clf.fit(df_intents['question'], df_intents['intent'])
    print("✅ Personal intent model trained successfully.")
    return clf


def format_schedule(schedule_docs: List[dict]) -> str:
    """
    Helper function to format schedule data into a readable string.
    
    Args:
        schedule_docs: List of schedule documents from database
        
    Returns:
        Formatted schedule string
    """
    if not schedule_docs:
        return "You have no upcoming events on your schedule."
    
    response_lines = ["Here is your schedule:"]
    for item in schedule_docs:
        course = db.courses.find_one({"_id": ObjectId(item['courseId'])})
        course_name = course['name'] if course else "Unknown Course"
        start_time = item['startTime'].strftime('%Y-%m-%d %H:%M')
        response_lines.append(f"- {course_name} at {start_time}")
    return "\n".join(response_lines)


# ===================================================================
# INITIALIZATION
# ===================================================================
def initialize_application():
    """Initialize all application components."""
    global KNOWLEDGE, KB_EMBEDDINGS, VECTORIZER, KB_MATRIX, EMBEDDING_MODEL, personal_intent_clf, db
    
    print("🚀 Initializing Student Life Companion API...")
    
    # Initialize databases
    print("📊 Connecting to databases...")
    db = init_mongodb()
    init_sqlite()
    
    # Load Sentence Transformer model
    print("🤖 Loading Sentence Transformer model (all-MiniLM-L6-v2)...")
    try:
        EMBEDDING_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Model loaded successfully!")
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        raise
    
    # Initialize knowledge base
    print("📚 Loading knowledge base...")
    KNOWLEDGE = load_kb()
    VECTORIZER, KB_MATRIX = build_semantic_index(KNOWLEDGE)
    KB_EMBEDDINGS = build_embeddings_index(KNOWLEDGE)
    print(f"✅ Knowledge base loaded with {len(KNOWLEDGE)} items")
    
    # Train personal intent model
    personal_intent_clf = train_personal_intent_model()
    
    print("✅ Application initialized successfully!")


# Initialize the application
initialize_application()


# ===================================================================
# API ENDPOINTS - KNOWLEDGE BASE
# ===================================================================
@app.get("/reload")
def reload_kb():
    """Reload knowledge base and rebuild indexes."""
    global KNOWLEDGE, KB_EMBEDDINGS, VECTORIZER, KB_MATRIX
    KNOWLEDGE = load_kb()
    VECTORIZER, KB_MATRIX = build_semantic_index(KNOWLEDGE)
    KB_EMBEDDINGS = build_embeddings_index(KNOWLEDGE)
    return {"status": "reloaded", "items": len(KNOWLEDGE)}


@app.get("/topics")
def get_topics():
    """Get all unique topics with counts from knowledge base."""
    topics = {}
    for item in KNOWLEDGE:
        topic = item.get("topic", "other")
        topics[topic] = topics.get(topic, 0) + 1
    return {"topics": topics}


@app.get("/questions/{topic}")
def get_questions_by_topic(topic: str):
    """
    Get all questions for a specific topic.
    
    Args:
        topic: Topic name to filter by
        
    Returns:
        Dictionary with topic, count, and list of questions
    """
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


# ===================================================================
# RATING AND HISTORY FUNCTIONS
# ===================================================================
def get_question_rating_boost(question: str) -> float:
    """
    Get rating boost for a question based on user feedback.
    
    Args:
        question: The question to check ratings for
        
    Returns:
        Boost value between 0.0 and 0.1
    """
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


# ===================================================================
# RELEVANCE CHECK FUNCTIONS
# ===================================================================
def check_relevance_with_groq(query: str, matched_question: str, matched_answer: str) -> bool:
    """
    Ask Groq if the matched answer is relevant to the user's query.
    
    Args:
        query: User's query
        matched_question: Matched question from KB
        matched_answer: Matched answer from KB
        
    Returns:
        True if relevant, False otherwise
    """
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
    """
    Fallback to Groq LLM when no answer found in knowledge base.
    
    Args:
        query: User's question
        
    Returns:
        LLM-generated answer
    """
    try:
        api_key = os.getenv("GROQ_API_KEY")
        
        if not api_key:
            return "I couldn't find an answer in my knowledge base. Please try rephrasing your question or contact student.experience@harbour.space"
        
        client = Groq(api_key=api_key)
        
        # Create context from knowledge base topics
        topics = set(item.get("topic", "") for item in KNOWLEDGE)
        context = f"You are a helpful AI assistant for Harbour.Space University students in Barcelona. You help with: {', '.join(topics)}. Be concise and helpful."
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
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

# ===================================================================
# RELEVANCE CHECK FUNCTIONS
# ===================================================================
def check_topic_relevance(query: str, matched_item: dict) -> bool:
    """
    Check if matched question is actually relevant to the query.
    
    Args:
        query: User's query
        matched_item: Matched knowledge base item
        
    Returns:
        True if relevant, False otherwise
    """
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


def check_relevance_with_groq(query: str, matched_question: str, matched_answer: str) -> bool:
    """
    Ask Groq if the matched answer is relevant to the user's query.
    
    Args:
        query: User's query
        matched_question: Matched question from KB
        matched_answer: Matched answer from KB
        
    Returns:
        True if relevant, False otherwise
    """
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
    """
    Fallback to Groq LLM when no answer found in knowledge base.
    
    Args:
        query: User's question
        
    Returns:
        LLM-generated answer
    """
    try:
        api_key = os.getenv("GROQ_API_KEY")
        
        if not api_key:
            return "I couldn't find an answer in my knowledge base. Please try rephrasing your question or contact student.experience@harbour.space"
        
        client = Groq(api_key=api_key)
        
        # Create context from knowledge base topics
        topics = set(item.get("topic", "") for item in KNOWLEDGE)
        context = f"You are a helpful AI assistant for Harbour.Space University students in Barcelona. You help with: {', '.join(topics)}. Be concise and helpful."
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
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


# ===================================================================
# API ENDPOINTS - Q&A
# ===================================================================
@app.get("/ask", response_model=QAResponse)
def ask(query: str, min_score: float = 0.35, autosave: bool = True):
    """
    Answer questions using semantic search and LLM fallback.
    
    Args:
        query: User's question
        min_score: Minimum similarity score for internal answers
        autosave: Whether to save query to history
        
    Returns:
        QAResponse with answer and metadata
    """
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
            answer=item.get("answer", ""),
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
        if autosave:
            save_history(resp, query)
        return resp

    # Keyword fallback
    ql = query.lower()
    for item in KNOWLEDGE:
        if item.get("topic") and item["topic"] in ql:
            resp = QAResponse(
                answer=item.get("answer", ""),
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
            if autosave:
                save_history(resp, query)
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
    if autosave:
        save_history(resp, query)
    return resp


# ===================================================================
# API ENDPOINTS - HISTORY
# ===================================================================
@app.get("/history")
def history(limit: int = 20):
    """
    Get recent query history.
    
    Args:
        limit: Maximum number of results to return
        
    Returns:
        List of recent queries with timestamps
    """
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT ts, query, answer, source FROM history ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    con.close()
    return [{"ts": r[0], "query": r[1], "answer": r[2], "source": r[3]} for r in rows]


# ===================================================================
# API ENDPOINTS - RATINGS
# ===================================================================
@app.post("/rate")
def rate_answer(req: RatingRequest):
    """
    Save user rating for an answer.
    
    Args:
        req: Rating request with question, topic, and rating value
        
    Returns:
        Success status
    """
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
    """
    Get most popular questions based on positive ratings.
    
    Args:
        limit: Maximum number of results
        
    Returns:
        List of popular questions with rating statistics
    """
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
    """
    Get questions with most negative ratings that need improvement.
    
    Args:
        limit: Maximum number of results
        
    Returns:
        List of questions needing improvement with rating statistics
    """
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
