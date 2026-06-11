from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    llm_provider: str = "anthropic"

    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimensions: int = 384
    embedding_device: str = "cpu"

    prompts_config_path: str = ""

    database_url: str = "postgresql+asyncpg://rag:ragpassword@localhost:5430/ragdb"
    upload_dir: str = "./uploads"

    rag_mode: str = "hybrid"
    rerank_enabled: bool = False

    langfuse_enabled: bool = True
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "http://localhost:3000"

    chunk_size: int = 512
    chunk_overlap: int = 50
    sliding_stride: int = 256

    vector_top_k: int = 20
    keyword_top_k: int = 20
    hybrid_top_k: int = 10
    naive_top_k: int = 10
    rerank_top_k: int = 5
    rrf_k: int = 60


settings = Settings()
