"""Environment setup for behave tests."""
import os
from pathlib import Path


def before_all(context):
    """Set up test environment before all tests."""
    # Set default test database
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["API_HOST"] = "127.0.0.1"
    os.environ["API_PORT"] = "8000"
    os.environ["LOG_LEVEL"] = "WARNING"

    # Get project root
    project_root = Path(__file__).parent.parent.parent
    context.project_root = project_root


def before_scenario(context, scenario):
    """Set up each scenario."""
    # Reset environment for each scenario
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"


def after_scenario(context, scenario):
    """Clean up after each scenario."""
    # Close any open connections
    if hasattr(context, "client"):
        pass  # TestClient handles cleanup


def after_all(context):
    """Clean up after all tests."""
    pass
