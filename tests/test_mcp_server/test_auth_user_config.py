"""Tests for user configuration storage module."""

from __future__ import annotations

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from graphsql.mcp_server.auth.user_config import (
    EncryptionKey,
    FileConfigStore,
    InMemoryConfigStore,
    UserConfigStore,
    UserDatabaseConfig,
)


class TestUserDatabaseConfig:
    """Tests for UserDatabaseConfig dataclass."""

    def test_create_config(self) -> None:
        """Test creating a database config."""
        config = UserDatabaseConfig(
            database_url="postgresql://user:pass@localhost:5432/db",
            database_name="mydb",
            description="Test database",
        )
        assert config.database_url == "postgresql://user:pass@localhost:5432/db"
        assert config.database_name == "mydb"
        assert config.description == "Test database"

    def test_config_with_defaults(self) -> None:
        """Test config with default values."""
        config = UserDatabaseConfig(
            database_url="postgresql://localhost/db",
        )
        assert config.max_rows == 1000
        assert config.query_timeout == 30
        assert config.read_only is True

    def test_config_custom_values(self) -> None:
        """Test config with custom values."""
        config = UserDatabaseConfig(
            database_url="postgresql://localhost/db",
            max_rows=5000,
            query_timeout=60,
            read_only=False,
        )
        assert config.max_rows == 5000
        assert config.query_timeout == 60
        assert config.read_only is False

    def test_config_serialization(self) -> None:
        """Test config can be serialized to dict."""
        config = UserDatabaseConfig(
            database_url="postgresql://localhost/db",
            database_name="test",
        )
        data = config.model_dump()
        assert data["database_url"] == "postgresql://localhost/db"
        assert data["database_name"] == "test"

    def test_config_from_dict(self) -> None:
        """Test config can be created from dict."""
        data = {
            "database_url": "postgresql://localhost/db",
            "database_name": "test",
        }
        config = UserDatabaseConfig(**data)
        assert config.database_url == "postgresql://localhost/db"


class TestEncryptionKey:
    """Tests for EncryptionKey class."""

    def test_generate_key(self) -> None:
        """Test generating a new encryption key."""
        key = EncryptionKey.generate()
        assert key is not None
        assert len(key.key) > 0

    def test_encrypt_decrypt_roundtrip(self) -> None:
        """Test encrypting and decrypting data."""
        key = EncryptionKey.generate()
        original = "secret data"
        encrypted = key.encrypt(original)
        assert encrypted != original
        decrypted = key.decrypt(encrypted)
        assert decrypted == original

    def test_encrypt_produces_different_output(self) -> None:
        """Test encrypting same data produces different ciphertext."""
        key = EncryptionKey.generate()
        data = "secret"
        encrypted1 = key.encrypt(data)
        encrypted2 = key.encrypt(data)
        # Fernet includes random IV, so ciphertexts differ
        assert encrypted1 != encrypted2

    def test_from_string(self) -> None:
        """Test creating key from base64 string."""
        key1 = EncryptionKey.generate()
        key_string = key1.to_string()
        key2 = EncryptionKey.from_string(key_string)

        # Both keys should produce same encryption/decryption
        data = "test data"
        encrypted = key1.encrypt(data)
        decrypted = key2.decrypt(encrypted)
        assert decrypted == data

    def test_to_string(self) -> None:
        """Test converting key to string."""
        key = EncryptionKey.generate()
        key_string = key.to_string()
        assert isinstance(key_string, str)
        assert len(key_string) > 40  # Base64 encoded key is long


