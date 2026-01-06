"""Rate limiting configuration and middleware."""

from loguru import logger
from slowapi import Limiter
from slowapi.util import get_remote_address

from graphsql.config import settings

# Create rate limiter with IP address as key, configurable via env
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.rate_limit_default],
    storage_uri=settings.rate_limit_storage_uri,
)

logger.info(
    "Rate limiter initialized",
    extra={
        "default_limit": settings.rate_limit_default,
        "storage_uri": settings.rate_limit_storage_uri,
    },
)
