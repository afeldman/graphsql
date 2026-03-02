"""GraphSQL MCP Server - Model Context Protocol server for database access.

This module provides an MCP server that exposes database access via GraphQL
and SQL tools to LLM agents, using the GraphSQL library as the execution layer.

Example:
    Start the MCP server::

        $ python -m graphsql.mcp_server.main

    Or using the CLI::

        $ graphsql-mcp
"""

__version__ = "0.1.0"
__author__ = "Anton Feldmann"
__email__ = "anton.feldmann@gmail.com"

__all__ = ["__version__", "__author__", "__email__"]
