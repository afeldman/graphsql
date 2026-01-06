"""Command Line Interface powered by Typer."""

import json
import os
import sys
import webbrowser
from pathlib import Path

import typer
import uvicorn
from rich.console import Console
from rich.table import Table

from graphsql import __version__
from graphsql.config import settings
from graphsql.database import DatabaseManager

app = typer.Typer(
    name="graphsql",
    help="🚀 Automatic REST and GraphQL API for any SQL database",
    rich_markup_mode="rich",
)
console = Console()


@app.command()
def server(
    host: str = typer.Option(
        settings.api_host,
        "--host",
        "-h",
        help="Bind host address",
    ),
    port: int = typer.Option(
        settings.api_port,
        "--port",
        "-p",
        help="Bind port number",
    ),
    reload: bool = typer.Option(
        settings.api_reload,
        "--reload/--no-reload",
        help="Enable auto-reload on file changes (dev mode)",
    ),
    log_level: str = typer.Option(
        settings.log_level.upper(),
        "--log-level",
        "-l",
        help="Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    ),
    database_url: str | None = typer.Option(
        None,
        "--database-url",
        "-d",
        help="Override DATABASE_URL environment variable",
    ),
) -> None:
    """Start the GraphQL/REST API server.

    Examples:
        Start with defaults:
            graphsql server

        Start with custom host/port:
            graphsql server --host 127.0.0.1 --port 9000

        Enable debug logging:
            graphsql server --log-level DEBUG
    """
    # Override environment if provided
    if database_url:
        os.environ["DATABASE_URL"] = database_url

    console.print("🚀 Starting GraphSQL API server...")
    console.print(f"   Host: [bold cyan]{host}[/bold cyan]")
    console.print(f"   Port: [bold cyan]{port}[/bold cyan]")
    console.print(f"   Reload: [bold cyan]{'enabled' if reload else 'disabled'}[/bold cyan]")
    console.print(f"   Log Level: [bold cyan]{log_level}[/bold cyan]")
    console.print()

    try:
        uvicorn.run(
            "graphsql.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level=log_level.lower(),
        )
    except KeyboardInterrupt:
        console.print("\n⏹️  Server stopped by user", style="yellow")
        sys.exit(0)
    except Exception as e:
        console.print(f"❌ Server error: {e}", style="bold red")
        sys.exit(1)


@app.command()
def inspect(
    database_url: str | None = typer.Option(
        None,
        "--database-url",
        "-d",
        envvar="DATABASE_URL",
        help="Database connection URL",
    ),
) -> None:
    """Inspect and display database structure.

    Shows all tables, columns, types, and primary keys.
    """
    if not database_url:
        database_url = settings.database_url

    with console.status("[bold green]Connecting to database..."):
        try:
            # Temporary database manager
            os.environ["DATABASE_URL"] = database_url
            db_manager = DatabaseManager()
            tables = db_manager.list_tables()

            console.print()
            console.print("✅ Connected successfully!", style="bold green")
            console.print(f"Found [bold]{len(tables)}[/bold] tables\n")

            for table_name in tables:
                info = db_manager.get_table_info(table_name)
                if not info:
                    continue

                table = Table(title=f"📊 {table_name}")
                table.add_column("Column", style="cyan")
                table.add_column("Type", style="magenta")
                table.add_column("Nullable", style="yellow")
                table.add_column("PK", style="green")

                for col in info["columns"]:
                    table.add_row(
                        col["name"],
                        col["type"],
                        "✓" if col["nullable"] else "✗",
                        "✓" if col["primary_key"] else "",
                    )

                console.print(table)
                console.print()

        except Exception as e:
            console.print(f"❌ Error: {e}", style="bold red")
            sys.exit(1)


@app.command()
def init(
    output: str = typer.Option(
        ".env",
        "--output",
        "-o",
        help="Output file path",
    ),
) -> None:
    """Initialize a new GraphSQL project with .env template."""
    env_content = """# GraphSQL Configuration

# Database Connection
DATABASE_URL=postgresql://user:password@localhost:5432/mydb
# Examples:
# DATABASE_URL=sqlite:///./database.db
# DATABASE_URL=mysql+pymysql://user:password@localhost:3306/mydb
# DATABASE_URL=hana+hdbcli://USER:PASSWORD@host:39015/?encrypt=true
# DATABASE_URL=redshift+psycopg2://USER:PASSWORD@cluster.redshift.amazonaws.com:5439/DB
# DATABASE_URL=snowflake://USER:PASSWORD@account/db/schema?warehouse=WH

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# CORS (comma separated origins or *)
CORS_ORIGINS=*

# Security
ENABLE_AUTH=false
API_KEY=change-me-in-production

# Pagination
DEFAULT_PAGE_SIZE=50
MAX_PAGE_SIZE=1000

# Logging
LOG_LEVEL=INFO
"""

    output_path = Path(output)

    if output_path.exists():
        console.print(f"⚠️  File [bold]{output}[/bold] already exists.")
        if typer.confirm("Overwrite?"):
            output_path.write_text(env_content)
            console.print(f"✅ Updated {output}", style="bold green")
        else:
            console.print("Aborted.")
            return
    else:
        output_path.write_text(env_content)
        console.print(f"✅ Created {output}", style="bold green")

    console.print()
    console.print("📝 Next steps:")
    console.print("1. Edit [bold].env[/bold] and set your [bold]DATABASE_URL[/bold]")
    console.print("2. Run: [bold cyan]graphsql server[/bold cyan]")
    console.print("3. Open: [bold cyan]http://localhost:8000/docs[/bold cyan]")


@app.command()
def export_openapi(
    output: str = typer.Option(
        "openapi.json",
        "--output",
        "-o",
        help="Output file path",
    ),
) -> None:
    """Export OpenAPI/Swagger schema to a JSON file."""
    from graphsql.main import app

    with console.status("[bold green]Exporting OpenAPI schema..."):
        try:
            schema = app.openapi()

            with open(output, "w") as f:
                json.dump(schema, f, indent=2)

            console.print(
                f"✅ OpenAPI schema exported to [bold]{output}[/bold]", style="bold green"
            )
        except Exception as e:
            console.print(f"❌ Error: {e}", style="bold red")
            sys.exit(1)


@app.callback(invoke_without_command=True)
def version_callback(
    ctx: typer.Context,
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit",
    ),
) -> None:
    """Show version if requested."""
    if version:
        console.print(f"GraphSQL [bold green]v{__version__}[/bold green]")
        ctx.exit()


@app.command()
def docs() -> None:
    """Open documentation in your browser."""
    url = "https://github.com/afeldman/graphsql#readme"
    console.print(f"Opening documentation: [bold cyan]{url}[/bold cyan]")
    webbrowser.open(url)


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
