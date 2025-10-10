# app/core/config.py
from functools import lru_cache
from typing import List, Optional, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict # pyright: ignore[reportMissingImports]


class Settings(BaseSettings):
    # --- Core ---
    POSTGRES_URL: str = "postgresql+psycopg2://user:password@localhost:5432/enginuity"

    # --- Vector DB ---
    VECTORDB_PROVIDER: str = "chroma"  # chroma|faiss|pinecone
    VECTORDB_DIR: str = "./vector_index"
    PINECONE_API_KEY: Optional[str] = None

    # --- OpenAI / LLM ---
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"           # <— added (frontend used LLM_MODEL)
    EMBEDDING_MODEL: str = "text-embedding-3-large"
    LLM_MODEL: str = "gpt-4o-mini"              # keep for backward-compat; use OPENAI_MODEL in new code

    # --- App / CORS / Data ---
    CORS_ALLOW_ORIGINS: Union[str, List[str]] = "http://localhost:8501"
    DATA_DIR: str = "../data"

    # pydantic-settings v2 style
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("CORS_ALLOW_ORIGINS", mode="before")
    @classmethod
    def _split_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            # allow CSV string in .env: CORS_ALLOW_ORIGINS=http://a,http://b
            return [s.strip() for s in v.split(",") if s.strip()]
        return ["http://localhost:8501"]

    # convenience flags
    @property
    def openai_enabled(self) -> bool:
        return bool(self.OPENAI_API_KEY)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
