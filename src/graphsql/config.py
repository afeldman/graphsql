"""Configuration management using pydantic-settings."""
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Database
    database_url: str = Field(
        default="sqlite:///./database.db",
        description="Database connection URL"
    )
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_reload: bool = Field(default=True, description="Enable auto-reload")
    
    # CORS
    cors_origins: str = Field(default="*", description="Allowed CORS origins")
    
    @field_validator("cors_origins")
    @classmethod
    def parse_cors_origins(cls, v: str) -> List[str]:
        """Convert a comma-separated origins string into a list.

        Args:
            v: Raw origins value from configuration.

        Returns:
            List of individual origins; returns ["*"] when wildcard is used.

        Examples:
            >>> Settings.parse_cors_origins("https://a.com,https://b.com")
            ['https://a.com', 'https://b.com']
            >>> Settings.parse_cors_origins("*")
            ['*']
        """
        if v == "*":
            return ["*"]
        return [origin.strip() for origin in v.split(",")]
    
    # Security
    api_key: str = Field(default="", description="API key for authentication")
    enable_auth: bool = Field(default=False, description="Enable authentication")
    
    # Pagination
    default_page_size: int = Field(default=50, ge=1, le=1000)
    max_page_size: int = Field(default=1000, ge=1, le=10000)
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    
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
settings = Settings()
