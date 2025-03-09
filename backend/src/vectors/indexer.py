import os
from loguru import logger
import fnmatch
from datetime import datetime
from typing import List, Dict, Any
import tiktoken
from sqlalchemy.orm import Session

from src.database.pgvector import get_db, Project, CodeFile, CodeChunk


class CodebaseIndexer:
    def __init__(self, vector_store):
        self.vector_store = vector_store
        self.encoding = tiktoken.get_encoding(
            "cl100k_base"
        )  # Same as used by many embedding models
        self.chunk_size = 1000  # Target tokens per chunk
        self.chunk_overlap = 200  # Token overlap between chunks

    def index_codebase(
        self,
        project_path: str,
        project_name: str,
        file_extensions: List[str],
        exclude_patterns: List[str],
    ) -> None:
        """
        Index a codebase by chunking files and storing their vectors.

        Args:
            project_path: Path to the project root
            project_name: Name of the project
            file_extensions: List of file extensions to include
            exclude_patterns: List of patterns to exclude
        """
        logger.info(f"Starting indexing for project {project_name} at {project_path}")

        with get_db() as db:
            try:
                # Create or update project entry
                project = db.query(Project).filter(Project.name == project_name).first()
                if project:
                    project.path = project_path
                    project.updated_at = datetime.now()
                else:
                    project = Project(name=project_name, path=project_path)
                    db.add(project)

                db.commit()

                # Walk through project files
                file_count = 0
                chunk_count = 0

                for root, dirs, files in os.walk(project_path):
                    # Filter out excluded directories
                    dirs[:] = [
                        d
                        for d in dirs
                        if not any(
                            fnmatch.fnmatch(d, pattern) for pattern in exclude_patterns
                        )
                    ]

                    for file in files:
                        # Check if file has a valid extension
                        if not any(file.endswith(ext) for ext in file_extensions):
                            continue

                        # Check if file matches any exclude pattern
                        if any(
                            fnmatch.fnmatch(file, pattern)
                            for pattern in exclude_patterns
                        ):
                            continue

                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, project_path)

                        try:
                            # Determine language based on file extension
                            _, ext = os.path.splitext(file)
                            language = self._get_language_for_extension(ext)

                            # Get file modification time
                            mtime = datetime.fromtimestamp(os.path.getmtime(file_path))

                            # Create or update file entry
                            code_file = (
                                db.query(CodeFile)
                                .filter(
                                    CodeFile.project_id == project.id,
                                    CodeFile.file_path == rel_path,
                                )
                                .first()
                            )

                            if code_file:
                                # Skip if file hasn't been modified
                                if (
                                    code_file.last_modified
                                    and code_file.last_modified >= mtime
                                ):
                                    continue

                                code_file.language = language
                                code_file.last_modified = mtime
                            else:
                                code_file = CodeFile(
                                    project_id=project.id,
                                    file_path=rel_path,
                                    language=language,
                                    last_modified=mtime,
                                )
                                db.add(code_file)

                            db.commit()

                            # Process file content
                            with open(
                                file_path, "r", encoding="utf-8", errors="ignore"
                            ) as f:
                                content = f.read()

                            # Chunk the file
                            chunks = self._chunk_file(content)

                            # Store chunks with vectors
                            self.vector_store.store_code_chunks(
                                db, project_name, rel_path, language, chunks
                            )

                            file_count += 1
                            chunk_count += len(chunks)

                        except Exception as e:
                            logger.error(f"Error processing file {file_path}: {str(e)}")

                logger.info(
                    f"Indexing completed for {project_name}: processed {file_count} files and created {chunk_count} chunks"
                )

            except Exception as e:
                db.rollback()
                logger.error(f"Failed to index codebase: {str(e)}")
                raise

    def get_index_status(self, project_name: str, db: Session) -> Dict[str, Any]:
        """
        Get the indexing status for a project.

        Args:
            project_name: Name of the project
            db: Database session

        Returns:
            Dictionary with status information
        """
        try:
            project = db.query(Project).filter(Project.name == project_name).first()
            if not project:
                return {"status": "not_found", "project_name": project_name}

            file_count = (
                db.query(CodeFile).filter(CodeFile.project_id == project.id).count()
            )
            chunk_count = (
                db.query(CodeChunk).filter(CodeChunk.project_id == project.id).count()
            )

            return {
                "status": "indexed" if file_count > 0 else "pending",
                "project_name": project_name,
                "file_count": file_count,
                "chunk_count": chunk_count,
                "last_updated": project.updated_at.isoformat()
                if project.updated_at
                else None,
            }

        except Exception as e:
            logger.error(f"Failed to get index status: {str(e)}")
            raise

    def _chunk_file(self, content: str) -> List[Dict[str, Any]]:
        """
        Chunk a file content into smaller pieces for embedding.

        Args:
            content: File content as string

        Returns:
            List of chunk dictionaries with start_line, end_line, and content
        """
        # Split content into lines
        lines = content.splitlines()

        # Initialize chunks
        chunks = []
        current_chunk_lines = []
        current_chunk_tokens = 0
        start_line = 1

        for i, line in enumerate(lines, 1):
            # Encode line to get token count
            line_tokens = len(self.encoding.encode(line))

            # Check if adding this line would exceed chunk size
            if (
                current_chunk_tokens + line_tokens > self.chunk_size
                and current_chunk_lines
            ):
                # Store current chunk
                chunk_content = "\n".join(current_chunk_lines)
                chunks.append(
                    {
                        "start_line": start_line,
                        "end_line": i - 1,
                        "content": chunk_content,
                    }
                )

                # Calculate overlap - keep the last few lines
                overlap_lines = []
                overlap_tokens = 0
                for line in reversed(current_chunk_lines):
                    line_token_count = len(self.encoding.encode(line))
                    if overlap_tokens + line_token_count > self.chunk_overlap:
                        break
                    overlap_lines.insert(0, line)
                    overlap_tokens += line_token_count

                # Start new chunk with overlap
                current_chunk_lines = overlap_lines
                current_chunk_tokens = overlap_tokens
                start_line = i - len(overlap_lines)

            # Add line to current chunk
            current_chunk_lines.append(line)
            current_chunk_tokens += line_tokens

        # Don't forget the last chunk
        if current_chunk_lines:
            chunk_content = "\n".join(current_chunk_lines)
            chunks.append(
                {
                    "start_line": start_line,
                    "end_line": len(lines),
                    "content": chunk_content,
                }
            )

        return chunks

    def _get_language_for_extension(self, extension: str) -> str:
        """
        Map file extension to programming language.

        Args:
            extension: File extension including the dot

        Returns:
            Programming language name
        """
        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".html": "html",
            ".css": "css",
            ".lua": "lua",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c",
            ".hpp": "cpp",
            ".rs": "rust",
            ".go": "go",
            ".java": "java",
            ".rb": "ruby",
            ".php": "php",
            ".sh": "bash",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".json": "json",
            ".md": "markdown",
            ".sql": "sql",
        }

        return extension_map.get(extension.lower(), "text")
