"""CLI for SSO-enabled MCP server.

This module provides the command-line interface for running the GraphSQL MCP server
with optional SSO authentication.

Usage:
    # Run with SSO proxy (default)
    graphsql-auth --mode proxy --port 8080

    # Run standalone without SSO
    graphsql-auth --mode standalone

    # Generate encryption key
    graphsql-auth --generate-key

Environment Variables:
    SSO_PROVIDER: SSO provider (azure_ad, okta, keycloak, auth0, google, github)
    SSO_CLIENT_ID: OAuth client ID
    SSO_CLIENT_SECRET: OAuth client secret
    SSO_TENANT_ID: Azure AD tenant ID
    SSO_DOMAIN: Provider domain (Okta, Auth0, Keycloak)
    SSO_REDIRECT_URI: OAuth redirect URI
    ENCRYPTION_KEY: Key for encrypting user configs
    CONFIG_STORE_PATH: Path for file-based config storage
    SESSION_TIMEOUT: Session timeout in seconds
"""

from __future__ import annotations

import argparse
import sys

from decouple import config
from loguru import logger

# Configure loguru - remove default handler and add custom one
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
    colorize=True,
)


def generate_encryption_key() -> str:
    """Generate a new encryption key.

    Returns:
        Base64-encoded Fernet key.
    """
    from graphsql.mcp_server.auth.user_config import EncryptionKey

    key = EncryptionKey.generate()
    return key.key.decode()


def run_standalone() -> None:
    """Run the MCP server in standalone mode (without SSO)."""
    from graphsql.mcp_server.main import main as run_mcp

    logger.info(
        "Starting MCP server in standalone mode",
        mode="standalone",
    )
    run_mcp()


def run_proxy(host: str, port: int) -> None:
    """Run the MCP server with SSO proxy.

    Args:
        host: Host to bind to.
        port: Port to bind to.
    """
    from graphsql.mcp_server.auth.proxy import AuthProxyConfig, run_auth_proxy
    from graphsql.mcp_server.auth.sso import SSOConfig, SSOProvider

    # Load SSO configuration from environment
    sso_provider = config("SSO_PROVIDER", default="azure_ad")
    try:
        provider = SSOProvider(sso_provider)
    except ValueError:
        logger.error(
            "Invalid SSO provider specified in configuration",
            sso_provider=sso_provider,
            valid_options=[p.value for p in SSOProvider],
        )
        sys.exit(1)

    client_id = config("SSO_CLIENT_ID", default="")
    client_secret = config("SSO_CLIENT_SECRET", default="")

    if not client_id or not client_secret:
        logger.error(
            "Missing required SSO credentials",
            has_client_id=bool(client_id),
            has_client_secret=bool(client_secret),
            hint="Set SSO_CLIENT_ID and SSO_CLIENT_SECRET environment variables",
        )
        sys.exit(1)

    # Build SSO config
    sso_config = SSOConfig(
        provider=provider,
        client_id=client_id,
        client_secret=client_secret,
        tenant_id=config("SSO_TENANT_ID", default=None),
        domain=config("SSO_DOMAIN", default=None),
        redirect_uri=config(
            "SSO_REDIRECT_URI",
            default=f"http://localhost:{port}/callback",
        ),
    )

    # Validate provider-specific requirements
    if provider == SSOProvider.AZURE_AD and not sso_config.tenant_id:
        logger.error(
            "Azure AD requires SSO_TENANT_ID environment variable",
            provider=provider.value,
        )
        sys.exit(1)

    if provider in (SSOProvider.OKTA, SSOProvider.AUTH0, SSOProvider.KEYCLOAK):
        if not sso_config.domain:
            logger.error(
                "SSO provider requires SSO_DOMAIN environment variable",
                provider=provider.value,
            )
            sys.exit(1)

    # Get encryption key
    encryption_key = config("ENCRYPTION_KEY", default="")
    if not encryption_key:
        logger.warning(
            "No ENCRYPTION_KEY found in environment",
            action="Generating temporary key",
            hint="Run 'graphsql-auth --generate-key' to create a persistent key",
        )
        encryption_key = generate_encryption_key()

    # Build proxy config
    proxy_config = AuthProxyConfig(
        sso=sso_config,
        encryption_key=encryption_key,
        config_store_path=config("CONFIG_STORE_PATH", default="./user_configs"),
        config_store_type=config("CONFIG_STORE_TYPE", default="file"),
        redis_url=config("REDIS_URL", default=None),
        session_timeout=config("SESSION_TIMEOUT", default=3600, cast=int),
        cleanup_interval=config("CLEANUP_INTERVAL", default=300, cast=int),
        host=host,
        port=port,
    )

    logger.info(
        "Starting GraphSQL MCP Auth Proxy",
        host=host,
        port=port,
        sso_provider=provider.value,
        redirect_uri=sso_config.redirect_uri,
        config_store_type=proxy_config.config_store_type,
        session_timeout=proxy_config.session_timeout,
        cleanup_interval=proxy_config.cleanup_interval,
    )

    run_auth_proxy(proxy_config)


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        args: Arguments to parse. If None, uses sys.argv.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="GraphSQL MCP Server with SSO Authentication",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start with SSO authentication
  graphsql-auth --mode proxy --port 8080

  # Start without SSO (standalone mode)
  graphsql-auth --mode standalone

  # Generate encryption key
  graphsql-auth --generate-key

Environment Variables (for proxy mode):
  SSO_PROVIDER       SSO provider (azure_ad, okta, keycloak, auth0, google, github)
  SSO_CLIENT_ID      OAuth client ID
  SSO_CLIENT_SECRET  OAuth client secret
  SSO_TENANT_ID      Azure AD tenant ID (Azure AD only)
  SSO_DOMAIN         Provider domain (Okta, Auth0, Keycloak)
  SSO_REDIRECT_URI   OAuth redirect URI
  ENCRYPTION_KEY     Key for encrypting user configs
  CONFIG_STORE_PATH  Path for file-based config storage
  SESSION_TIMEOUT    Session timeout in seconds (default: 3600)
        """,
    )

    parser.add_argument(
        "--mode",
        choices=["proxy", "standalone"],
        default="proxy",
        help="Run mode: proxy (with SSO) or standalone (direct MCP)",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to bind to (default: 8080)",
    )
    parser.add_argument(
        "--config-path",
        dest="config_path",
        default="./user_configs",
        help="Path for config storage (default: ./user_configs)",
    )
    parser.add_argument(
        "--env-file",
        dest="env_file",
        default=".env",
        help="Path to .env file (default: .env)",
    )
    parser.add_argument(
        "--generate-key",
        action="store_true",
        help="Generate a new encryption key and exit",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    return parser.parse_args(args)


def main() -> None:
    """Main entry point for SSO-enabled MCP server."""
    args = parse_args()

    if args.verbose:
        logger.remove()
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level="DEBUG",
            colorize=True,
        )
        logger.debug("Verbose logging enabled")

    if args.generate_key:
        key = generate_encryption_key()
        print(f"Generated encryption key:\n{key}")
        print("\nSet this in your environment:")
        print(f'export ENCRYPTION_KEY="{key}"')
        sys.exit(0)

    if args.mode == "standalone":
        run_standalone()
    else:
        run_proxy(args.host, args.port)


if __name__ == "__main__":
    main()
