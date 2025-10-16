# 🏗️ Architecture Documentation

## Overview

Student Life Companion - AI-powered Q&A system for Harbour.Space students in Barcelona. Provides answers from internal knowledge base or falls back to Groq LLM.

---

## 🎯 Core Components

### 1. **FastAPI Backend** (`main.py`)
- REST API server
- Semantic search with Sentence Transformers
- Groq LLM integration for fallback
- SQLite for dynamic data (history, ratings, profiles)
- User profile management

### 2. **Telegram Bot** (`telegram_bot.py`)
- Natural language interface
- Profile selection on first use
- Commands: `/start`, `/profile`, `/help`, `/topics`, `/popular`
- Connects to FastAPI backend

### 3. **Web Frontend** (`static/frontend.html`)
- Single-page application
- Profile selection modal
- Topic filtering
- Popular questions display
- Dark mode support

### 4. **Knowledge Base** (`knowledge_base.json`)
- 42 curated Q&A pairs
- Topics: visa, housing, banking, healthcare, transport, mobile, life, university
- Static data, manually maintained

### 5. **Database** (`notebook.db` - SQLite)
- `history` - query history
- `ratings` - user feedback (👍/👎)
- `user_profiles` - user profile preferences

---

## 🔄 Data Flow

### Query Processing Flow:

```
User Query
    ↓
[Telegram Bot / Web Frontend]
    ↓
FastAPI /ask endpoint
    ↓
Sentence Transformer (encode query)
    ↓
Cosine Similarity with KB embeddings
    ↓
Three-tier relevance check:
    ├─ High confidence (>0.6) → Use KB answer
    ├─ Medium (0.35-0.6) → Ask Groq to verify relevance
    │   ├─ YES → Use KB answer
    │   └─ NO → Groq generates answer
    └─ Low (<0.35) → Groq generates answer
    ↓
Response to User
```

---

## 🧠 Semantic Search System

### Components:

1. **Embeddings Model**: `all-MiniLM-L6-v2` (Sentence Transformers)
   - 384-dimensional vectors
   - Fast inference (~10ms per query)
   - Good for semantic similarity

2. **Relevance Checking**:
   - **Simple check** (`check_topic_relevance`): Filters obvious mismatches
   - **Groq verification** (`check_relevance_with_groq`): AI-powered relevance check for edge cases

3. **Rating Boost**:
   - Positive ratings increase similarity score (+0.05 per rating, max +0.1)
   - Helps surface better answers over time

---

## 👥 User Profiles

### Available Profiles:

1. **📚 Student (long-term)** - Full degree (1-4 years)
   - Topics: all
   
2. **👨‍🏫 Teacher (3-9 weeks)** - Short-term teaching
   - Topics: housing, transport, life, mobile
   
3. **🌍 Exchange/Visiting (3-9 weeks)** - Exchange students
   - Topics: housing, transport, mobile, life, university
   
4. **🛬 Just Arrived** - Survival guide (first week)
   - Topics: transport, mobile, life, housing
   
5. **🤷 Other** - Doesn't fit categories
   - Topics: all

### Profile Storage:
- Web: `localStorage` (user_id: `web_<random>`)
- Telegram: `user_id` from Telegram
- Backend: SQLite `user_profiles` table

---

## 🔌 API Endpoints

### Core Endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ask` | GET | Main Q&A endpoint |
| `/reload` | GET | Reload knowledge base |
| `/topics` | GET | Get all topics with counts |
| `/questions/{topic}` | GET | Get questions by topic |
| `/popular` | GET | Get popular questions |
| `/rate` | POST | Rate an answer |
| `/profile` | POST | Set user profile |
| `/profile/{user_id}` | GET | Get user profile |
| `/profiles` | GET | Get available profiles |
| `/history` | GET | Get query history |

---

## 🗄️ Database Schema

### SQLite Tables:

```sql
-- Query history
CREATE TABLE history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts INTEGER,
    query TEXT,
    answer TEXT,
    matched_question TEXT,
    topic TEXT,
    similarity REAL,
    source TEXT
);

-- User ratings
CREATE TABLE ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts INTEGER,
    question TEXT,
    topic TEXT,
    rating INTEGER,  -- 1 for 👍, -1 for 👎
    user_query TEXT
);

-- User profiles
CREATE TABLE user_profiles (
    user_id TEXT PRIMARY KEY,
    profile_type TEXT,
    created_at INTEGER,
    updated_at INTEGER
);
```

---

## 🔧 Technology Stack

### Backend:
- **FastAPI** - Web framework
- **Uvicorn** - ASGI server
- **Sentence Transformers** - Embeddings
- **Groq** - LLM fallback (llama-3.3-70b-versatile)
- **SQLite** - Database
- **Python 3.9+**

### Frontend:
- **Vanilla JavaScript** - No frameworks
- **CSS3** - Custom styling with dark mode
- **LocalStorage** - Client-side state

### Telegram:
- **python-telegram-bot** - Bot framework
- **httpx** - Async HTTP client

---

## 📦 Deployment

### Requirements:
- Python 3.9+
- 1GB RAM minimum
- 500MB disk space
- Environment variables:
  - `GROQ_API_KEY` - Groq API key
  - `TELEGRAM_BOT_TOKEN` - Telegram bot token
  - `API_BASE_URL` - Backend URL (default: http://127.0.0.1:8888)

### Running:
```bash
# Install dependencies
pip install -r requirements.txt

# Start FastAPI server
uvicorn main:app --reload --port 8888

# Start Telegram bot (separate terminal)
python telegram_bot.py
```

---

## 🔐 Security Considerations

1. **API Keys**: Stored in `.env` file (not in git)
2. **Rate Limiting**: Groq API has 30 requests/min limit
3. **Input Validation**: FastAPI Pydantic models
4. **SQL Injection**: Using parameterized queries
5. **CORS**: Configured for same-origin only

---

## 📈 Performance

### Current Metrics:
- **Query latency**: 200-500ms (with Groq verification)
- **Embeddings**: ~10ms per query
- **Database**: <5ms for simple queries
- **Capacity**: 100+ concurrent users

### Bottlenecks:
1. Groq API calls (30/min limit)
2. Sentence Transformer model loading (1-2 seconds on startup)

---

## 🚀 Future Improvements

### Planned:
- [ ] Notion integration for knowledge base sync
- [ ] Multi-language support (Spanish, Russian)
- [ ] Voice message support (Telegram)
- [ ] Analytics dashboard
- [ ] Caching layer (Redis)

### Considered:
- [ ] PostgreSQL migration (if >10k users/day)
- [ ] Vector database (Pinecone/Weaviate) for better search
- [ ] Fine-tuned embeddings model
- [ ] A/B testing framework

---

## 📚 Related Documentation

- [API Documentation](API.md)
- [Telegram Bot Setup](../TELEGRAM_BOT_SETUP.md)
- [README](../README.md)
