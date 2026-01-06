"""GraphQL schema generation using Strawberry."""
from typing import Any, Dict, List, Optional

import strawberry
from sqlalchemy.orm import Session
from strawberry.fastapi import GraphQLRouter

from graphsql.config import settings
from graphsql.database import db_manager, get_db, serialize_model


def create_graphql_schema() -> GraphQLRouter:
    """Create a Strawberry GraphQL schema from reflected database tables.

    Returns:
        Configured ``GraphQLRouter`` mounted at ``/graphql`` containing queries
        and mutations for each table discovered via SQLAlchemy automap.

    Examples:
        Attach the router to a FastAPI app:

        >>> from fastapi import FastAPI
        >>> from graphsql.graphql_schema import create_graphql_schema
        >>> app = FastAPI()
        >>> app.include_router(create_graphql_schema())  # doctest: +SKIP
    """

    # Dynamically create types for each table
    table_types: Dict[str, Any] = {}

    for table_name in db_manager.list_tables():
        model = db_manager.get_model(table_name)
        if not model:
            continue

        # Create Strawberry type dynamically
        fields = {}
        for column in model.__table__.columns:
            python_type = column.type.python_type

            # Map Python types to Strawberry types
            if python_type is str:
                field_type = Optional[str]
            elif python_type is int:
                field_type = Optional[int]
            elif python_type is float:
                field_type = Optional[float]
            elif python_type is bool:
                field_type = Optional[bool]
            else:
                field_type = Optional[str]  # Fallback

            fields[column.name] = field_type

        # Create the Strawberry type
        table_type = strawberry.type(
            type(
                f"{table_name.capitalize()}Type",
                (),
                {
                    "__annotations__": fields,
                    **{k: None for k in fields.keys()}
                }
            )
        )

        table_types[table_name] = table_type

    # Create Query class
    query_fields = {}

    for table_name, table_type in table_types.items():
        model = db_manager.get_model(table_name)
        pk_column = db_manager.get_primary_key_column(table_name)

        # Single record query
        def make_single_resolver(model_class: Any, pk_col: str, tbl_name: str) -> Any:
            def resolver(id: int, info: Any) -> Optional[Any]:
                db: Session = next(get_db())
                try:
                    record = db.query(model_class).filter(
                        getattr(model_class, pk_col) == id
                    ).first()

                    if not record:
                        return None

                    data = serialize_model(record)
                    # Create instance of the type
                    type_class = table_types[tbl_name]
                    instance = type_class.__class__.__new__(type_class.__class__)
                    for key, value in data.items():
                        setattr(instance, key, value)
                    return instance
                finally:
                    db.close()

            return resolver

        # List query
        def make_list_resolver(model_class: Any, tbl_name: str) -> Any:
            def resolver(
                limit: int = settings.default_page_size,
                offset: int = 0,
                info: Any = None
            ) -> List[Any]:
                db: Session = next(get_db())
                try:
                    records = db.query(model_class).offset(offset).limit(
                        min(limit, settings.max_page_size)
                    ).all()

                    result = []
                    for record in records:
                        data = serialize_model(record)
                        type_class = table_types[tbl_name]
                        instance = type_class.__class__.__new__(type_class.__class__)
                        for key, value in data.items():
                            setattr(instance, key, value)
                        result.append(instance)
                    return result
                finally:
                    db.close()

            return resolver

        if pk_column:
            query_fields[table_name] = strawberry.field(
                resolver=make_single_resolver(model, pk_column, table_name)
            )

        query_fields[f"all_{table_name}"] = strawberry.field(
            resolver=make_list_resolver(model, table_name)
        )

    # Create the Query type
    @strawberry.type
    class Query:
        pass

    # Add fields to Query
    for field_name, field_obj in query_fields.items():
        setattr(Query, field_name, field_obj)

    # Create Mutation class
    mutation_fields = {}

    for table_name, table_type in table_types.items():
        model = db_manager.get_model(table_name)

        # Create mutation input type
        input_fields = {}
        for column in model.__table__.columns:
            if not column.primary_key and not column.autoincrement:
                python_type = column.type.python_type

                if python_type is str:
                    field_type = Optional[str]
                elif python_type is int:
                    field_type = Optional[int]
                elif python_type is float:
                    field_type = Optional[float]
                elif python_type is bool:
                    field_type = Optional[bool]
                else:
                    field_type = Optional[str]

                input_fields[column.name] = field_type

        # Create Input type
        strawberry.input(
            type(
                f"{table_name.capitalize()}Input",
                (),
                {
                    "__annotations__": input_fields,
                    **{k: None for k in input_fields.keys()}
                }
            )
        )

        # Create mutation
        def make_create_mutation(model_class: Any, tbl_name: str) -> Any:
            def mutation(data: Any, info: Any) -> Any:
                db: Session = next(get_db())
                try:
                    # Convert Strawberry input to dict
                    data_dict = {
                        k: v for k, v in vars(data).items()
                        if v is not None and not k.startswith('_')
                    }

                    new_record = model_class(**data_dict)
                    db.add(new_record)
                    db.commit()
                    db.refresh(new_record)

                    result_data = serialize_model(new_record)
                    type_class = table_types[tbl_name]
                    instance = type_class.__class__.__new__(type_class.__class__)
                    for key, value in result_data.items():
                        setattr(instance, key, value)
                    return instance
                except Exception as e:
                    db.rollback()
                    raise e
                finally:
                    db.close()

            return mutation

        mutation_fields[f"create_{table_name}"] = strawberry.mutation(
            resolver=make_create_mutation(model, table_name)
        )

    # Create Mutation type
    @strawberry.type
    class Mutation:
        pass

    # Add fields to Mutation
    for field_name, field_obj in mutation_fields.items():
        setattr(Mutation, field_name, field_obj)

    # Create schema
    schema = strawberry.Schema(query=Query, mutation=Mutation)

    return GraphQLRouter(schema, path="/graphql")
