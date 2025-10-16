# Student Life Companion 🎓

AI-powered Q&A assistant for Harbour.Space students in Barcelona. Provides instant answers about visa, housing, transport, healthcare, and student life using semantic search and AI.

## ✨ Features

### Core Functionality
- **🧠 Semantic Search**: Sentence Transformers embeddings for accurate question matching
- **🤖 AI Fallback**: Groq LLM (Llama 3.3 70B) for questions outside knowledge base
- **📚 Knowledge Base**: 42 curated Q&As covering all aspects of student life
- **👥 User Profiles**: Personalized experience (Student, Teacher, Exchange, Just Arrived, Other)
- **⭐ Smart Relevance**: Three-tier relevance checking (embeddings + AI verification)

### User Experience
- **💬 Telegram Bot**: Natural language interface with inline buttons
- **🌐 Web Interface**: Beautiful responsive UI with dark mode
- **📊 Topic Filtering**: Browse by category (Visa, Housing, Transport, etc.)
- **🔥 Popular Questions**: See what others find helpful
- **📜 Query History**: Track all your questions
- **👍👎 Rating System**: Help improve answer quality

### Technical
- **⚡ Fast**: 50-100ms response time for KB queries
- **🔒 Secure**: API keys in environment variables
- **📱 Mobile Ready**: Works on any device
- **🚀 Scalable**: Handles 100+ concurrent users

## 🛠️ Tech Stack

- **Backend**: FastAPI + Uvicorn
- **ML**: Sentence Transformers (all-MiniLM-L6-v2)
- **AI**: Groq API (llama-3.3-70b-versatile)
- **Database**: SQLite (history, ratings, profiles)
- **Frontend**: Vanilla JavaScript + CSS3
- **Bot**: python-telegram-bot

## Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd windsurf-project
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. **Setup Groq API (OPTIONAL but recommended):**
```bash
# Get free API key from https://console.groq.com/
export GROQ_API_KEY="gsk_your_key_here"

# See GROQ_SETUP.md for detailed instructions
```

4. Run the server:
```bash
# Local only (default)
uvicorn main:app --reload

# Access from phone/other devices on same WiFi
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

5. Open the frontend:
```
# On your computer
http://127.0.0.1:8000/static/frontend.html

# On your phone (same WiFi)
http://YOUR_COMPUTER_IP:8000/static/frontend.html
# Example: http://192.168.1.100:8000/static/frontend.html
```

**To find your computer's IP:**
- **Mac**: `ifconfig | grep "inet " | grep -v 127.0.0.1`
- **Windows**: `ipconfig`
- **Linux**: `ip addr show`

## 📡 API Endpoints

See [docs/API.md](docs/API.md) for full documentation.

**Main Endpoints:**
- `GET /ask` - Ask a question (semantic search + AI fallback)
- `GET /topics` - Get all topics with counts
- `GET /popular` - Get popular questions
- `POST /profile` - Set user profile
- `POST /rate` - Rate an answer
- `GET /history` - Get query history
- `GET /reload` - Reload knowledge base

**Example:**
```bash
curl "http://127.0.0.1:8888/ask?query=How%20to%20book%20TIE%20appointment"
```

## 📁 Project Structure

```
windsurf-project/
├── main.py                    # FastAPI backend with semantic search
├── telegram_bot.py            # Telegram bot interface
├── knowledge_base.json        # 42 curated Q&As
├── requirements.txt           # Python dependencies
├── .env                       # API keys (create from .env.example)
├── .env.example               # Environment variables template
├── notebook.db                # SQLite database (auto-created)
├── static/
│   └── frontend.html          # Web interface
├── docs/
│   ├── ARCHITECTURE.md        # System architecture
│   └── API.md                 # API documentation
├── tests/
│   ├── test_smoke.py          # Smoke tests
│   └── test_relevance.py      # Relevance checking tests
└── TELEGRAM_BOT_SETUP.md      # Bot setup instructions
```

## 🧪 Testing

Run tests with pytest:

```bash
# Install pytest
pip install pytest

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_smoke.py -v
pytest tests/test_relevance.py -v
```

**Test Coverage:**
- ✅ Smoke tests - Basic functionality checks
- ✅ Relevance tests - Query filtering accuracy
- 🚧 Integration tests - Coming soon
- 🚧 E2E tests - Coming soon

## 📚 Documentation

- **[Architecture](docs/ARCHITECTURE.md)** - System design and data flow
- **[API Documentation](docs/API.md)** - Complete API reference
- **[Telegram Bot Setup](TELEGRAM_BOT_SETUP.md)** - Bot configuration guide

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest tests/ -v`
5. Submit a pull request

## 📝 Knowledge Base

Edit `knowledge_base.json` to add new topics. Each entry includes:
- `topic`: Category (visa, housing, transport, etc.)
- `question`: Sample question with synonyms
- `answer`: Detailed response
- `steps`: Step-by-step instructions (optional)
- `source_url`: Official link
- `verified`: Accuracy flag
- `cost`, `deadline`, `contacts`, `quick_links`: Additional metadata

## 📄 License

MIT

## 🙏 Acknowledgments

- **Harbour.Space University** - For the inspiration
- **Groq** - For free LLM API access
- **Sentence Transformers** - For semantic search capabilities
