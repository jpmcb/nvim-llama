import sys
from loguru import logger
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from contextlib import asynccontextmanager

from src.database.pgvector import get_db_session, init_db
from src.vectors.vector_store import VectorStore
from src.vectors.indexer import CodebaseIndexer
from src.agent.llm import LLMService

# Set the logging level based on provided env
logger.remove()
logger.add(sys.stderr, level="DEBUG")

# Initialize services
vector_store = VectorStore()
llm_service = LLMService()
codebase_indexer = CodebaseIndexer(vector_store)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the database on startup
    init_db()
    yield

    # Clean up resources on shutdown
    pass


app = FastAPI(lifespan=lifespan)


# Pydantic models for API
class IndexCodebaseRequest(BaseModel):
    project_path: str
    project_name: str
    file_extensions: List[str] = [
        ".py",
        ".js",
        ".ts",
        ".lua",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".go",
        ".rs",
        ".java",
    ]
    exclude_patterns: List[str] = [
        "node_modules",
        ".git",
        "__pycache__",
        "venv",
        "env",
        "dist",
        "build",
    ]


class ChatRequest(BaseModel):
    project_name: str
    query: str
    chat_history: List[Dict[str, str]] = []
    context_files: Optional[List[str]] = None


class ChatResponse(BaseModel):
    response: str
    context_files: List[Dict[str, Any]] = []


@app.post("/index_codebase")
async def index_codebase(
    request: IndexCodebaseRequest, background_tasks: BackgroundTasks
):
    """
    Index a codebase for vectorization. This is a long-running operation
    that will be executed in the background.
    """
    try:
        # Start indexing in the background
        background_tasks.add_task(
            codebase_indexer.index_codebase,
            request.project_path,
            request.project_name,
            request.file_extensions,
            request.exclude_patterns,
        )

        return {"status": "indexing_started", "project_name": request.project_name}
    except Exception as e:
        logger.error(f"Failed to start indexing: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start indexing: {str(e)}"
        )


@app.get("/index_status/{project_name}")
async def index_status(project_name: str, db=Depends(get_db_session)):
    """
    Get the indexing status for a project.
    """
    try:
        status = codebase_indexer.get_index_status(project_name, db)
        return status
    except Exception as e:
        logger.error(f"Failed to get index status: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get index status: {str(e)}"
        )


@app.post("/chat", response_model=ChatResponse)
async def chat_with_codebase(request: ChatRequest, db=Depends(get_db_session)):
    """
    Chat with the codebase using the LLM model and vector store.
    """
    try:
        # Retrieve relevant code chunks based on the query
        context_chunks, context_files = vector_store.query_vectors(
            db, request.project_name, request.query, limit=5
        )

        # Format context
        context_text = "\n\n".join(
            [
                f"File: {chunk['file_path']}\n```{chunk['language']}\n{chunk['content']}\n```"
                for chunk in context_chunks
            ]
        )

        # Get response from LLM
        response = llm_service.generate_response(
            request.query, context_text, request.chat_history
        )

        return ChatResponse(
            response=response,
            context_files=[{"file_path": file["file_path"]} for file in context_files],
        )
    except Exception as e:
        logger.error(f"Failed to generate response: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error generating response: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
