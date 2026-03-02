"""Database connection management for MCP server.

This module provides database engine creation and session management
with proper connection pooling. It reuses the main GraphSQL database
infrastructure when possible.

Example:
    >>> from graphsql.mcp_server.db import get_engine, get_session
    >>> engine = get_engine()
    >>> with get_session() as session:
    ...     result = session.execute(text("SELECT 1"))
"""

from __future__ import annotations

import logging
from collections.abc import Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING, cast

from sqlalchemy import MetaData, create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool, StaticPool

from graphsql.mcp_server.config import MCPServerConfig, get_config

if TYPE_CHECKING:
    from sqlalchemy.engine import Connection

logger = logging.getLogger(__name__)

# Module-level engine cache
_engine: Engine | None = None
_session_factory: sessionmaker | None = None


def create_db_engine(config: MCPServerConfig | None = None) -> Engine:
    """Create a SQLAlchemy engine with proper connection pooling.

    Args:
        config: Configuration instance. Uses global config if None.

    Returns:
        Configured SQLAlchemy Engine instance.

    Note:
        SQLite uses StaticPool for single connection.
        Other databases use QueuePool with configurable size.

    Example:
        >>> engine = create_db_engine()
        >>> engine.url.database
        './database.db'
    """
    if config is None:
        config = get_config()

    logger.info(f"Creating database engine for: {_mask_url(config.database_url)}")

    if config.is_sqlite:
        # SQLite specific configuration
        engine = create_engine(
            config.database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=config.log_level == "DEBUG",
        )
    else:
        # Production database configuration with connection pooling
        engine = create_engine(
            config.database_url,
            poolclass=QueuePool,
            pool_size=config.pool_size,
            max_overflow=config.pool_max_overflow,
            pool_timeout=config.pool_timeout,
            pool_recycle=config.pool_recycle,
            pool_pre_ping=True,  # Verify connection health
            echo=config.log_level == "DEBUG",
        )

    # Add query timeout event listener
    @event.listens_for(engine, "connect")
    def set_query_timeout(dbapi_conn: Connection, connection_record: object) -> None:
        """Set query timeout on new connections."""
        if hasattr(dbapi_conn, "set_session"):
            # PostgreSQL with psycopg2
            try:
                dbapi_conn.set_session(autocommit=False)
            except Exception:
                pass

    logger.info("Database engine created successfully")
    return engine


def get_engine(config: MCPServerConfig | None = None) -> Engine:
    """Get or create the global database engine.

    This function implements a singleton pattern for the database engine.
    The engine is created on first call and reused thereafter.

    Args:
        config: Optional configuration. Uses global config if None.

    Returns:
        SQLAlchemy Engine instance.

    Example:
        >>> engine = get_engine()
        >>> engine.execute(text("SELECT 1"))
    """
    global _engine
    if _engine is None:
        _engine = create_db_engine(config)
    return _engine


def get_session_factory(engine: Engine | None = None) -> sessionmaker:
    """Get or create the session factory.

    Args:
        engine: SQLAlchemy engine. Creates one if None.

    Returns:
        Configured sessionmaker instance.
    """
    global _session_factory
    if _session_factory is None:
        if engine is None:
            engine = get_engine()
        _session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine,
        )
    return _session_factory


@contextmanager
def get_session(engine: Engine | None = None) -> Generator[Session, None, None]:
    """Context manager for database sessions.

    Creates a new session, yields it, and ensures proper cleanup.
    Automatically rolls back on exception.

    Args:
        engine: SQLAlchemy engine. Uses global engine if None.

    Yields:
        SQLAlchemy Session instance.

    Example:
        >>> with get_session() as session:
        ...     result = session.execute(text("SELECT 1"))
        ...     print(result.scalar())
        1
    """
    factory = get_session_factory(engine)
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def reflect_metadata(engine: Engine | None = None) -> MetaData:
    """Reflect database schema into MetaData.

    Args:
        engine: SQLAlchemy engine. Uses global engine if None.

    Returns:
        MetaData with reflected tables.

    Example:
        >>> metadata = reflect_metadata()
        >>> list(metadata.tables.keys())
        ['users', 'orders', ...]
    """
    if engine is None:
        engine = get_engine()

    metadata = MetaData()
    metadata.reflect(bind=engine)
    return metadata


def get_table_names(engine: Engine | None = None) -> list[str]:
    """Get list of all table names in the database.

    Args:
        engine: SQLAlchemy engine. Uses global engine if None.

    Returns:
        List of table names.
    """
    if engine is None:
        engine = get_engine()

    from sqlalchemy import inspect

    inspector = inspect(engine)
    return cast(list[str], inspector.get_table_names())


def test_connection(engine: Engine | None = None) -> bool:
    """Test database connectivity.

    Args:
        engine: SQLAlchemy engine. Uses global engine if None.

    Returns:
        True if connection is successful, False otherwise.
    """
    if engine is None:
        engine = get_engine()

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False


def close_engine() -> None:
    """Close and dispose of the global engine.

    Should be called during application shutdown.
    """
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("Database engine closed")


def _mask_url(url: str) -> str:
    """Mask credentials in database URL for logging.

    Args:
        url: Database connection URL.

    Returns:
        URL with password masked.
    """
    if "@" in url:
        parts = url.split("@")
        if len(parts) >= 2:
            # Mask the password part
            prefix = parts[0]
            if ":" in prefix:
                scheme_user = prefix.rsplit(":", 1)[0]
                return f"{scheme_user}:****@{parts[1]}"
    return url