class TestInMemoryConfigStore:
    """Tests for InMemoryConfigStore class."""

    @pytest.fixture
    def store(self) -> InMemoryConfigStore:
        """Create an in-memory store fixture."""
        return InMemoryConfigStore()

    @pytest.mark.asyncio
    async def test_save_and_get_config(self, store: InMemoryConfigStore) -> None:
        """Test saving and retrieving a config."""
        config = UserDatabaseConfig(
            database_url="postgresql://localhost/db",
            database_name="test",
        )
        await store.save_config("user123", config)
        retrieved = await store.get_config("user123")
        assert retrieved is not None
        assert retrieved.database_url == config.database_url

    @pytest.mark.asyncio
    async def test_get_nonexistent_config(self, store: InMemoryConfigStore) -> None:
        """Test getting a config that doesn't exist."""
        result = await store.get_config("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_config(self, store: InMemoryConfigStore) -> None:
        """Test deleting a config."""
        config = UserDatabaseConfig(database_url="postgresql://localhost/db")
        await store.save_config("user123", config)
        await store.delete_config("user123")
        result = await store.get_config("user123")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_config(self, store: InMemoryConfigStore) -> None:
        """Test deleting a config that doesn't exist (no error)."""
        # Should not raise
        await store.delete_config("nonexistent")

    @pytest.mark.asyncio
    async def test_has_config(self, store: InMemoryConfigStore) -> None:
        """Test checking if config exists."""
        config = UserDatabaseConfig(database_url="postgresql://localhost/db")
        assert await store.has_config("user123") is False
        await store.save_config("user123", config)
        assert await store.has_config("user123") is True

    @pytest.mark.asyncio
    async def test_list_users(self, store: InMemoryConfigStore) -> None:
        """Test listing all users with configs."""
        config = UserDatabaseConfig(database_url="postgresql://localhost/db")
        await store.save_config("user1", config)
        await store.save_config("user2", config)
        await store.save_config("user3", config)
        users = await store.list_users()
        assert len(users) == 3
        assert "user1" in users
        assert "user2" in users
        assert "user3" in users

    @pytest.mark.asyncio
    async def test_update_config(self, store: InMemoryConfigStore) -> None:
        """Test updating an existing config."""
        config1 = UserDatabaseConfig(
            database_url="postgresql://localhost/db1",
            database_name="db1",
        )
        config2 = UserDatabaseConfig(
            database_url="postgresql://localhost/db2",
            database_name="db2",
        )
        await store.save_config("user123", config1)
        await store.save_config("user123", config2)
        retrieved = await store.get_config("user123")
        assert retrieved is not None
        assert retrieved.database_name == "db2"


class TestFileConfigStore:
    """Tests for FileConfigStore class."""

    @pytest.fixture
    def temp_dir(self) -> Generator[Path, None, None]:
        """Create a temporary directory fixture."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def encryption_key(self) -> EncryptionKey:
        """Create an encryption key fixture."""
        return EncryptionKey.generate()

    @pytest.fixture
    def store(
        self, temp_dir: Path, encryption_key: EncryptionKey
    ) -> FileConfigStore:
        """Create a file store fixture."""
        return FileConfigStore(
            base_path=temp_dir,
            encryption_key=encryption_key,
        )

    @pytest.mark.asyncio
    async def test_save_and_get_config(self, store: FileConfigStore) -> None:
        """Test saving and retrieving a config."""
        config = UserDatabaseConfig(
            database_url="postgresql://localhost/db",
            database_name="test",
        )
        await store.save_config("user123", config)
        retrieved = await store.get_config("user123")
        assert retrieved is not None
        assert retrieved.database_url == config.database_url
        assert retrieved.database_name == config.database_name

    @pytest.mark.asyncio
    async def test_config_is_encrypted_on_disk(
        self, store: FileConfigStore, temp_dir: Path
    ) -> None:
        """Test that config is encrypted when stored."""
        config = UserDatabaseConfig(
            database_url="postgresql://secret:password@localhost/db",
        )
        await store.save_config("user123", config)

        # Find the encrypted config file (it uses hashed name)
        enc_files = list(temp_dir.glob("*.enc"))
        assert len(enc_files) >= 1

        # Read the raw file (excluding index file)
        config_files = [f for f in enc_files if not f.name.startswith(".")]
        assert len(config_files) >= 1

        with open(config_files[0]) as f:
            raw_content = f.read()

        # The password should not be visible in plaintext
        assert "password" not in raw_content

    @pytest.mark.asyncio
    async def test_get_nonexistent_config(self, store: FileConfigStore) -> None:
        """Test getting a config that doesn't exist."""
        result = await store.get_config("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_config(self, store: FileConfigStore) -> None:
        """Test deleting a config."""
        config = UserDatabaseConfig(database_url="postgresql://localhost/db")
        await store.save_config("user123", config)
        await store.delete_config("user123")
        result = await store.get_config("user123")
        assert result is None

    @pytest.mark.asyncio
    async def test_has_config(self, store: FileConfigStore) -> None:
        """Test checking if config exists."""
        config = UserDatabaseConfig(database_url="postgresql://localhost/db")
        assert await store.has_config("user123") is False
        await store.save_config("user123", config)
        assert await store.has_config("user123") is True

    @pytest.mark.asyncio
    async def test_list_users(
        self, store: FileConfigStore
    ) -> None:
        """Test listing all users with configs."""
        config = UserDatabaseConfig(database_url="postgresql://localhost/db")
        await store.save_config("user1", config)
        await store.save_config("user2", config)
        users = await store.list_users()
        assert len(users) == 2
        assert "user1" in users
        assert "user2" in users

    @pytest.mark.asyncio
    async def test_creates_storage_directory(
        self, encryption_key: EncryptionKey
    ) -> None:
        """Test that storage directory is created if missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "subdir" / "configs"
            store = FileConfigStore(
                base_path=storage_path,
                encryption_key=encryption_key,
            )
            config = UserDatabaseConfig(database_url="postgresql://localhost/db")
            await store.save_config("user123", config)
            assert storage_path.exists()

    @pytest.mark.asyncio
    async def test_different_keys_cannot_decrypt(
        self, temp_dir: Path
    ) -> None:
        """Test that different keys cannot decrypt configs."""
        key1 = EncryptionKey.generate()
        key2 = EncryptionKey.generate()

        store1 = FileConfigStore(base_path=temp_dir, encryption_key=key1)
        store2 = FileConfigStore(base_path=temp_dir, encryption_key=key2)

        config = UserDatabaseConfig(database_url="postgresql://localhost/db")
        await store1.save_config("user123", config)

        # Store2 with different key should not be able to decrypt
        # Implementation returns None on decryption failure
        result = await store2.get_config("user123")
        assert result is None


class TestUserConfigStoreInterface:
    """Tests for UserConfigStore abstract interface."""

    def test_is_abstract(self) -> None:
        """Test that UserConfigStore cannot be instantiated directly."""
        with pytest.raises(TypeError):
            UserConfigStore()  # type: ignore[abstract]
