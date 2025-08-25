import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # OpenAI Configuration
    openai_api_key: str = ""
    openai_model: str = "gpt-3.5-turbo"
    openai_embedding_model: str = "text-embedding-ada-002"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8001
    debug: bool = False
    
    # Vector Database Configuration
    chroma_persist_directory: str = "./chroma_db"
    
    # RAG Configuration
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_tokens: int = 1000
    
    # Document Storage
    data_directory: str = "./data"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Validate required settings
if not settings.openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable is required")
