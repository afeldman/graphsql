"""REST API routes."""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi import Query as QueryParam
from pydantic import BaseModel
from sqlalchemy.orm import Session

from graphsql.config import settings
from graphsql.database import db_manager, get_db, serialize_model
from graphsql.rate_limit import limiter
from graphsql.cache import cache_get, cache_set

router = APIRouter(prefix="/api", tags=["REST API"])


class PaginatedResponse(BaseModel):
    """Paginated response model."""
    data: List[Dict[str, Any]]
    total: int
    limit: int
    offset: int


@router.get("/tables", response_model=Dict[str, List[str]])
@limiter.limit(settings.rate_limit_tables)
async def list_tables(request: Request) -> Dict[str, List[str]]:
    """List all available tables in the database.

    Returns:
        Mapping with a single ``tables`` key containing all table names.

    Examples:
        >>> await list_tables()  # doctest: +SKIP
        {'tables': ['users', 'orders']}
    """
    cache_key = "tables:list"
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

    tables = {"tables": db_manager.list_tables()}
    await cache_set(cache_key, tables)
    return tables


@router.get("/tables/{table_name}/info")
@limiter.limit(settings.rate_limit_tables)
async def get_table_info(request: Request, table_name: str) -> Dict[str, Any]:
    """Return reflected metadata for a specific table.

    Args:
        table_name: Target table name.

    Returns:
        Columns, defaults, and primary key information for the table.

    Raises:
        HTTPException: If the table does not exist.
    """
    cache_key = f"tables:info:{table_name}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

    info = db_manager.get_table_info(table_name)
    if not info:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")

    await cache_set(cache_key, info)
    return info


@router.get("/{table_name}", response_model=PaginatedResponse)
@limiter.limit(settings.rate_limit_tables)
async def get_all_records(
    request: Request,
    table_name: str,
    offset: int = QueryParam(0, ge=0),
    limit: int = QueryParam(settings.default_page_size, ge=1),
    db: Session = Depends(get_db)
) -> PaginatedResponse:
    """Get paginated records from a table.

    Args:
        table_name: Name of the table to query.
        offset: Number of rows to skip.
        limit: Maximum number of rows to return.
        db: Database session dependency.

    Returns:
        PaginatedResponse containing records and pagination metadata.

    Raises:
        HTTPException: If the table does not exist.

    Examples:
        A simple GET with pagination parameters::

            curl "http://localhost:8000/api/users?limit=20&offset=0"
    """
    model = db_manager.get_model(table_name)
    if not model:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")

    # Enforce max page size defensively
    safe_limit = min(limit, settings.max_page_size)

    # Get total count
    total = db.query(model).count()

    # Get paginated records
    records = db.query(model).offset(offset).limit(safe_limit).all()

    return PaginatedResponse(
        data=[serialize_model(record) for record in records],
        total=total,
        limit=safe_limit,
        offset=offset
    )


@router.get("/{table_name}/{record_id}")
async def get_record(
    table_name: str,
    record_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get a specific record by ID.

    Args:
        table_name: Name of the table to query.
        record_id: Primary key value of the record.
        db: Database session dependency.

    Returns:
        Serialized record.

    Raises:
        HTTPException: If the table or record does not exist, or if no primary
        key is defined.

    Examples:
        >>> await get_record("users", 1)  # doctest: +SKIP
        {'id': 1, 'name': 'Alice'}
    """
    model = db_manager.get_model(table_name)
    if not model:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")

    pk_column = db_manager.get_primary_key_column(table_name)
    if not pk_column:
        raise HTTPException(status_code=400, detail="Table has no primary key")

    record = db.query(model).filter(getattr(model, pk_column) == record_id).first()

    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    return serialize_model(record)


@router.post("/{table_name}", status_code=201)
async def create_record(
    table_name: str,
    data: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Create a new record in the table.

    Args:
        table_name: Name of the table to insert into.
        data: Column values for the new record.
        db: Database session dependency.

    Returns:
        Serialized representation of the created record.

    Raises:
        HTTPException: If the table is unknown or the insert fails.

    Examples:
        Create a record via curl::

            curl -X POST http://localhost:8000/api/users \
                 -H "Content-Type: application/json" \
                 -d '{"name": "Alice"}'
    """
    model = db_manager.get_model(table_name)
    if not model:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")

    try:
        new_record = model(**data)
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        return serialize_model(new_record)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{table_name}/{record_id}")
async def update_record(
    table_name: str,
    record_id: int,
    data: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Update an existing record.

    Args:
        table_name: Name of the table containing the record.
        record_id: Primary key value of the record to update.
        data: Fields to overwrite.
        db: Database session dependency.

    Returns:
        Serialized representation of the updated record.

    Raises:
        HTTPException: If the table or record does not exist, the table has no
        primary key, or the update fails.

    Examples:
        Update selected fields via curl::

            curl -X PUT http://localhost:8000/api/users/1 \
                 -H "Content-Type: application/json" \
                 -d '{"name": "Bob"}'
    """
    model = db_manager.get_model(table_name)
    if not model:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")

    pk_column = db_manager.get_primary_key_column(table_name)
    if not pk_column:
        raise HTTPException(status_code=400, detail="Table has no primary key")

    record = db.query(model).filter(getattr(model, pk_column) == record_id).first()

    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    try:
        for key, value in data.items():
            if hasattr(record, key):
                setattr(record, key, value)
        db.commit()
        db.refresh(record)
        return serialize_model(record)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{table_name}/{record_id}")
async def patch_record(
    table_name: str,
    record_id: int,
    data: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Partially update an existing record."""
    return await update_record(table_name, record_id, data, db)


@router.delete("/{table_name}/{record_id}", status_code=204)
async def delete_record(
    table_name: str,
    record_id: int,
    db: Session = Depends(get_db)
) -> None:
    """Delete a record by primary key.

    Args:
        table_name: Name of the table.
        record_id: Primary key value to delete.
        db: Database session dependency.

    Raises:
        HTTPException: If the table or record does not exist, the table has no
        primary key, or the delete fails.

    Examples:
        Delete a record via curl::

            curl -X DELETE http://localhost:8000/api/users/1
    """
    model = db_manager.get_model(table_name)
    if not model:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")

    pk_column = db_manager.get_primary_key_column(table_name)
    if not pk_column:
        raise HTTPException(status_code=400, detail="Table has no primary key")

    record = db.query(model).filter(getattr(model, pk_column) == record_id).first()

    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    try:
        db.delete(record)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
