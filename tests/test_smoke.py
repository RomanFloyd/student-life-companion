"""
Smoke Tests - Basic functionality checks
Run with: pytest tests/test_smoke.py -v
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from main import app, KNOWLEDGE, KB_EMBEDDINGS, EMBEDDING_MODEL

client = TestClient(app)


def test_server_starts():
    """Test that server responds to root endpoint"""
    response = client.get("/")
    assert response.status_code == 200


def test_knowledge_base_loaded():
    """Test that knowledge base is loaded"""
    assert KNOWLEDGE is not None
    assert len(KNOWLEDGE) > 0
    assert len(KNOWLEDGE) == 42  # Expected number of questions


def test_embeddings_loaded():
    """Test that embeddings are created for all KB items"""
    assert KB_EMBEDDINGS is not None
    assert len(KB_EMBEDDINGS) == len(KNOWLEDGE)


def test_embedding_model_loaded():
    """Test that Sentence Transformer model is loaded"""
    assert EMBEDDING_MODEL is not None


def test_ask_endpoint_exists():
    """Test that /ask endpoint exists and responds"""
    response = client.get("/ask?query=hello")
    assert response.status_code == 200
    assert "answer" in response.json()


def test_topics_endpoint():
    """Test that /topics endpoint returns topics"""
    response = client.get("/topics")
    assert response.status_code == 200
    data = response.json()
    assert "topics" in data
    assert len(data["topics"]) > 0


def test_profiles_endpoint():
    """Test that /profiles endpoint returns profiles"""
    response = client.get("/profiles")
    assert response.status_code == 200
    data = response.json()
    assert "profiles" in data
    assert len(data["profiles"]) == 5  # 5 profiles


def test_reload_endpoint():
    """Test that /reload endpoint works"""
    response = client.get("/reload")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "reloaded"
    assert data["items"] == len(KNOWLEDGE)


def test_popular_endpoint():
    """Test that /popular endpoint works"""
    response = client.get("/popular")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_history_endpoint():
    """Test that /history endpoint works"""
    response = client.get("/history")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_static_frontend_exists():
    """Test that frontend HTML is accessible"""
    response = client.get("/static/frontend.html")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_knowledge_base_structure():
    """Test that knowledge base has correct structure"""
    for item in KNOWLEDGE:
        assert "question" in item
        assert "answer" in item
        assert "topic" in item
        assert isinstance(item["question"], str)
        assert isinstance(item["answer"], str)
        assert len(item["question"]) > 0
        assert len(item["answer"]) > 0


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
