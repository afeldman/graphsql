"""Database connection and model management."""

from typing import Any

from loguru import logger
from sqlalchemy import MetaData, Table, create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from graphsql.config import settings


class DatabaseManager:
    """Manage database connections and automatic model mapping.

    Examples:
        Initialize once and reuse the global instance:

        >>> from graphsql.database import db_manager
        >>> db_manager.list_tables()  # doctest: +SKIP
        ['users', 'orders']
    """

    def __init__(self) -> None:
        """Initialize the database engine, session factory, and models."""
        # SQLite specific configuration
        if settings.is_sqlite:
            self.engine = create_engine(
                settings.database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=settings.log_level == "DEBUG",
            )
        else:
            self.engine = create_engine(
                settings.database_url,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                echo=settings.log_level == "DEBUG",
            )

        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        # Automatic model mapping
        self.Base = automap_base()
        try:
            self.Base.prepare(autoload_with=self.engine, reflect=True)
            self._models: dict[str, Any] = {
                name: getattr(self.Base.classes, name) for name in self.Base.classes.keys()
            }
        except Exception as e:
            logger.warning("Could not prepare database models: {}", e)
            self._models = {}

        self.metadata = MetaData()
        self.metadata.reflect(bind=self.engine)

    def get_session(self) -> Session:
        """Create a new SQLAlchemy session.

        Returns:
            Session: A database session bound to the configured engine.

        Examples:
            >>> from graphsql.database import db_manager
            >>> with db_manager.get_session() as session:  # doctest: +SKIP
            ...     session.execute("SELECT 1")
        """
        return self.SessionLocal()

    def get_model(self, table_name: str) -> type[Any] | None:
        """Return the mapped SQLAlchemy model for a table.

        Args:
            table_name: Name of the table to resolve.

        Returns:
            The mapped model class, or ``None`` when the table is unknown.
        """
        return self._models.get(table_name)

    def get_table(self, table_name: str) -> Table | None:
        """Return the reflected SQLAlchemy ``Table`` for a name."""
        return self.metadata.tables.get(table_name)

    def list_tables(self) -> list[str]:
        """List all available table names.

        Returns:
            All reflected table names known to the automapper.
        """
        return list(self._models.keys())

    def get_table_info(self, table_name: str) -> dict[str, Any] | None:
        """Return column metadata for a table.

        Args:
            table_name: Table name to inspect.

        Returns:
            Dictionary with column definitions and primary keys, or ``None`` if
            the table does not exist.

        Examples:
            >>> db_manager.get_table_info("users")  # doctest: +SKIP
            {'name': 'users', 'columns': [...], 'primary_keys': ['id']}
        """
        table = self.get_table(table_name)
        if not table:
            return None

        columns = []
        for column in table.columns:
            columns.append(
                {
                    "name": column.name,
                    "type": str(column.type),
                    "nullable": column.nullable,
                    "primary_key": column.primary_key,
                    "default": str(column.default) if column.default else None,
                }
            )

        return {
            "name": table_name,
            "columns": columns,
            "primary_keys": [col.name for col in table.primary_key],
        }

    def get_primary_key_column(self, table_name: str) -> str | None:
        """Return the first primary key column name for a table."""
        model = self.get_model(table_name)
        if not model:
            return None

        pk_columns = list(model.__table__.primary_key.columns)
        return pk_columns[0].name if pk_columns else None


# Global database manager instance
db_manager = DatabaseManager()


def get_db() -> Session:
    """FastAPI dependency that yields a database session."""
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db.close()


def serialize_model(obj: Any) -> dict[str, Any]:
    """Serialize a SQLAlchemy model instance.

    Args:
        obj: ORM instance to serialize.

    Returns:
        Dictionary representation with ISO date strings and decoded bytes.

    Examples:
        >>> serialize_model(record)  # doctest: +SKIP
        {'id': 1, 'created_at': '2024-01-01T12:00:00', 'name': 'Alice'}
    """
    from datetime import date, datetime
    from decimal import Decimal

    result = {}
    for column in obj.__table__.columns:
        value = getattr(obj, column.name)

        # Handle special types
        if isinstance(value, (datetime, date)):
            result[column.name] = value.isoformat()
        elif isinstance(value, Decimal):
            result[column.name] = float(value)
        elif isinstance(value, bytes):
            result[column.name] = value.decode("utf-8", errors="ignore")
        else:
            result[column.name] = value

    return result
