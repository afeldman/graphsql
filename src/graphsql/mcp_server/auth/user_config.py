"""User-specific database configuration store.

This module provides encrypted storage for user-specific database configurations.
Each user's database connection details are stored securely and can be retrieved
when they authenticate via SSO.

Example:
    >>> from graphsql.mcp_server.auth.user_config import (
    ...     FileConfigStore, EncryptionKey, UserDatabaseConfig
    ... )
    >>> key = EncryptionKey.generate()
    >>> store = FileConfigStore(Path("./configs"), key)
    >>> config = UserDatabaseConfig(
    ...     user_id="user123",
    ...     database_url="postgresql://user:pass@host/db",
    ... )
    >>> await store.save_config(config)
"""

from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Self

from cryptography.fernet import Fernet
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field


class UserDatabaseConfig(BaseModel):
    """User-specific database configuration.

    This model holds all database connection and query settings for a specific user.
    It is stored encrypted and retrieved when the user authenticates.

    Attributes:
        user_id: User identifier from SSO (optional, can be set during save).
        database_url: SQLAlchemy-compatible database connection URL.
        database_name: Optional database name override.
        schema_name: Optional schema name for PostgreSQL.
        description: Optional description for this configuration.
        read_only: Whether to enforce read-only mode.
        max_rows: Maximum rows returned per query.
        query_timeout: Query execution timeout in seconds.
        allowed_tables: Whitelist of allowed tables (empty = all allowed).
        blocked_tables: Blacklist of blocked tables.
        connection_pool_size: Database connection pool size.
        extra_options: Additional database options.
    """

    user_id: str | None = Field(default=None, description="User identifier from SSO")
    database_url: str = Field(description="Database connection URL")
    database_name: str | None = Field(default=None, description="Database name")
    description: str | None = Field(default=None, description="Configuration description")
    schema_name: str | None = Field(default=None, description="Schema name")
    read_only: bool = Field(default=True, description="Read-only mode")
    max_rows: int = Field(default=1000, description="Maximum rows per query")
    query_timeout: int = Field(default=30, description="Query timeout in seconds")
    allowed_tables: list[str] = Field(
        default_factory=list,
        description="Whitelist of allowed tables",
    )
    blocked_tables: list[str] = Field(
        default_factory=list,
        description="Blacklist of blocked tables",
    )
    connection_pool_size: int = Field(default=5, description="Connection pool size")
    extra_options: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional database options",
    )

    def to_connection_string(self) -> str:
        """Generate connection string with options.

        Returns:
            Database connection URL, optionally with database name appended.
        """
        url = self.database_url
        if self.database_name and "/" not in url.split("://")[-1]:
            url = f"{url}/{self.database_name}"
        return url

    def get_masked_url(self) -> str:
        """Get connection URL with password masked.

        Returns:
            Connection URL with password replaced by asterisks.
        """
        import re

        return re.sub(r"://([^:]+):([^@]+)@", r"://\1:****@", self.database_url)


