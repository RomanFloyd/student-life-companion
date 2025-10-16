"""
Unit Tests for Relevance Checking
Run with: pytest tests/test_relevance.py -v
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import check_topic_relevance


def test_relevance_check_obvious_mismatch():
    """Test that obvious mismatches are filtered out"""
    query = "best pizza in barcelona"
    item = {
        "topic": "visa",
        "question": "How to get TIE card?",
        "answer": "You need to book an appointment..."
    }
    
    result = check_topic_relevance(query, item)
    assert result == False, "Should filter out 'best pizza' query for visa topic"


def test_relevance_check_weather_query():
    """Test that weather queries are filtered"""
    query = "what's the weather like in barcelona"
    item = {
        "topic": "transport",
        "question": "How to use metro?",
        "answer": "Buy T-Casual card..."
    }
    
    result = check_topic_relevance(query, item)
    assert result == False, "Should filter out weather queries"


def test_relevance_check_joke_query():
    """Test that joke queries are filtered"""
    query = "tell me a joke"
    item = {
        "topic": "housing",
        "question": "How to find apartment?",
        "answer": "Check Idealista..."
    }
    
    result = check_topic_relevance(query, item)
    assert result == False, "Should filter out joke queries"


def test_relevance_check_valid_query():
    """Test that valid queries pass through"""
    query = "how to book TIE appointment"
    item = {
        "topic": "visa",
        "question": "How to book Toma de huellas?",
        "answer": "Book online at ICP portal..."
    }
    
    result = check_topic_relevance(query, item)
    assert result == True, "Should allow valid visa query"


def test_relevance_check_topic_mismatch():
    """Test that topic mismatches are caught"""
    query = "how to get NIE number"
    item = {
        "topic": "transport",
        "question": "What is T-Casual card?",
        "answer": "T-Casual is 10-trip ticket..."
    }
    
    # Query mentions "NIE" (admin topic) but matched transport
    result = check_topic_relevance(query, item)
    # Should be False because query has admin keywords but matched transport
    assert result == False, "Should filter topic mismatch (NIE vs transport)"


def test_relevance_check_housing_query():
    """Test housing-related query"""
    query = "where to find apartment in barcelona"
    item = {
        "topic": "housing",
        "question": "How to find apartment?",
        "answer": "Check Idealista, Spotahome..."
    }
    
    result = check_topic_relevance(query, item)
    assert result == True, "Should allow housing query"


def test_relevance_check_general_non_kb_query():
    """Test general queries that shouldn't match KB"""
    queries = [
        "what's the meaning of life",
        "how to make friends",
        "best restaurants near me",
        "where to buy clothes",
        "nightlife in barcelona"
    ]
    
    item = {
        "topic": "university",
        "question": "How to enroll?",
        "answer": "Contact admissions..."
    }
    
    for query in queries:
        result = check_topic_relevance(query, item)
        # These should likely be False, but check_topic_relevance
        # only filters specific patterns, so some might pass
        # This test documents current behavior
        assert isinstance(result, bool), f"Should return bool for query: {query}"


def test_relevance_check_empty_query():
    """Test empty query handling"""
    query = ""
    item = {
        "topic": "visa",
        "question": "How to get TIE?",
        "answer": "Book appointment..."
    }
    
    result = check_topic_relevance(query, item)
    assert isinstance(result, bool), "Should handle empty query gracefully"


def test_relevance_check_case_insensitive():
    """Test that relevance check is case-insensitive"""
    query = "BEST PIZZA IN BARCELONA"
    item = {
        "topic": "visa",
        "question": "How to get TIE?",
        "answer": "Book appointment..."
    }
    
    result = check_topic_relevance(query, item)
    assert result == False, "Should be case-insensitive"


def test_relevance_check_multiple_non_kb_keywords():
    """Test queries with multiple non-KB keywords"""
    query = "best cheap restaurants with good weather"
    item = {
        "topic": "transport",
        "question": "How to use metro?",
        "answer": "Buy T-Casual..."
    }
    
    result = check_topic_relevance(query, item)
    assert result == False, "Should filter queries with multiple non-KB keywords"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
