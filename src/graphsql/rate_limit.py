"""Rate limiting configuration and middleware."""

from slowapi import Limiter
from slowapi.util import get_remote_address
from loguru import logger

# Create rate limiter with IP address as key
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["60 per minute"],  # Global default: 60 requests per minute
    storage_uri="memory://",  # In-memory storage (for production use Redis)
)

# Log rate limit info
logger.info("Rate limiter initialized with 60 req/min default limit")
