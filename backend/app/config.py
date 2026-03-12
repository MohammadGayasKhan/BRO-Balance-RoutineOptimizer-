"""Application-wide configuration loaded from environment variables."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/


class _Settings:
    """Simple settings object populated from env vars at import time."""

    # LLM (Groq / xAI / any OpenAI-compatible provider)
    GROK_API_KEY: str = os.getenv("GROK_API_KEY", "")
    GROK_MODEL: str = os.getenv("GROK_MODEL", "llama-3.3-70b-versatile")
    GROK_BASE_URL: str = os.getenv("GROK_BASE_URL", "https://api.groq.com/openai/v1")

    # Google OAuth
    GOOGLE_CREDENTIALS_FILE: Path = BASE_DIR / os.getenv(
        "GOOGLE_CREDENTIALS_FILE", "credentials.json"
    )
    GOOGLE_TOKEN_FILE: Path = BASE_DIR / os.getenv("GOOGLE_TOKEN_FILE", "token.json")
    GOOGLE_SCOPES: list[str] = ["https://www.googleapis.com/auth/calendar"]
    GOOGLE_REDIRECT_URI: str = os.getenv(
        "GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/callback"
    )

    # Pinecone (optional)
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "rythmind-kb")

    # Session
    SESSION_SECRET: str = os.getenv("SESSION_SECRET", "dev-secret-change-me")

    # CORS
    CORS_ORIGINS: List[str] = json.loads(
        os.getenv("CORS_ORIGINS", '["http://localhost:4200"]')
    )

    # Frontend redirect after OAuth
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:4200")


settings = _Settings()
