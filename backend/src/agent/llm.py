import os
from loguru import logger
from typing import List, Dict, Optional

# LangChain imports
from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    GoogleGenerativeAIEmbeddings,
)
from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.schema import AIMessage, HumanMessage, SystemMessage


class LLMService:
    """
    Provider-agnostic LLM service that uses LangChain to support multiple providers.

    This service handles:
    1. Chat/completion generation
    2. Text embeddings
    """

    def __init__(self):
        # Load configuration from environment
        self.provider = os.getenv("LLM_PROVIDER", "google").lower()
        self.embedding_provider = os.getenv("EMBEDDING_PROVIDER", "google").lower()

        # Initialize the LLM and Embedding models based on provider config
        self.llm = self._initialize_llm()
        self.embedding_model = self._initialize_embedding_model()

        logger.info(f"Initialized LLM service with provider: {self.provider}")
        logger.info(
            f"Initialized embedding service with provider: {self.embedding_provider}"
        )

    def _initialize_llm(self):
        """Initialize the appropriate LLM based on configuration"""

        if self.provider == "google":
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.warning("GEMINI_API_KEY not found in environment variables")

            model_name = os.getenv("GEMINI_MODEL_NAME", "models/gemini-2.0-flash")
            return ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=api_key,
                temperature=0.7,
            )

        else:
            logger.warning(
                f"Unsupported LLM provider: {self.provider}. Falling back to Google."
            )
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.warning("GEMINI_API_KEY not found in environment variables")

            model_name = os.getenv("GEMINI_MODEL_NAME", "models/gemini-2.0-flash")
            return ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=api_key,
                temperature=0.7,
            )

    def _initialize_embedding_model(self):
        """Initialize the appropriate embedding model based on configuration"""
        if self.embedding_provider == "google":
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.warning("GEMINI_API_KEY not found in environment variables")

            model_name = os.getenv(
                "GEMINI_EMBEDDING_MODEL", "models/text-embedding-004"
            )
            return GoogleGenerativeAIEmbeddings(
                model=model_name, google_api_key=api_key
            )

        else:
            logger.warning(
                f"Unsupported embedding provider: {self.embedding_provider}. Falling back to Google."
            )
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.warning("GEMINI_API_KEY not found in environment variables")

            model_name = os.getenv("GEMINI_EMBEDDING_MODEL", "models/embedding-001")
            return GoogleGenerativeAIEmbeddings(
                model=model_name, google_api_key=api_key
            )

    def generate_response(
        self,
        query: str,
        context: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """
        Generate a response using the LLM model based on the query and context.

        Args:
            query: User query string
            context: Code context from the vector store
            chat_history: List of previous chat messages as dictionaries with 'role' and 'content'

        Returns:
            Generated response string
        """
        try:
            # Create system message with context
            system_template = """You are a coding assistant that helps users understand and work with their codebase.
Answer the user's question based on the code context provided below. 
Be specific and reference relevant parts of the code in your explanation.
If the context doesn't contain enough information to answer the question, say so.

CODE CONTEXT:
{context}
"""
            system_message_prompt = SystemMessagePromptTemplate.from_template(
                system_template
            )

            # Create human message prompt
            human_template = "{query}"
            human_message_prompt = HumanMessagePromptTemplate.from_template(
                human_template
            )

            # Create chat prompt
            chat_prompt = ChatPromptTemplate.from_messages(
                [system_message_prompt, human_message_prompt]
            )

            # Format messages
            messages = chat_prompt.format_prompt(
                context=context, query=query
            ).to_messages()

            # Convert chat history if provided
            if chat_history:
                history_messages = []
                for msg in chat_history[
                    :-1
                ]:  # Exclude the current query which we already formatted
                    role = msg.get("role", "user")
                    content = msg.get("content", "")

                    if not content.strip():
                        continue

                    if role == "user":
                        history_messages.append(HumanMessage(content=content))
                    elif role == "assistant":
                        history_messages.append(AIMessage(content=content))
                    elif role == "system":
                        history_messages.append(SystemMessage(content=content))

                # Insert history before current query but after system message
                if history_messages:
                    messages = [messages[0]] + history_messages + [messages[-1]]

            # Generate response
            response = self.llm(messages)

            # Extract response content
            if hasattr(response, "content"):
                return response.content
            else:
                return str(response)

        except Exception as e:
            logger.error(f"Failed to generate response: {str(e)}")
            # Fallback error response
            return f"I'm sorry, I encountered an error while generating a response: {str(e)}"

    def pad_embedding(self, embedding, target_dim=1024):
        """Pad embedding with zeros to reach target dimension"""
        current_dim = len(embedding)

        if current_dim == target_dim:
            return embedding
        elif current_dim > target_dim:
            return embedding[:target_dim]  # Truncate if larger

        # Pad with zeros
        padding = [0.0] * (target_dim - current_dim)
        return embedding + padding

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of text strings.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors
        """
        try:
            # Check if there are any texts to embed
            if not texts:
                return []

            # Generate embeddings using the configured provider
            embeddings = self.embedding_model.embed_documents(
                texts, output_dimensionality=1024
            )

            padded_embeddings = []
            for embedding in embeddings:
                padded_embeddings.append(self.pad_embedding(embedding))

            return padded_embeddings

        except Exception as e:
            logger.error(f"Failed to generate embeddings: {str(e)}")
            # Return empty embeddings for all texts as fallback
            # Using a standard embedding dimension, adjust based on your model
            embedding_dim = 1024
            return [[0.0] * embedding_dim] * len(texts)
