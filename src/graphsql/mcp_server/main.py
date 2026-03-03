"""MCP Server main module.

This module implements the MCP server using the official MCP Python SDK.
It registers tools for database access and handles MCP protocol messages.

Example:
    Start the server::

        python -m graphsql.mcp_server.main

    Or with environment variables::

        DATABASE_URL=postgresql://user:pass@localhost/db python -m graphsql.mcp_server.main
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    TextContent,
    Tool,
)

from graphsql.mcp_server.config import MCPServerConfig, get_config
from graphsql.mcp_server.db import close_engine, get_engine, test_connection
from graphsql.mcp_server.engine import get_graphsql_engine
from graphsql.mcp_server.tools import TOOL_DEFINITIONS, MCPTools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


def create_mcp_server(config: MCPServerConfig | None = None) -> Server:
    """Create and configure the MCP server.

    Args:
        config: Server configuration. Uses global config if None.

    Returns:
        Configured MCP Server instance.
    """
    if config is None:
        config = get_config()

    # Create MCP server
    server = Server(config.server_name)

    # Initialize database and GraphSQL engine
    logger.info(f"Initializing MCP server: {config.server_name}")
    engine = get_engine(config)

    if not test_connection(engine):
        logger.error("Failed to connect to database")
        raise RuntimeError("Database connection failed")

    graphsql_engine = get_graphsql_engine(engine)
    tools = MCPTools(graphsql_engine)

    logger.info(
        f"Database connected. Found {len(graphsql_engine.introspect_schema().tables)} tables"
    )

    # Register tool handlers
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """Return list of available tools.

        Returns:
            List of Tool definitions.
        """
        return [
            Tool(
                name=str(tool["name"]),
                description=str(tool["description"]),
                inputSchema=tool["inputSchema"],  # type: ignore[arg-type]
            )
            for tool in TOOL_DEFINITIONS
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle tool invocation.

        Args:
            name: Tool name to invoke.
            arguments: Tool arguments.

        Returns:
            List of TextContent with tool results.
        """
        logger.info(f"Tool called: {name}")

        try:
            if name == "sql_query":
                sql_result = tools.sql_query(arguments.get("query", ""))
                return [
                    TextContent(type="text", text=json.dumps(sql_result.model_dump(), indent=2))
                ]

            elif name == "graphql_query":
                gql_result = tools.graphql_query(
                    arguments.get("query", ""),
                    arguments.get("variables"),
                )
                return [
                    TextContent(type="text", text=json.dumps(gql_result.model_dump(), indent=2))
                ]

            elif name == "schema_introspect":
                schema_result = tools.schema_introspect(arguments.get("table_name"))
                return [
                    TextContent(type="text", text=json.dumps(schema_result.model_dump(), indent=2))
                ]

            elif name == "health_check":
                health_result = tools.health_check()
                return [
                    TextContent(type="text", text=json.dumps(health_result.model_dump(), indent=2))
                ]

            else:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({"error": f"Unknown tool: {name}"}),
                    )
                ]

        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return [
                TextContent(
                    type="text",
                    text=json.dumps({"error": str(e), "success": False}),
                )
            ]

    return server


async def run_server() -> None:
    """Run the MCP server with stdio transport.

    This function starts the MCP server and handles the stdio transport
    for communication with MCP clients.
    """
    config = get_config()
    logger.info(f"Starting MCP server: {config.server_name} v{config.server_version}")
    logger.info(f"Read-only mode: {config.read_only}")
    logger.info(f"Max rows: {config.max_rows}")
    logger.info(f"Query timeout: {config.query_timeout}s")

    server = create_mcp_server(config)

    try:
        async with stdio_server() as (read_stream, write_stream):
            logger.info("MCP server running on stdio")
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
    finally:
        logger.info("Shutting down MCP server")
        close_engine()


def main() -> None:
    """Entry point for the MCP server.

    This function is called when running the server as a module or
    via the console script entry point.
    """
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logger.info("Server interrupted")
    except Exception as e:
        logger.error(f"Server failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
