"""Fixtures and configuration for pytest."""
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from graphsql.main import app


@pytest.fixture(scope="session")
def test_db() -> Generator:
    """Create an in-memory SQLite test database.

    Yields:
        A database URL string for testing.
    """
    db_url = "sqlite:///:memory:"
    yield db_url


@pytest.fixture(scope="function")
def db_session(test_db: str) -> Generator[Session, None, None]:
    """Create a database session for testing.

    Args:
        test_db: The test database URL.

    Yields:
        A SQLAlchemy session object.
    """
    engine = create_engine(test_db, connect_args={"check_same_thread": False})
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    session = session_local()
    yield session
    session.close()


@pytest.fixture
def client(monkeypatch, test_db: str) -> TestClient:
    """Create a FastAPI test client with test database.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
        test_db: The test database URL.

    Returns:
        A TestClient configured with the test database.
    """
    # Mock environment variables
    monkeypatch.setenv("DATABASE_URL", test_db)
    monkeypatch.setenv("API_HOST", "127.0.0.1")
    monkeypatch.setenv("API_PORT", "8000")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")

    # Return test client
    return TestClient(app)


@pytest.fixture
def sample_db(db_session: Session) -> Session:
    """Create a sample database with test tables.

    Args:
        db_session: Database session.

    Returns:
        Database session with sample data.
    """
    # Create users table
    db_session.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            age INTEGER
        )
    """)

    # Create posts table
    db_session.execute("""
        CREATE TABLE posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Insert sample data
    db_session.execute(
        "INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
        ("Alice", "alice@example.com", 30),
    )
    db_session.execute(
        "INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
        ("Bob", "bob@example.com", 25),
    )
    db_session.execute(
        "INSERT INTO posts (user_id, title, content) VALUES (?, ?, ?)",
        (1, "First Post", "This is Alice's first post"),
    )

    db_session.commit()
    return db_session
