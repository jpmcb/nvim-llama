import os
import pytest
from unittest.mock import patch, MagicMock
import numpy as np
from langchain.schema import AIMessage

from src.consts.vectors import VECTOR_DIMS

# Import after patching environment
with patch.dict(os.environ, {"LLM_PROVIDER": "test", "EMBEDDING_PROVIDER": "test"}):
    from src.agent.llm import LLMService


@pytest.fixture
def mock_llm():
    """Mock LLM that returns a predictable response"""
    mock = MagicMock()
    mock.return_value = AIMessage(content="This is a mock LLM response")
    return mock


@pytest.fixture
def mock_embedding_model():
    """Mock embedding model that returns predictable embeddings"""
    mock = MagicMock()
    mock.embed_documents.return_value = [
        np.random.rand(VECTOR_DIMS).tolist() for _ in range(3)
    ]
    return mock


def test_generate_response(mock_llm):
    """Test response generation"""
    with patch.object(LLMService, "_initialize_llm", return_value=mock_llm):
        with patch.object(LLMService, "_initialize_embedding_model"):
            service = LLMService()

            response = service.generate_response(
                query="How does this code work?",
                context="def hello(): print('hello')",
                chat_history=[
                    {"role": "user", "content": "Can you explain this code?"},
                    {"role": "assistant", "content": "Sure, I'll explain it."},
                ],
            )

            assert response == "This is a mock LLM response"
            assert mock_llm.call_count == 1


def test_generate_embeddings(mock_embedding_model):
    """Test embedding generation"""
    with patch.object(LLMService, "_initialize_llm"):
        with patch.object(
            LLMService, "_initialize_embedding_model", return_value=mock_embedding_model
        ):
            service = LLMService()

            texts = [
                "def function1(): return 'hello'",
                "def function2(): return 'world'",
                "def function3(): print('Hello world')",
            ]

            embeddings = service.generate_embeddings(texts)

            assert len(embeddings) == 3
            assert all(len(embedding) == VECTOR_DIMS for embedding in embeddings)


def test_error_handling():
    """Test error handling in service methods"""
    with patch.object(LLMService, "_initialize_llm") as mock_init_llm:
        with patch.object(
            LLMService, "_initialize_embedding_model"
        ) as mock_init_embedding:
            # Setup to raise exceptions
            mock_init_llm.return_value = MagicMock(side_effect=Exception("LLM error"))
            mock_init_embedding.return_value = MagicMock(
                embed_documents=MagicMock(side_effect=Exception("Embedding error"))
            )

            service = LLMService()

            # Test response generation error handling
            response = service.generate_response(
                query="test query", context="test context"
            )
            assert "I'm sorry, I encountered an error" in response

            # Test embedding generation error handling
            embeddings = service.generate_embeddings(["test text"])
            assert len(embeddings) == 1
            assert len(embeddings[0]) == VECTOR_DIMS  # Should return fallback embedding
