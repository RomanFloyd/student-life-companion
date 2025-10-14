# Student Life Companion 🎓

AI-powered assistant for international students in Spain, helping with visa, work permits, and tax questions.

## Features

- **Semantic Search**: Uses TF-IDF and cosine similarity to find relevant answers
- **AI Fallback**: Groq LLM (Llama 3.1 70B) answers questions not in knowledge base - **FREE!**
- **Knowledge Base**: 42 curated Q&As about student life, visa, housing, university
- **Rating System**: 👍/👎 ratings improve search results
- **Topic Filters**: Browse questions by category (Visa, Housing, University, etc.)
- **Popular Questions**: Top-5 most helpful answers
- **Query History**: SQLite database tracks all questions and answers
- **Dark Theme**: Beautiful UI with animations and gradients
- **Mobile Ready**: Works on phone via local network

## Tech Stack

- **Backend**: FastAPI (Python)
- **ML**: scikit-learn for semantic matching
- **Database**: SQLite for history
- **Frontend**: Vanilla JavaScript with modern UI

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

## API Endpoints

- `GET /` - Health check
- `GET /ask?query=<question>` - Ask a question
- `GET /history?limit=<n>` - Get query history
- `GET /reload` - Reload knowledge base

## Project Structure

```
windsurf-project/
├── main.py              # FastAPI backend
├── knowledge_base.json  # Q&A data
├── requirements.txt     # Python dependencies
├── static/
│   └── frontend.html    # Web interface
└── notebook.db          # SQLite history (auto-created)
```

## Knowledge Base

Edit `knowledge_base.json` to add new topics. Each entry includes:
- `topic`: Category (visa, work, tax)
- `question`: Sample question
- `answer`: Detailed response
- `steps`: Step-by-step instructions (optional)
- `source_url`: Official link
- `verified`: Accuracy flag

## License

MIT
