from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import json, sqlite3, time
from pathlib import Path

# semantic search
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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

@app.get("/ask", response_model=QAResponse)
def ask(query: str, min_score: float = 0.28, autosave: bool = True):
    q_vec = VECTORIZER.transform([query])
    sims = cosine_similarity(q_vec, KB_MATRIX)[0]
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

    resp = QAResponse(
        answer="No close match found. Please check the official Extranjería or Tax Agency pages.",
        matched_question=None, topic=None, steps=None, source_url=None,
        verified=None, similarity=None, source="external",
        cost=None, contacts=None, quick_links=None, deadline=None, related_topics=None
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
