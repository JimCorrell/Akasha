from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="AKASHA_")

    vault_path: Path = Path.home() / "vault" / "akasha"
    chroma_path: Path = Path.home() / ".akasha" / "chroma"
    # backend: "local" (fastembed, no API key) or "openai"
    embedding_backend: str = "local"
    local_embedding_model: str = "BAAI/bge-small-en-v1.5"
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    api_host: str = "127.0.0.1"
    api_port: int = 8765
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-6"


settings = Settings()
