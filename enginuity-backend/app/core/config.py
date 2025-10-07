from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache

class Settings(BaseSettings):
    POSTGRES_URL: str = "postgresql+psycopg2://user:password@localhost:5432/enginuity"
    VECTORDB_PROVIDER: str = "chroma"  # chroma|faiss|pinecone
    VECTORDB_DIR: str = "./vector_index"
    PINECONE_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    EMBEDDING_MODEL: str = "text-embedding-3-large"
    LLM_MODEL: str = "gpt-4o-mini"
    CORS_ALLOW_ORIGINS: str = "http://localhost:8501"
    DATA_DIR: str = "../data"

    class Config:
        env_file = ".env"

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