class EncryptionKey(BaseModel):
    """Encryption key management for secure config storage.

    Uses Fernet symmetric encryption (AES-128 in CBC mode with HMAC).

    Attributes:
        key: 32-byte base64-encoded Fernet key.
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    key: bytes

    @classmethod
    def generate(cls) -> Self:
        """Generate a new random encryption key.

        Returns:
            New EncryptionKey instance with random key.
        """
        return cls(key=Fernet.generate_key())

    @classmethod
    def from_string(cls, key_str: str) -> Self:
        """Create from string representation.

        Args:
            key_str: Base64-encoded key string or raw string to use as key.

        Returns:
            EncryptionKey instance.
        """
        # Try to use as-is first (if it's a valid Fernet key)
        if len(key_str) == 44 and key_str.endswith("="):
            return cls(key=key_str.encode())
        # Otherwise derive a key from the string
        import base64

        derived = hashlib.sha256(key_str.encode()).digest()
        return cls(key=base64.urlsafe_b64encode(derived))

    def to_string(self) -> str:
        """Convert key to string representation.

        Returns:
            Base64-encoded key string.
        """
        return self.key.decode()

    def encrypt(self, data: str) -> str:
        """Encrypt string data.

        Args:
            data: Plain text data to encrypt.

        Returns:
            Base64-encoded encrypted data.
        """
        f = Fernet(self.key)
        return f.encrypt(data.encode()).decode()

    def decrypt(self, encrypted: str) -> str:
        """Decrypt encrypted data.

        Args:
            encrypted: Base64-encoded encrypted data.

        Returns:
            Decrypted plain text.

        Raises:
            cryptography.fernet.InvalidToken: If decryption fails.
        """
        f = Fernet(self.key)
        return f.decrypt(encrypted.encode()).decode()


class UserConfigStore(ABC):
    """Abstract base for user configuration storage.

    Implement this interface to create custom storage backends
    (e.g., database, cloud storage, etc.).
    """

    @abstractmethod
    async def get_config(self, user_id: str) -> UserDatabaseConfig | None:
        """Get configuration for a user.

        Args:
            user_id: User identifier from SSO.

        Returns:
            User's database configuration or None if not found.
        """
        ...

    @abstractmethod
    async def save_config(self, user_id: str, config: UserDatabaseConfig) -> None:
        """Save user configuration.

        Args:
            user_id: User identifier from SSO.
            config: User database configuration to save.
        """
        ...

    @abstractmethod
    async def delete_config(self, user_id: str) -> None:
        """Delete user configuration.

        Args:
            user_id: User identifier from SSO.
        """
        ...

    @abstractmethod
    async def list_users(self) -> list[str]:
        """List all configured users.

        Returns:
            List of user identifiers.
        """
        ...

    async def has_config(self, user_id: str) -> bool:
        """Check if configuration exists for user.

        Args:
            user_id: User identifier from SSO.

        Returns:
            True if configuration exists.
        """
        return await self.get_config(user_id) is not None


class InMemoryConfigStore(UserConfigStore):
    """In-memory configuration store.

    Useful for testing and development. Configurations are lost when
    the process exits.

    Attributes:
        _configs: Internal storage dictionary.
    """

    def __init__(self) -> None:
        """Initialize in-memory config store."""
        self._configs: dict[str, UserDatabaseConfig] = {}

    async def get_config(self, user_id: str) -> UserDatabaseConfig | None:
        """Get configuration for a user.

        Args:
            user_id: User identifier from SSO.

        Returns:
            User's database configuration or None if not found.
        """
        return self._configs.get(user_id)

    async def save_config(self, user_id: str, config: UserDatabaseConfig) -> None:
        """Save user configuration.

        Args:
            user_id: User identifier from SSO.
            config: User database configuration to save.
        """
        config.user_id = user_id
        self._configs[user_id] = config
        logger.debug(
            "Saved configuration to in-memory store",
            user_id=user_id,
            database_url=(
                config.database_url[:30] + "..."
                if len(config.database_url) > 30
                else config.database_url
            ),
            read_only=config.read_only,
        )

    async def delete_config(self, user_id: str) -> None:
        """Delete user configuration.

        Args:
            user_id: User identifier from SSO.
        """
        self._configs.pop(user_id, None)
        logger.debug(
            "Deleted configuration from in-memory store",
            user_id=user_id,
        )

    async def list_users(self) -> list[str]:
        """List all configured users.

        Returns:
            List of user identifiers.
        """
        return list(self._configs.keys())

    def clear(self) -> None:
        """Clear all stored configurations."""
        self._configs.clear()


class FileConfigStore(UserConfigStore):
    """File-based configuration store with encryption.

    Stores each user's configuration as an encrypted JSON file.
    User IDs are hashed for filesystem safety.

    Attributes:
        base_path: Directory where config files are stored.
        encryption_key: Key for encrypting configuration data.
    """

    def __init__(self, base_path: Path, encryption_key: EncryptionKey) -> None:
        """Initialize file config store.

        Args:
            base_path: Directory where config files are stored.
            encryption_key: Key for encrypting configuration data.
        """
        self.base_path = base_path
        self.encryption_key = encryption_key
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(
            "Initialized file-based config store",
            base_path=str(self.base_path),
            encryption_algorithm="Fernet (AES-128-CBC)",
        )

    def _get_user_file(self, user_id: str) -> Path:
        """Get file path for user config.

        User IDs are hashed to ensure filesystem-safe filenames.

        Args:
            user_id: User identifier from SSO.

        Returns:
            Path to the user's encrypted config file.
        """
        hashed = hashlib.sha256(user_id.encode()).hexdigest()[:16]
        return self.base_path / f"{hashed}.enc"

    def _get_index_file(self) -> Path:
        """Get path to user index file.

        Returns:
            Path to the index file.
        """
        return self.base_path / ".index.enc"

    async def _load_index(self) -> dict[str, str]:
        """Load user ID to hash mapping.

        Returns:
            Dictionary mapping user IDs to their file hashes.
        """
        index_file = self._get_index_file()
        if not index_file.exists():
            return {}
        try:
            encrypted = index_file.read_text()
            decrypted = self.encryption_key.decrypt(encrypted)
            result: dict[str, str] = json.loads(decrypted)
            return result
        except Exception:
            return {}

    async def _save_index(self, index: dict[str, str]) -> None:
        """Save user ID to hash mapping.

        Args:
            index: Dictionary mapping user IDs to their file hashes.
        """
        index_file = self._get_index_file()
        encrypted = self.encryption_key.encrypt(json.dumps(index))
        index_file.write_text(encrypted)

    async def get_config(self, user_id: str) -> UserDatabaseConfig | None:
        """Get configuration for a user.

        Args:
            user_id: User identifier from SSO.

        Returns:
            User's database configuration or None if not found.
        """
        file_path = self._get_user_file(user_id)
        if not file_path.exists():
            return None

        try:
            encrypted = file_path.read_text()
            decrypted = self.encryption_key.decrypt(encrypted)
            data = json.loads(decrypted)
            return UserDatabaseConfig(**data)
        except Exception as e:
            logger.error(
                "Failed to load configuration from file store",
                user_id=user_id,
                error=str(e),
                file_path=str(file_path),
            )
            return None

    async def save_config(self, user_id: str, config: UserDatabaseConfig) -> None:
        """Save user configuration.

        Args:
            user_id: User identifier from SSO.
            config: User database configuration to save.
        """
        config.user_id = user_id
        file_path = self._get_user_file(user_id)
        data = config.model_dump()
        encrypted = self.encryption_key.encrypt(json.dumps(data))
        file_path.write_text(encrypted)

        # Update index
        index = await self._load_index()
        index[user_id] = file_path.stem
        await self._save_index(index)

        logger.info(
            "Saved encrypted configuration to file store",
            user_id=user_id,
            file_path=str(file_path),
            read_only=config.read_only,
            config_size_bytes=len(encrypted),
        )

    async def delete_config(self, user_id: str) -> None:
        """Delete user configuration.

        Args:
            user_id: User identifier from SSO.
        """
        file_path = self._get_user_file(user_id)
        if file_path.exists():
            file_path.unlink()

        # Update index
        index = await self._load_index()
        index.pop(user_id, None)
        await self._save_index(index)

        logger.info(
            "Deleted configuration from file store",
            user_id=user_id,
            file_existed=file_path.exists(),
        )

    async def list_users(self) -> list[str]:
        """List all configured users.

        Returns:
            List of user identifiers.
        """
        index = await self._load_index()
        return list(index.keys())


class RedisConfigStore(UserConfigStore):
    """Redis-based configuration store with encryption.

    Uses Redis for distributed, persistent configuration storage.
    Suitable for multi-instance deployments.

    Attributes:
        redis_url: Redis connection URL.
        encryption_key: Key for encrypting configuration data.
        prefix: Key prefix for all stored configs.
        ttl: Optional TTL for stored configs in seconds.
    """

    def __init__(
        self,
        redis_url: str,
        encryption_key: EncryptionKey,
        prefix: str = "graphsql:user_config:",
        ttl: int | None = None,
    ) -> None:
        """Initialize Redis config store.

        Args:
            redis_url: Redis connection URL.
            encryption_key: Key for encrypting configuration data.
            prefix: Key prefix for all stored configs.
            ttl: Optional TTL for stored configs in seconds.
        """
        self.redis_url = redis_url
        self.encryption_key = encryption_key
        self.prefix = prefix
        self.ttl = ttl
        self._client: Any = None

    async def _get_client(self) -> Any:
        """Get or create Redis client.

        Returns:
            Async Redis client.
        """
        if self._client is None:
            try:
                import redis.asyncio as redis

                self._client = redis.from_url(self.redis_url)
            except ImportError as e:
                raise ImportError(
                    "Redis support requires the 'redis' package. "
                    "Install it with: pip install redis"
                ) from e
        return self._client

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None

    async def get_config(self, user_id: str) -> UserDatabaseConfig | None:
        """Get configuration for a user.

        Args:
            user_id: User identifier from SSO.

        Returns:
            User's database configuration or None if not found.
        """
        client = await self._get_client()
        encrypted = await client.get(f"{self.prefix}{user_id}")
        if encrypted is None:
            return None

        try:
            decrypted = self.encryption_key.decrypt(encrypted.decode())
            data = json.loads(decrypted)
            return UserDatabaseConfig(**data)
        except Exception as e:
            logger.error(
                "Failed to load configuration from Redis",
                user_id=user_id,
                error=str(e),
            )
            return None

    async def save_config(self, user_id: str, config: UserDatabaseConfig) -> None:
        """Save user configuration.

        Args:
            user_id: User identifier from SSO.
            config: User database configuration to save.
        """
        config.user_id = user_id
        client = await self._get_client()
        data = config.model_dump()
        encrypted = self.encryption_key.encrypt(json.dumps(data))
        key = f"{self.prefix}{user_id}"

        if self.ttl:
            await client.setex(key, self.ttl, encrypted)
        else:
            await client.set(key, encrypted)

        logger.info(
            "Saved encrypted configuration to Redis",
            user_id=user_id,
            redis_key=key,
            ttl_seconds=self.ttl,
            config_size_bytes=len(encrypted),
        )

    async def delete_config(self, user_id: str) -> None:
        """Delete user configuration.

        Args:
            user_id: User identifier from SSO.
        """
        client = await self._get_client()
        await client.delete(f"{self.prefix}{user_id}")
        logger.info(
            "Deleted configuration from Redis",
            user_id=user_id,
            redis_key=f"{self.prefix}{user_id}",
        )

    async def list_users(self) -> list[str]:
        """List all configured users.

        Returns:
            List of user identifiers.
        """
        client = await self._get_client()
        keys = await client.keys(f"{self.prefix}*")
        return [k.decode().replace(self.prefix, "") for k in keys]
