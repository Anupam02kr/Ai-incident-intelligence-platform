from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "incident-api"
    debug: bool = False

    base_dir: Path = Path(__file__).resolve().parent
    data_dir: Path = base_dir / "data"
    chroma_dir: Path = data_dir / "chroma"
    uploads_dir: Path = data_dir / "uploads"
    docs_dir: Path = data_dir / "docs"

    database_url: str = "sqlite+aiosqlite:///./data/incidents.db"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    summarization_model: str = "facebook/bart-large-cnn"
    rag_top_k: int = 4
    max_log_chars: int = 12000

    openai_api_key: str | None = None
    llm_provider: str = "local"
    tesseract_cmd: str | None = None


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    for d in (s.data_dir, s.chroma_dir, s.uploads_dir, s.docs_dir):
        d.mkdir(parents=True, exist_ok=True)
    return s
