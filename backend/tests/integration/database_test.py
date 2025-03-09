import os
import pytest
import numpy as np
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Import after setting environment variable
from src.consts.vectors import VECTOR_DIMS
from src.database.pgvector import Base, Project, CodeFile, CodeChunk


@pytest.fixture(scope="function")
def test_db():
    """
    Create a clean test database for each test function
    """
    # Get test database URL
    test_db_url = os.getenv("DATABASE_URL", "")

    # Create test engine
    test_engine = create_engine(test_db_url)

    # Create extension and tables
    with test_engine.connect() as conn:
        conn.execute(text("DROP EXTENSION IF EXISTS vector CASCADE"))
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    print("created extension")

    # Create all tables
    Base.metadata.drop_all(bind=test_engine)
    print("dropped tables")
    Base.metadata.create_all(bind=test_engine)
    print("created tables")

    # Create a test session
    TestingSessionLocal = sessionmaker(bind=test_engine)
    test_session = TestingSessionLocal()

    yield test_session

    # Clean up
    test_session.close()


def test_project_creation(test_db):
    """
    Test creating a project in the database, queries for it,
    and asserts that it has the right fields for the ORM.
    """
    # Create a new project
    project = Project(name="test-project", path="/path/to/test-project")
    test_db.add(project)
    test_db.commit()

    # Query the project
    db_project = test_db.query(Project).filter(Project.name == "test-project").first()

    # Check fields
    assert db_project is not None
    assert db_project.name == "test-project"
    assert db_project.path == "/path/to/test-project"
    assert db_project.created_at is not None


def test_code_file_creation(test_db):
    """
    Test creating a code file, storing it in the DB and querying
    it for its fields.
    """
    # Create a project first
    project = Project(name="test-project", path="/path/to/test-project")
    test_db.add(project)
    test_db.commit()

    # Create a code file
    code_file = CodeFile(
        project_id=project.id,
        file_path="src/main.py",
        language="python",
        last_modified=datetime.now(),
    )
    test_db.add(code_file)
    test_db.commit()

    # Query the file
    db_file = (
        test_db.query(CodeFile).filter(CodeFile.file_path == "src/main.py").first()
    )

    # Check fields
    assert db_file is not None
    assert db_file.project_id == project.id
    assert db_file.file_path == "src/main.py"
    assert db_file.language == "python"


def test_code_chunk_with_embedding(test_db):
    """
    Test creating a code chunk with an embedding based in a project and
    code file. Use fake embeddings.
    """
    # Create a project first
    project = Project(name="test-project", path="/path/to/test-project")
    test_db.add(project)
    test_db.commit()

    # Create a code file
    code_file = CodeFile(
        project_id=project.id,
        file_path="src/main.py",
        language="python",
        last_modified=datetime.now(),
    )
    test_db.add(code_file)
    test_db.commit()

    # Create a sample embedding using the DB's vector dimensions
    sample_embedding = np.random.rand(VECTOR_DIMS).astype(np.float32)

    # Create a code chunk with an embedding
    code_chunk = CodeChunk(
        project_id=project.id,
        file_id=code_file.id,
        start_line=1,
        end_line=10,
        content="def hello_world():\n    print('Hello world!')",
        embedding=sample_embedding,
    )
    test_db.add(code_chunk)
    test_db.commit()

    # Query the chunk
    db_chunk = (
        test_db.query(CodeChunk).filter(CodeChunk.file_id == code_file.id).first()
    )

    # Check fields
    assert db_chunk is not None
    assert db_chunk.project_id == project.id
    assert db_chunk.file_id == code_file.id
    assert db_chunk.start_line == 1
    assert db_chunk.end_line == 10
    assert db_chunk.content == "def hello_world():\n    print('Hello world!')"
    assert db_chunk.embedding is not None
    assert len(db_chunk.embedding) == VECTOR_DIMS


def test_relationships(test_db):
    """
    Test relationship navigation between object relations:
    i.e., projects have code files which have chunks which have embeddings, etc.
    """
    # Create a project
    project = Project(name="test-project", path="/path/to/test-project")
    test_db.add(project)
    test_db.commit()

    # Create two code files
    file1 = CodeFile(
        project_id=project.id,
        file_path="src/main.py",
        language="python",
        last_modified=datetime.now(),
    )
    file2 = CodeFile(
        project_id=project.id,
        file_path="src/utils.py",
        language="python",
        last_modified=datetime.now(),
    )
    test_db.add_all([file1, file2])
    test_db.commit()

    # Create sample embeddings
    embedding1 = np.random.rand(VECTOR_DIMS).astype(np.float32)
    embedding2 = np.random.rand(VECTOR_DIMS).astype(np.float32)

    # Create chunks for each file
    chunk1 = CodeChunk(
        project_id=project.id,
        file_id=file1.id,
        start_line=1,
        end_line=10,
        content="def main():\n    print('Main')",
        embedding=embedding1,
    )
    chunk2 = CodeChunk(
        project_id=project.id,
        file_id=file2.id,
        start_line=1,
        end_line=5,
        content="def util():\n    return True",
        embedding=embedding2,
    )
    test_db.add_all([chunk1, chunk2])
    test_db.commit()

    # Test project -> files relationship
    db_project = test_db.query(Project).filter(Project.id == project.id).first()
    assert len(db_project.files) == 2
    assert db_project.files[0].file_path in ["src/main.py", "src/utils.py"]
    assert db_project.files[1].file_path in ["src/main.py", "src/utils.py"]

    # Test project -> chunks relationship
    assert len(db_project.chunks) == 2

    # Test file -> chunks relationship
    db_file1 = test_db.query(CodeFile).filter(CodeFile.id == file1.id).first()
    assert len(db_file1.chunks) == 1
    assert db_file1.chunks[0].content == "def main():\n    print('Main')"

    # Test chunk -> file relationship
    db_chunk2 = test_db.query(CodeChunk).filter(CodeChunk.id == chunk2.id).first()
    assert db_chunk2.file.file_path == "src/utils.py"

    # Test chunk -> project relationship
    assert db_chunk2.project.name == "test-project"
