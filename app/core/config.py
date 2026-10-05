"""Environment-backed settings.

The shape follows a small settings object loaded from the process environment
and an optional .env file. Test runs skip .env so unit tests cannot pick up a
developer API key.
"""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
LOCAL_JWT_SECRET = "local-demo-jwt-secret-not-for-production-00"


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


def get_environment() -> Environment:
    raw = os.getenv("APP_ENV", "development").lower()
    if raw in {"production", "prod"}:
        return Environment.PRODUCTION
    if raw in {"staging", "stage"}:
        return Environment.STAGING
    if raw == "test":
        return Environment.TEST
    return Environment.DEVELOPMENT


def load_env_file() -> str | None:
    env = get_environment()
    if env is Environment.TEST:
        return None
    for name in (f".env.{env.value}", ".env"):
        path = ROOT / name
        if path.is_file():
            load_dotenv(path, override=False)
            return str(path)
    return None


ENV_FILE = load_env_file()


def _flag(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


class Settings:
    """Runtime settings. Instantiate once via the module-level `settings`."""

    def __init__(self) -> None:
        self.ENVIRONMENT = get_environment()
        self.PROJECT_NAME = os.getenv("PROJECT_NAME", "bank-doc-rag")
        self.VERSION = os.getenv("VERSION", "0.1.0")
        self.DESCRIPTION = os.getenv(
            "DESCRIPTION",
            "Personal portfolio RAG over synthetic multilingual bank-style documents.",
        )
        self.API_V1_STR = "/api/v1"

        self.OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
        self.OPENROUTER_BASE_URL = os.getenv(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
        ).rstrip("/")
        self.CHAT_MODEL = os.getenv("CHAT_MODEL", "openai/gpt-6-luna")
        self.EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "openai/text-embedding-3-small")
        self.EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1536"))
        self.LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "90"))

        self.QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "bank_docs")
        self.QDRANT_LOCATION = os.getenv("QDRANT_LOCATION", "")
        self.QDRANT_PATH = os.getenv("QDRANT_PATH", "")
        self.RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "8"))
        self.OFFLINE_DEMO = _flag("OFFLINE_DEMO", False)

        self.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", LOCAL_JWT_SECRET)
        self.JWT_ALGORITHM = "HS256"
        self.JWT_EXPIRE_DAYS = int(os.getenv("JWT_EXPIRE_DAYS", "7"))
        self.DEMO_USERNAME = os.getenv("DEMO_USERNAME", "demo")
        self.DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "demo-not-a-bank")
        self.AUTH_REQUIRED = _flag("AUTH_REQUIRED", False)

        self.LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "")
        self.LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "")
        self.LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self._validate_jwt()

    def _validate_jwt(self) -> None:
        if self.ENVIRONMENT is not Environment.PRODUCTION:
            return
        secret = self.JWT_SECRET_KEY.strip()
        if len(secret) < 32 or secret == LOCAL_JWT_SECRET:
            raise RuntimeError(
                "Production requires JWT_SECRET_KEY of at least 32 characters "
                "and a value other than the local demo default."
            )


settings = Settings()
