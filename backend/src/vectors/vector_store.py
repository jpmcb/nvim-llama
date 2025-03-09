from loguru import logger
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from src.database.pgvector import Project, CodeFile, CodeChunk
from src.agent.llm import LLMService


class VectorStore:
    def __init__(self):
        self.llm_service = LLMService()

    def store_code_chunks(
        self,
        db: Session,
        project_name: str,
        file_path: str,
        language: str,
        chunks: List[Dict[str, Any]],
    ) -> None:
        """
        Store code chunks with their embeddings in the database.

        Args:
            db: Database session
            project_name: Name of the project
            file_path: Path to the file relative to project root
            language: Programming language of the file
            chunks: List of code chunks with start_line, end_line, and content
        """
        try:
            # Get or create project
            project = db.query(Project).filter(Project.name == project_name).first()
            if not project:
                logger.error(f"Project {project_name} not found")
                return

            # Get or create file
            code_file = (
                db.query(CodeFile)
                .filter(
                    CodeFile.project_id == project.id, CodeFile.file_path == file_path
                )
                .first()
            )

            if not code_file:
                logger.error(f"File {file_path} not found for project {project_name}")
                return

            # Delete existing chunks for this file
            db.query(CodeChunk).filter(CodeChunk.file_id == code_file.id).delete()

            # Create embeddings for all chunks in a batch
            chunk_contents = [chunk["content"] for chunk in chunks]
            embeddings = self.llm_service.generate_embeddings(chunk_contents)

            # Store chunks with embeddings
            for i, chunk in enumerate(chunks):
                code_chunk = CodeChunk(
                    project_id=project.id,
                    file_id=code_file.id,
                    start_line=chunk["start_line"],
                    end_line=chunk["end_line"],
                    content=chunk["content"],
                    embedding=embeddings[i],
                )
                db.add(code_chunk)

            db.commit()
            logger.info(f"Stored {len(chunks)} chunks for {file_path}")

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to store code chunks: {str(e)}")
            raise

    def query_vectors(
        self, db: Session, project_name: str, query: str, limit: int = 5
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Query the vector store for relevant code chunks based on the query.

        Args:
            db: Database session
            project_name: Name of the project
            query: Query string
            limit: Maximum number of results to return

        Returns:
            Tuple containing:
              - List of relevant code chunks with file_path, language, and content
              - List of relevant files with file_path and relevance score
        """
        try:
            # Generate query embedding
            query_embedding = self.llm_service.generate_embeddings([query])[0]

            # Get project
            project = db.query(Project).filter(Project.name == project_name).first()
            if not project:
                logger.error(f"Project {project_name} not found")
                return [], []

            # Query for most similar chunks
            stmt = (
                select(
                    CodeChunk.id,
                    CodeChunk.content,
                    CodeChunk.start_line,
                    CodeChunk.end_line,
                    CodeFile.file_path,
                    CodeFile.language,
                )
                .join(CodeFile, CodeChunk.file_id == CodeFile.id)
                .where(CodeChunk.project_id == project.id)
                .order_by(CodeChunk.embedding.l2_distance(query_embedding))
                .limit(limit)
            )

            results = db.execute(stmt).fetchall()

            # Format results
            chunks = []
            files = {}

            for row in results:
                chunks.append(
                    {
                        "content": row.content,
                        "file_path": row.file_path,
                        "language": row.language,
                        "start_line": row.start_line,
                        "end_line": row.end_line,
                    }
                )

                # Track unique files and their best relevance score
                file_path = row.file_path

                if file_path not in files:
                    files[file_path] = {"file_path": file_path}

            # Convert files dictionary to list and sort by relevance
            file_list = list(files.values())

            return chunks, file_list

        except Exception as e:
            logger.error(f"Failed to query vectors: {str(e)}")
            raise
