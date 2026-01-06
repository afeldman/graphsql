"""Application settings loaded from environment variables via python-decouple."""
from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from typing import List

from decouple import config as env_config


@dataclass(slots=True)
class Settings:
    """Typed container for application configuration.

    Environment variables are parsed with ``python-decouple`` so that values can
    be provided via ``.env`` files or the process environment.

    Examples:
        Instantiate from the current environment and inspect flags::

            settings = Settings.load()
            assert settings.is_sqlite is True
            assert settings.cors_origins == ["*"]
    """

    database_url: str
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    api_key: str = ""
    enable_auth: bool = False
    default_page_size: int = 50
    max_page_size: int = 1000
    log_level: str = "INFO"
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 1440  # 24 hours
    rate_limit_default: str = "60/minute"
    rate_limit_tables: str = "100/minute"
    rate_limit_storage_uri: str = "memory://"
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 300
    cache_prefix: str = "graphsql:cache:"
    session_ttl_seconds: int = 86400
    session_prefix: str = "graphsql:session:"

    @classmethod
    def load(cls) -> "Settings":
        """Build a settings instance from environment variables.

        Returns:
            A populated ``Settings`` object with sane defaults.

        Environment keys
        ----------------
        - ``DATABASE_URL``: SQLAlchemy database URL (default ``sqlite:///./database.db``)
        - ``API_HOST``: Bind host for FastAPI/uvicorn (default ``0.0.0.0``)
        - ``API_PORT``: Bind port (default ``8000``)
        - ``API_RELOAD``: Enable auto-reload in development (default ``true``)
        - ``CORS_ORIGINS``: Comma-separated allowed origins or ``*`` (default ``*``)
        - ``API_KEY``: Optional API key to enable auth
        - ``ENABLE_AUTH``: Toggle API key enforcement (default ``false``)
        - ``DEFAULT_PAGE_SIZE``: Page size for REST/GraphQL listings (default ``50``)
        - ``MAX_PAGE_SIZE``: Max page size allowed (default ``1000``)
        - ``LOG_LEVEL``: Log level for the service (default ``INFO``)
        - ``JWT_SECRET_KEY``: Secret key for JWT encoding (auto-generated if not set)
        - ``JWT_ALGORITHM``: JWT algorithm (default ``HS256``)
        - ``JWT_EXPIRATION_MINUTES``: JWT expiration in minutes (default ``1440``)
        - ``RATE_LIMIT_DEFAULT``: Default rate limit (default ``60/minute``)
        - ``RATE_LIMIT_TABLES``: Rate limit for table endpoints (default ``100/minute``)
        - ``RATE_LIMIT_STORAGE_URI``: Backend for rate limiting (default ``memory://``)
        - ``REDIS_URL``: Redis connection URL for caching/sessions (default ``redis://localhost:6379/0``)
        - ``CACHE_TTL_SECONDS``: Default cache TTL in seconds (default ``300``)
        - ``CACHE_PREFIX``: Cache key prefix (default ``graphsql:cache:"`)
        - ``SESSION_TTL_SECONDS``: Session TTL in seconds (default ``86400``)
        - ``SESSION_PREFIX``: Session key prefix (default ``graphsql:session:"`)

        Examples:
            >>> settings = Settings.load()
            >>> settings.api_port
            8000
        """

        raw_cors = env_config("CORS_ORIGINS", default="*")
        jwt_secret = env_config("JWT_SECRET_KEY", default="")
        if not jwt_secret:
            jwt_secret = secrets.token_urlsafe(32)

        return cls(
            database_url=env_config("DATABASE_URL", default="sqlite:///./database.db"),
            api_host=env_config("API_HOST", default="0.0.0.0"),
            api_port=env_config("API_PORT", cast=int, default=8000),
            api_reload=env_config("API_RELOAD", cast=bool, default=True),
            cors_origins=cls.parse_cors_origins(raw_cors),
            api_key=env_config("API_KEY", default=""),
            enable_auth=env_config("ENABLE_AUTH", cast=bool, default=False),
            default_page_size=env_config("DEFAULT_PAGE_SIZE", cast=int, default=50),
            max_page_size=env_config("MAX_PAGE_SIZE", cast=int, default=1000),
            log_level=env_config("LOG_LEVEL", default="INFO"),
            jwt_secret_key=jwt_secret,
            jwt_algorithm=env_config("JWT_ALGORITHM", default="HS256"),
            jwt_expiration_minutes=env_config("JWT_EXPIRATION_MINUTES", cast=int, default=1440),
            rate_limit_default=env_config("RATE_LIMIT_DEFAULT", default="60/minute"),
            rate_limit_tables=env_config("RATE_LIMIT_TABLES", default="100/minute"),
            rate_limit_storage_uri=env_config("RATE_LIMIT_STORAGE_URI", default="memory://"),
            redis_url=env_config("REDIS_URL", default="redis://localhost:6379/0"),
            cache_ttl_seconds=env_config("CACHE_TTL_SECONDS", cast=int, default=300),
            cache_prefix=env_config("CACHE_PREFIX", default="graphsql:cache:"),
            session_ttl_seconds=env_config("SESSION_TTL_SECONDS", cast=int, default=86400),
            session_prefix=env_config("SESSION_PREFIX", default="graphsql:session:"),
        )

    @staticmethod
    def parse_cors_origins(raw: str) -> List[str]:
        """Convert a comma-separated origins string into a list.

        Args:
            raw: Raw origins value from configuration.

        Returns:
            List of individual origins; returns ["*"] when wildcard is used.

        Examples:
            >>> Settings.parse_cors_origins("https://a.com,https://b.com")
            ['https://a.com', 'https://b.com']
            >>> Settings.parse_cors_origins("*")
            ['*']
        """
        if raw == "*":
            return ["*"]
        return [origin.strip() for origin in raw.split(",") if origin.strip()]

    @property
    def JWT_SECRET_KEY(self) -> str:
        """Get JWT secret key."""
        return self.jwt_secret_key

    @property
    def JWT_ALGORITHM(self) -> str:
        """Get JWT algorithm."""
        return self.jwt_algorithm

    @property
    def JWT_EXPIRATION_MINUTES(self) -> int:
        """Get JWT expiration minutes."""
        return self.jwt_expiration_minutes

    @property
    def RATE_LIMIT_DEFAULT(self) -> str:
        """Get default rate limit string."""
        return self.rate_limit_default

    @property
    def RATE_LIMIT_TABLES(self) -> str:
        """Get tables rate limit string."""
        return self.rate_limit_tables

    @property
    def RATE_LIMIT_STORAGE_URI(self) -> str:
        """Get rate limit storage URI."""
        return self.rate_limit_storage_uri

    @property
    def REDIS_URL(self) -> str:
        """Get Redis connection URL."""
        return self.redis_url

    @property
    def CACHE_TTL_SECONDS(self) -> int:
        """Get default cache TTL."""
        return self.cache_ttl_seconds

    @property
    def CACHE_PREFIX(self) -> str:
        """Get cache key prefix."""
        return self.cache_prefix

    @property
    def SESSION_TTL_SECONDS(self) -> int:
        """Get session TTL."""
        return self.session_ttl_seconds

    @property
    def SESSION_PREFIX(self) -> str:
        """Get session key prefix."""
        return self.session_prefix

    @property
    def is_sqlite(self) -> bool:
        """Return whether the configured database is SQLite."""
        return self.database_url.startswith("sqlite")

    @property
    def is_postgres(self) -> bool:
        """Return whether the configured database is PostgreSQL."""
        return self.database_url.startswith(("postgresql", "postgres"))

    @property
    def is_mysql(self) -> bool:
        """Return whether the configured database is MySQL."""
        return self.database_url.startswith("mysql")


# Global settings instance
settings = Settings.load()
