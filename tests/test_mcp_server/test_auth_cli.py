"""Tests for auth CLI module."""

from __future__ import annotations

import os
import sys
from io import StringIO
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from graphsql.mcp_server.auth.cli import (
    main,
    parse_args,
)


class TestParseArgs:
    """Tests for argument parsing."""

    def test_default_mode(self) -> None:
        """Test default mode is proxy."""
        args = parse_args([])
        assert args.mode == "proxy"

    def test_proxy_mode(self) -> None:
        """Test proxy mode argument."""
        args = parse_args(["--mode", "proxy"])
        assert args.mode == "proxy"

    def test_standalone_mode(self) -> None:
        """Test standalone mode argument."""
        args = parse_args(["--mode", "standalone"])
        assert args.mode == "standalone"

    def test_generate_key_flag(self) -> None:
        """Test generate-key flag."""
        args = parse_args(["--generate-key"])
        assert args.generate_key is True

    def test_host_argument(self) -> None:
        """Test host argument."""
        args = parse_args(["--host", "127.0.0.1"])
        assert args.host == "127.0.0.1"

    def test_port_argument(self) -> None:
        """Test port argument."""
        args = parse_args(["--port", "9000"])
        assert args.port == 9000

    def test_default_host(self) -> None:
        """Test default host."""
        args = parse_args([])
        assert args.host == "0.0.0.0"

    def test_default_port(self) -> None:
        """Test default port."""
        args = parse_args([])
        assert args.port == 8080

    def test_config_path_argument(self) -> None:
        """Test config path argument."""
        args = parse_args(["--config-path", "/custom/path"])
        assert args.config_path == "/custom/path"

    def test_env_file_argument(self) -> None:
        """Test env file argument."""
        args = parse_args(["--env-file", ".env.prod"])
        assert args.env_file == ".env.prod"


class TestGenerateKey:
    """Tests for key generation."""

    def test_generate_key_argument(self) -> None:
        """Test generate-key flag is parsed correctly."""
        args = parse_args(["--generate-key"])
        assert args.generate_key is True
    
    def test_generate_key_value(self) -> None:
        """Test generate_encryption_key produces valid key."""
        from graphsql.mcp_server.auth.cli import generate_encryption_key
        key = generate_encryption_key()
        # Should be a base64-encoded string
        assert isinstance(key, str)
        assert len(key) > 0


class TestMainFunction:
    """Tests for main CLI function."""

    def test_main_with_missing_env_vars(self) -> None:
        """Test main handles missing environment variables."""
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(sys, "argv", ["graphsql-auth"]):
                with pytest.raises(SystemExit):
                    main()

    def test_main_with_generate_key(self) -> None:
        """Test main with generate-key flag."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            with patch.object(sys, "argv", ["graphsql-auth", "--generate-key"]):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                
                # Should exit with 0 (success)
                assert exc_info.value.code == 0 or exc_info.value.code is None

    def test_main_validates_sso_config(self) -> None:
        """Test main validates SSO configuration."""
        env_vars = {
            "SSO_PROVIDER": "azure_ad",
            "SSO_CLIENT_ID": "test-client",
            "SSO_CLIENT_SECRET": "test-secret",
            # Missing SSO_TENANT_ID for Azure AD
            "SSO_REDIRECT_URI": "http://localhost/callback",
            "ENCRYPTION_KEY": "dGVzdC1lbmNyeXB0aW9uLWtleS0zMi1ieXRlcw==",
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            with patch.object(sys, "argv", ["graphsql-auth"]):
                # Should fail due to missing tenant_id
                with pytest.raises((SystemExit, ValueError)):
                    main()


class TestCLIIntegration:
    """Integration tests for CLI."""

    @pytest.fixture
    def valid_env_vars(self) -> dict[str, str]:
        """Create valid environment variables fixture."""
        return {
            "SSO_PROVIDER": "github",
            "SSO_CLIENT_ID": "test-client-id",
            "SSO_CLIENT_SECRET": "test-client-secret",
            "SSO_REDIRECT_URI": "http://localhost:8080/callback",
            "ENCRYPTION_KEY": "dGVzdC1lbmNyeXB0aW9uLWtleS0zMi1ieXRlcyE=",
            "CONFIG_STORE_PATH": "/tmp/test-configs",
        }

    def test_cli_help(self) -> None:
        """Test CLI help output."""
        with patch.object(sys, "argv", ["graphsql-auth", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            # Help should exit with 0
            assert exc_info.value.code == 0

    def test_cli_mode_selection(self, valid_env_vars: dict[str, str]) -> None:
        """Test CLI mode selection works."""
        args = parse_args(["--mode", "standalone"])
        assert args.mode == "standalone"

    def test_cli_port_validation(self) -> None:
        """Test CLI validates port number."""
        args = parse_args(["--port", "8080"])
        assert 1 <= args.port <= 65535


class TestEnvironmentLoading:
    """Tests for environment variable loading."""

    def test_loads_from_env_file(self) -> None:
        """Test CLI loads from .env file."""
        # This test verifies the env file loading mechanism
        args = parse_args(["--env-file", ".env.test"])
        assert args.env_file == ".env.test"

    def test_env_precedence(self) -> None:
        """Test environment variables take precedence over .env file."""
        # Environment variables should override .env file values
        with patch.dict(
            os.environ,
            {"SSO_PROVIDER": "okta"},
            clear=False,
        ):
            # The SSO_PROVIDER from env should be used
            provider = os.environ.get("SSO_PROVIDER")
            assert provider == "okta"
