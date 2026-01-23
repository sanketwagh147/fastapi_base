"""
Auto-discovery router system for FastAPI.

This module provides automatic route discovery and registration.
Place route files in app/routes/ directory with a 'router' variable.

Configuration Priority:
    1. APIRouter() constructor parameters (recommended)
    2. ROUTER_CONFIG dict in the module (optional)
    3. Auto-generated from file path (default)

Example route file (app/routes/users.py):
    from fastapi import APIRouter

    router = APIRouter(
        prefix="/api/v1/users",
        tags=["users"]
    )

    @router.get("/")
    async def list_users():
        return {"users": []}
"""

import importlib
from pathlib import Path
from typing import Any

from fastapi import APIRouter, FastAPI


class RouterDiscoveryError(Exception):
    """Raised when router discovery fails."""


def discover_routers(routes_dir: Path) -> list[tuple[APIRouter, dict[str, Any]]]:
    """
    Auto-discover all routers in the routes directory.

    Args:
        routes_dir: Path to the routes directory

    Returns:
        List of (router, config) tuples where config contains prefix, tags, etc.

    Raises:
        RouterDiscoveryError: If any router file fails to load

    Configuration Priority:
        1. Router's own prefix/tags (from APIRouter constructor)
        2. ROUTER_CONFIG dict (if present in module)
        3. Auto-generated defaults (from file path)

    Note:
        Files starting with _ are ignored (e.g., _example.py, __init__.py)
    """
    routers = []

    # Get all Python files in routes directory (excluding __init__.py and _*.py)
    for py_file in routes_dir.rglob("*.py"):
        # ALWAYS ignore files starting with underscore
        if py_file.name.startswith("_"):
            continue

        # Convert file path to module path
        # e.g., app/routes/v1/events.py -> app.routes.v1.events
        # Need to go up to project root (parent of 'app' folder)
        relative_path = py_file.relative_to(routes_dir.parent.parent)
        module_path = str(relative_path.with_suffix("")).replace("/", ".")

        try:
            # Import the module
            print(f"  Loading: {module_path}")
            module = importlib.import_module(module_path)

            # Check if module has a 'router' attribute
            if not hasattr(module, "router"):
                msg = (
                    f"Router file '{py_file.name}' does not export a 'router' variable.\n"
                    f"  File: {py_file}\n"
                    f"  Module: {module_path}"
                )
                raise RouterDiscoveryError(msg)

            router = module.router

            # Validate it's an APIRouter instance
            if not isinstance(router, APIRouter):
                msg = (
                    f"Router file '{py_file.name}' exports 'router' but it's not "
                    f"an APIRouter instance.\n"
                    f"  File: {py_file}\n"
                    f"  Module: {module_path}\n"
                    f"  Type: {type(router).__name__}"
                )
                raise RouterDiscoveryError(msg)

            # Start with router's built-in configuration
            config = {}

            # Extract prefix from router if set
            if router.prefix:
                config["prefix"] = router.prefix

            # Extract tags from router if set
            if router.tags:
                config["tags"] = list(router.tags)

            # Merge with ROUTER_CONFIG (overrides router settings if present)
            if hasattr(module, "ROUTER_CONFIG"):
                router_config = module.ROUTER_CONFIG
                if not isinstance(router_config, dict):
                    msg = (
                        f"Router file '{py_file.name}' has ROUTER_CONFIG but it's not a dict.\n"
                        f"  File: {py_file}\n"
                        f"  Module: {module_path}\n"
                        f"  Type: {type(router_config).__name__}"
                    )
                    raise RouterDiscoveryError(msg)
                config.update(router_config)

            # Apply defaults only if not configured
            if "prefix" not in config:
                # Auto-generate prefix from file path
                # e.g., routes/v1/events.py -> /api/v1/events
                route_path = py_file.relative_to(routes_dir).with_suffix("")
                config["prefix"] = f"/api/{route_path}".replace("\\", "/")

            if "tags" not in config:
                # Use filename as tag
                config["tags"] = [py_file.stem]

            routers.append((router, config))

        except Exception as e:
            print(f"  ❌ Error in {py_file.name}: {type(e).__name__}: {e}")
            # Re-raise the original exception to see the full traceback
            raise

    return routers


def register_routers(app: FastAPI, routes_dir: Path | None = None) -> None:
    """
    Discover and register all routers with the FastAPI app.

    This function will raise an exception and fail the app startup if:
    - Any router file fails to import
    - Any router file doesn't export a 'router' variable
    - Any router file exports an invalid router type

    Files starting with _ are always ignored (e.g., _example.py).

    Args:
        app: FastAPI application instance
        routes_dir: Optional path to routes directory.
                   If None, uses app/routes relative to this file.

    Raises:
        RouterDiscoveryError: If any router file fails to load
        FileNotFoundError: If routes directory doesn't exist

    Call this once during app initialization in main.py:
        from app.core.route_discovery import register_routers
        register_routers(app)
    """
    if routes_dir is None:
        # Default: app/routes directory
        routes_dir = Path(__file__).parent.parent / "routes"

    if not routes_dir.exists():
        msg = (
            f"Routes directory not found: {routes_dir}\n"
            f"  Expected: {routes_dir}\n"
            f"  Hint: Create the directory or check your project structure"
        )
        raise FileNotFoundError(msg)

    print(f"🔍 Discovering routes in: {routes_dir}")

    routers = discover_routers(routes_dir)

    if not routers:
        print("⚠️  No routers discovered (only files starting with _ found)")
        return

    print(f"📦 Found {len(routers)} router(s)\n")

    for router, config in routers:
        try:
            app.include_router(router, **config)
            prefix = config.get("prefix", "")
            tags = config.get("tags", [])
            print(f"  ✓ {prefix} (tags: {tags})")
        except Exception as e:
            msg = (
                f"Failed to register router with prefix '{config.get('prefix', 'unknown')}'.\n"
                f"  Config: {config}\n"
                f"  Error: {e}"
            )
            raise RouterDiscoveryError(msg) from e
