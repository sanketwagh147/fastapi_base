"""Authentication and authorization dependencies for FastAPI.

Provides Depends()-based auth that integrates with OpenAPI docs (lock icon),
supports dependency_overrides for testing, and composes at any level.

Usage:
    # Protect a single route
    @router.get("/profile")
    async def profile(user: AuthUser = Depends(get_current_user)):
        return {"sub": user.sub}

    # Protect an entire router
    router = APIRouter(dependencies=[Depends(get_current_active_user)])

    # Role-based access
    @router.delete("/users/{user_id}")
    async def delete_user(user: AuthUser = Depends(require_role("admin"))):
        ...

Testing:
    app.dependency_overrides[get_current_user] = lambda: AuthUser(sub="test")
"""

from typing import Any

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field

from app.core.exceptions.http_exceptions import ForbiddenError, UnauthorizedError

__all__ = [
    "AuthUser",
    "get_current_active_user",
    "get_current_user",
    "oauth2_scheme",
    "require_role",
]

# ---------------------------------------------------------------------------
# OAuth2 scheme — extracts Bearer token from Authorization header.
# tokenUrl is the endpoint your login route will live at.
# ---------------------------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ---------------------------------------------------------------------------
# Token payload model
# ---------------------------------------------------------------------------
class AuthUser(BaseModel):
    """Decoded JWT claims.

    Extend this model when you add more claims (e.g. email, tenant_id).
    """

    sub: str = Field(description="Subject — typically user ID or username")
    roles: list[str] = Field(default_factory=list, description="User roles")
    is_active: bool = Field(default=True, description="Whether the user account is active")


# ---------------------------------------------------------------------------
# Core dependency: get_current_user
# ---------------------------------------------------------------------------
async def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> AuthUser:
    """Validate the Bearer token and return the current user's claims.

    This is a **placeholder** — replace the body with real JWT decoding
    (e.g. ``jose.jwt.decode``) and optional DB lookup once ready.

    Raises:
        UnauthorizedError: If the token is missing, expired, or invalid.
    """
    # TODO: Replace with real JWT validation, e.g.:
    #
    # from jose import JWTError, jwt
    # from app.main_config import jwt_config
    #
    # try:
    #     payload = jwt.decode(
    #         token,
    #         jwt_config.secret_key.get_secret_value(),
    #         algorithms=[jwt_config.algorithm],
    #     )
    #     return AuthUser(**payload)
    # except JWTError:
    #     raise UnauthorizedError(message="Invalid or expired token")

    if not token:
        raise UnauthorizedError(message="Not authenticated")

    # Placeholder: return a dummy payload so routes are wirable now
    return AuthUser(sub="placeholder-user", roles=["user"], is_active=True)


# ---------------------------------------------------------------------------
# Chained dependency: get_current_active_user
# ---------------------------------------------------------------------------
async def get_current_active_user(
    user: AuthUser = Depends(get_current_user),
) -> AuthUser:
    """Ensure the authenticated user's account is active.

    Raises:
        UnauthorizedError: If the account is inactive/disabled.
    """
    if not user.is_active:
        raise UnauthorizedError(message="Inactive user account")
    return user


# ---------------------------------------------------------------------------
# Factory: require_role
# ---------------------------------------------------------------------------
def require_role(*required_roles: str) -> Any:
    """Return a dependency that enforces one-or-more roles.

    Usage:
        @router.get("/admin", dependencies=[Depends(require_role("admin"))])
        async def admin_panel(): ...

        # Or inject the user directly:
        @router.get("/admin")
        async def admin_panel(user: AuthUser = Depends(require_role("admin"))):
            return {"admin": user.sub}
    """

    async def _role_checker(
        user: AuthUser = Depends(get_current_active_user),
    ) -> AuthUser:
        if not any(role in user.roles for role in required_roles):
            raise ForbiddenError(
                message="Insufficient permissions",
                detail={"required_roles": list(required_roles)},
            )
        return user

    return _role_checker
