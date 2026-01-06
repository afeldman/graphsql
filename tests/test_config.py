"""Unit tests for configuration module."""
from typing import Any

from graphsql.config import Settings


class TestSettingsLoading:
    """Test Settings.load() method."""

    def test_load_defaults(self, monkeypatch: Any) -> None:
        """Test loading settings with minimal environment."""
        monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")

        settings = Settings.load()

        assert settings.database_url == "sqlite:///test.db"
        assert settings.api_host == "0.0.0.0"
        assert settings.api_port == 8000
        assert settings.api_reload is True
        assert settings.log_level == "INFO"

    def test_load_with_custom_values(self, monkeypatch: Any) -> None:
        """Test loading settings with custom environment values."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/graphsql")
        monkeypatch.setenv("API_HOST", "127.0.0.1")
        monkeypatch.setenv("API_PORT", "9000")
        monkeypatch.setenv("API_RELOAD", "false")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")

        settings = Settings.load()

        assert settings.database_url == "postgresql://localhost/graphsql"
        assert settings.api_host == "127.0.0.1"
        assert settings.api_port == 9000
        assert settings.api_reload is False
        assert settings.log_level == "DEBUG"

    def test_load_cors_origins(self, monkeypatch: Any) -> None:
        """Test parsing CORS origins from environment."""
        monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
        monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080")

        settings = Settings.load()

        assert settings.cors_origins == ["http://localhost:3000", "http://localhost:8080"]

    def test_database_type_detection_sqlite(self, monkeypatch: Any) -> None:
        """Test SQLite database type detection."""
        monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")

        settings = Settings.load()

        assert settings.is_sqlite is True
        assert settings.is_postgres is False
        assert settings.is_mysql is False

    def test_database_type_detection_postgres(self, monkeypatch: Any) -> None:
        """Test PostgreSQL database type detection."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")

        settings = Settings.load()

        assert settings.is_sqlite is False
        assert settings.is_postgres is True
        assert settings.is_mysql is False

    def test_database_type_detection_mysql(self, monkeypatch: Any) -> None:
        """Test MySQL database type detection."""
        monkeypatch.setenv("DATABASE_URL", "mysql+pymysql://user:pass@localhost/db")

        settings = Settings.load()

        assert settings.is_sqlite is False
        assert settings.is_postgres is False
        assert settings.is_mysql is True

    def test_auth_settings(self, monkeypatch: Any) -> None:
        """Test authentication settings."""
        monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
        monkeypatch.setenv("ENABLE_AUTH", "true")
        monkeypatch.setenv("API_KEY", "secret-key-123")

        settings = Settings.load()

        assert settings.enable_auth is True
        assert settings.api_key == "secret-key-123"

    def test_pagination_settings(self, monkeypatch: Any) -> None:
        """Test pagination settings."""
        monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
        monkeypatch.setenv("DEFAULT_PAGE_SIZE", "100")
        monkeypatch.setenv("MAX_PAGE_SIZE", "5000")

        settings = Settings.load()

        assert settings.default_page_size == 100
        assert settings.max_page_size == 5000
