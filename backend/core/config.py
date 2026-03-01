"""
Application configuration — reads from environment variables.
Copy .env.example to .env and fill in the values.
"""

import os
from typing import List

# Load .env file if present (dev convenience)
try:
    from dotenv import load_dotenv
    load_dotenv(override=False)   # don't override already-set env vars
except ImportError:
    pass


class Settings:
    ENV: str                   = os.getenv("ENV", "development")
    SECRET_KEY: str            = os.getenv("SECRET_KEY", "change-me-in-production-please")
    API_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("API_TOKEN_EXPIRE_MINUTES", "480"))  # 8 h

    # Hosts / CORS
    # Set ALLOWED_HOSTS=* and ALLOWED_ORIGINS=* on Railway to accept any domain
    ALLOWED_HOSTS: List[str]   = os.getenv("ALLOWED_HOSTS", "*").split(",")
    _raw_origins: str          = os.getenv("ALLOWED_ORIGINS", "*")
    ALLOWED_ORIGINS: List[str] = ["*"] if _raw_origins.strip() == "*" else _raw_origins.split(",")

    # PostgreSQL connection string
    # Format: postgresql://user:password@host:port/dbname
    # Railway provides DATABASE_URL as postgres:// — psycopg2 needs postgresql://
    _db_url: str               = os.getenv(
        "DATABASE_URL",
        "postgresql://dcuser:dcpassword@localhost:5432/debugchamp"
    )
    DATABASE_URL: str          = _db_url.replace("postgres://", "postgresql://", 1) if _db_url.startswith("postgres://") else _db_url

    # Test runner
    PYTEST_TIMEOUT: int        = int(os.getenv("PYTEST_TIMEOUT", "60"))   # seconds per run
    REPO_ROOT: str             = os.getenv("REPO_ROOT", os.path.abspath(os.path.join(
                                     os.path.dirname(__file__), "..", "..")))

    # Admin
    ADMIN_USERNAME: str        = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str        = os.getenv("ADMIN_PASSWORD", "admin")   # override in .env!


settings = Settings()
