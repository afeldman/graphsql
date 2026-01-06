"""Authentication REST endpoints."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from .auth import create_access_token, TokenResponse
from .cache import session_create

router = APIRouter(prefix="/auth", tags=["authentication"])

# Demo users - for development only!
# In production, use database for user storage
users_db = {
    "admin": {
        "user_id": "admin",
        "password": "admin123",
        "scope": "admin",
    },
    "demo": {
        "user_id": "demo",
        "password": "demo123",
        "scope": "default",
    },
}


class LoginRequest(BaseModel):
    """Login request payload."""

    username: str
    password: str


@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest) -> TokenResponse:
    """Authenticate user and return JWT token.

    Args:
        credentials: Username and password

    Returns:
        JWT access token

    Raises:
        HTTPException: 401 if invalid credentials
    """
    user = users_db.get(credentials.username)

    if not user or user["password"] != credentials.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token = create_access_token(
        user_id=user["user_id"],
        scope=user.get("scope", "default"),
    )

    # Store session in Redis (optional; best-effort)
    await session_create(
        session_id=token.access_token,
        data={"user_id": user["user_id"], "scope": user.get("scope", "default")},
    )

    return token
