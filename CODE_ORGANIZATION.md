# Code Organization Summary

## main.py Structure

The code has been reorganized into the following logical sections:

### 1. **STANDARD LIBRARY IMPORTS** (Lines ~1-10)
- Standard Python libraries (json, os, sqlite3, time, pathlib, typing)

### 2. **THIRD-PARTY IMPORTS** (Lines ~11-50)
- FastAPI framework
- Machine Learning libraries (sklearn, pandas)
- Database clients (pymongo, sqlite3)
- LLM integration (groq)
- Sentence Transformers for embeddings
- Environment variables (dotenv)

### 3. **CONFIGURATION** (Lines ~51-85)
- MongoDB connection settings
- File paths (knowledge base, SQLite DB)
- Semantic search thresholds
- FastAPI app initialization
- CORS middleware configuration
- Global variable declarations

### 4. **PYDANTIC MODELS** (Lines ~86-110)
- QAResponse: Response model for Q&A
- PersonalQuery: Request model for personal assistant
- PersonalResponse: Response model for personal assistant
- RatingRequest: Request model for ratings

### 5. **DATABASE INITIALIZATION** (Lines ~111-170)
- `init_mongodb()`: MongoDB connection setup
- `init_sqlite()`: SQLite tables creation
- `save_history()`: Save query history to database

### 6. **KNOWLEDGE BASE FUNCTIONS** (Lines ~171-210)
- `load_kb()`: Load knowledge base from JSON
- `build_semantic_index()`: Build TF-IDF search index
- `build_embeddings_index()`: Create sentence embeddings

### 7. **PERSONAL ASSISTANT FUNCTIONS** (Lines ~211-350)
- `generate_training_data_from_db()`: Create training data from MongoDB
- `train_personal_intent_model()`: Train intent classification model
- `format_schedule()`: Format schedule data for display

### 8. **INITIALIZATION** (Lines ~351-385)
- `initialize_application()`: Main initialization function
  - Connects to databases
  - Loads ML models
  - Builds indexes
  - Trains classifiers

### 9. **API ENDPOINTS - KNOWLEDGE BASE** (Lines ~386-432)
- `GET /reload`: Reload knowledge base
- `GET /topics`: Get all topics with counts
- `GET /questions/{topic}`: Get questions by topic

### 10. **RATING AND HISTORY FUNCTIONS** (Lines ~433-475)
- `get_question_rating_boost()`: Calculate rating boost for questions

### 11. **RELEVANCE CHECK FUNCTIONS** (Lines ~476-700)
- `check_topic_relevance()`: Check if match is relevant to query
- `check_relevance_with_groq()`: Use Groq LLM for relevance checking
- `ask_groq_llm()`: Fallback to Groq LLM for answers

### 12. **API ENDPOINTS - Q&A** (Lines ~701-810)
- `GET /ask`: Main Q&A endpoint with semantic search and LLM fallback

### 13. **API ENDPOINTS - HISTORY** (Lines ~811-825)
- `GET /history`: Get recent query history

### 14. **API ENDPOINTS - RATINGS** (Lines ~826-950)
- `POST /rate`: Save user rating for answers
- `GET /popular`: Get most popular questions
- `GET /needs-improvement`: Get questions needing improvement

## Key Improvements

### ✅ Better Organization
- Clear section separators with descriptive headers
- Logical grouping of related functions
- Imports organized by category

### ✅ Proper Initialization
- All initialization consolidated in one function
- Clear dependency order
- Better error handling and status messages

### ✅ Enhanced Documentation
- All functions have proper docstrings
- Clear parameter and return type descriptions
- Inline comments where needed

### ✅ API Endpoint Organization
- Grouped by functionality (KB, Q&A, History, Ratings)
- Removed duplicate endpoints
- Clear endpoint purposes

### ✅ Code Flow
- Functions defined before use
- Global variables declared at top
- Initialization happens in controlled manner

## Code Quality Metrics

- **Total Lines**: ~950
- **Functions**: 20+
- **API Endpoints**: 8
- **Sections**: 14
- **Documentation Coverage**: 100%

## Usage

The code now follows a clear top-down structure:
1. Imports
2. Configuration
3. Models
4. Helper Functions
5. Initialization
6. API Endpoints

This makes it easier to:
- Find specific functionality
- Understand dependencies
- Add new features
- Debug issues
- Maintain the codebase
