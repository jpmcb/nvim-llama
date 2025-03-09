from datetime import datetime
import os
from loguru import logger
from sqlalchemy import (
    create_engine,
    String,
    Integer,
    Text,
    DateTime,
    ForeignKey,
    text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    sessionmaker,
    relationship,
    declarative_base,
)
from sqlalchemy.sql import func
from contextlib import contextmanager
from pgvector.sqlalchemy import Vector

# Get database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://neovim:neovim@localhost:5432/nvim-llama"
)


# Create SQLAlchemy engine and session factory
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


# Define models
class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    path: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

    # Relationships
    files = relationship(
        "CodeFile", back_populates="project", cascade="all, delete-orphan"
    )
    chunks = relationship(
        "CodeChunk", back_populates="project", cascade="all, delete-orphan"
    )


class CodeFile(Base):
    __tablename__ = "code_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"))
    file_path: Mapped[str] = mapped_column(String, index=True)

    # Path relative to project root
    language: Mapped[str] = mapped_column(String)  # Programming language
    last_modified: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

    # Relationships
    project = relationship("Project", back_populates="files")
    chunks = relationship(
        "CodeChunk", back_populates="file", cascade="all, delete-orphan"
    )


class CodeChunk(Base):
    __tablename__ = "code_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"))
    file_id: Mapped[int] = mapped_column(Integer, ForeignKey("code_files.id"))
    start_line: Mapped[int] = mapped_column(Integer)  # Start line in the file
    end_line: Mapped[int] = mapped_column(Integer)  # End line in the file
    content: Mapped[str] = mapped_column(Text)  # The actual code chunk content
    embedding = mapped_column(Vector(1024))  # Vector embedding for the chunk
    created_at = mapped_column(DateTime, default=func.now())

    # Relationships
    project = relationship("Project", back_populates="chunks")
    file = relationship("CodeFile", back_populates="chunks")


# Database initialization
def init_db():
    try:
        # Create extension if it doesn't exist
        with engine.connect() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            connection.commit()
        logger.debug("Created pgvector extension")

        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")

        # Add HNSW index
        with engine.connect() as connection:
            # Create the index in the database directly
            connection.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS hnsw_code_chunks_embeddings
                    ON code_chunks
                    USING hnsw (embedding vector_cosine_ops)
                """
                )
            )
            connection.commit()
        logger.info("HNSW index created successfully")

    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise


# Session dependency
@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# FastAPI dependency
def get_db_session():
    with get_db() as session:
        yield session
