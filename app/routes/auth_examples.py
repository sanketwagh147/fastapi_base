"""Sample auth-protected routes demonstrating all protection levels.

This file shows how to use the auth dependencies from app.core.auth.
Auto-discovered by route_discovery — drop it in app/routes/ and it works.

Remove or replace this file once you build real authenticated endpoints.
"""

from fastapi import APIRouter, Depends

from app.core.auth import AuthUser, get_current_active_user, get_current_user, require_role

router = APIRouter(
    prefix="/api/auth-examples",
    tags=["auth-examples"],
)


# =============================================================================
# Level 1: Any authenticated user (valid token required)
# =============================================================================


@router.get("/me")
async def get_me(user: AuthUser = Depends(get_current_user)):
    """Return the current user's token claims.

    Requires: valid Bearer token in Authorization header.
    """
    return {"sub": user.sub, "roles": user.roles}


# =============================================================================
# Level 2: Authenticated + active account
# =============================================================================


@router.get("/me/active")
async def get_me_active(user: AuthUser = Depends(get_current_active_user)):
    """Same as /me but also verifies the account is active.

    Requires: valid token + is_active=True.
    """
    return {"sub": user.sub, "roles": user.roles, "is_active": user.is_active}


# =============================================================================
# Level 3: Role-based access control
# =============================================================================


@router.get("/admin-only")
async def admin_only(user: AuthUser = Depends(require_role("admin"))):
    """Only users with the 'admin' role can access this.

    Requires: valid token + active account + 'admin' in roles.
    """
    return {"message": f"Hello admin {user.sub}"}


@router.get("/editor-or-admin")
async def editor_or_admin(user: AuthUser = Depends(require_role("admin", "editor"))):
    """Users with 'admin' OR 'editor' role can access this.

    Requires: valid token + active account + at least one matching role.
    """
    return {"message": f"Hello {user.sub}", "roles": user.roles}


# =============================================================================
# Level 4: Router-level protection (all routes require auth)
# =============================================================================
# To protect every route in a router at once, pass dependencies to APIRouter:
#
#   protected_router = APIRouter(
#       prefix="/api/protected",
#       tags=["protected"],
#       dependencies=[Depends(get_current_active_user)],
#   )
#
#   @protected_router.get("/resource")
#   async def get_resource():
#       # No need to add Depends() here — already enforced by the router
#       return {"data": "secret"}
