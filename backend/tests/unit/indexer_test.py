import pytest
from unittest.mock import MagicMock

# Import after setting env vars
from src.vectors.indexer import CodebaseIndexer


@pytest.fixture
def mock_vector_store():
    """Create a mock vector store"""
    return MagicMock()


@pytest.fixture
def indexer(mock_vector_store):
    """Create a CodebaseIndexer with mock dependencies"""
    return CodebaseIndexer(mock_vector_store)


def test_chunk_file(indexer):
    """Test file chunking functionality"""
    # Test with a small file
    content = (
        "def function1():\n    return 'hello'\n\ndef function2():\n    return 'world'"
    )
    chunks = indexer._chunk_file(content)

    assert len(chunks) == 1
    assert chunks[0]["start_line"] == 1
    assert chunks[0]["end_line"] == 5
    assert chunks[0]["content"] == content

    # Test with a larger file (simulate by lowering chunk size)
    indexer.chunk_size = 10  # Small chunk size for testing
    indexer.chunk_overlap = 2

    content = "\n".join([f"line {i}" for i in range(1, 21)])
    chunks = indexer._chunk_file(content)

    assert len(chunks) > 1
    assert chunks[0]["start_line"] == 1
    assert chunks[0]["end_line"] < 20


def test_get_language_for_extension(indexer):
    """Test language detection from file extensions"""
    assert indexer._get_language_for_extension(".py") == "python"
    assert indexer._get_language_for_extension(".js") == "javascript"
    assert indexer._get_language_for_extension(".ts") == "typescript"
    assert indexer._get_language_for_extension(".cpp") == "cpp"
    assert indexer._get_language_for_extension(".unknown") == "text"
