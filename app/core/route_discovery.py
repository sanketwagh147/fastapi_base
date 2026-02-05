"""FastAPI route auto-discovery.

Conventions:
- Put route modules under `app/routes/`.
- Each module exports a `router: APIRouter`.
- Files starting with `_` are ignored.

Configuration:
- Prefer setting `prefix`/`tags` in the `APIRouter(...)` constructor.
- Optionally export `ROUTER_CONFIG` (a mapping) for additional `include_router(...)`
  kwargs (e.g., `dependencies`, `responses`).
- If a router has no `prefix`/`tags`, defaults are generated from the file path.
"""

import importlib
import logging
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from fastapi import APIRouter, FastAPI

logger = logging.getLogger(__name__)


class RouterDiscoveryError(Exception):
    """Raised when router discovery fails."""


_CONFIG_PREFIX_KEY = "prefix"
_CONFIG_TAGS_KEY = "tags"


def _iter_route_files(routes_dir: Path) -> list[Path]:
    return sorted(
        (
            py_file
            for py_file in routes_dir.rglob("*.py")
            if py_file.is_file() and not py_file.name.startswith("_")
        ),
        key=lambda path: path.as_posix(),
    )


def _infer_module_path(routes_dir: Path, py_file: Path) -> str:
    """Infer the importable module path for a route file.

    Default expectation: routes live under an importable package like `app/routes/*`.
    For example, `app/routes/v1/events.py` -> `app.routes.v1.events`.
    """
    routes_package = routes_dir.name
    if routes_package == "routes":
        base_package = routes_dir.parent.name
        rel_module = ".".join(py_file.relative_to(routes_dir).with_suffix("").parts)
        return f"{base_package}.routes.{rel_module}"

    # Fallback: build from project root (parent of 'app')
    # e.g., <root>/app/routes/v1/events.py -> app.routes.v1.events
    project_root = routes_dir.parent.parent
    relative_path = py_file.relative_to(project_root)
    return ".".join(relative_path.with_suffix("").parts)


def _load_router_config(module: Any, py_file: Path, module_path: str) -> dict[str, Any]:
    if not hasattr(module, "ROUTER_CONFIG"):
        return {}

    router_config = module.ROUTER_CONFIG
    if not isinstance(router_config, Mapping):
        msg = (
            f"Router file '{py_file.name}' has ROUTER_CONFIG but it's not a mapping.\n"
            f"  File: {py_file}\n"
            f"  Module: {module_path}\n"
            f"  Type: {type(router_config).__name__}"
        )
        raise RouterDiscoveryError(msg)

    return dict(router_config)


def _normalize_tags(value: Any, py_file: Path, module_path: str) -> list[str]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        msg = (
            f"ROUTER_CONFIG['tags'] must be a sequence of strings.\n"
            f"  File: {py_file}\n"
            f"  Module: {module_path}\n"
            f"  Type: {type(value).__name__}"
        )
        raise RouterDiscoveryError(msg)

    tags = list(value)
    if not all(isinstance(tag, str) for tag in tags):
        msg = (
            f"ROUTER_CONFIG['tags'] must contain only strings.\n"
            f"  File: {py_file}\n"
            f"  Module: {module_path}\n"
            f"  Value: {tags}"
        )
        raise RouterDiscoveryError(msg)

    return tags


def discover_routers(routes_dir: Path) -> list[tuple[APIRouter, dict[str, Any]]]:
    """Discover routers under a routes directory.

    Returns a list of `(router, include_kwargs)` pairs.

    Prefix/tags precedence:
    1. Router's own `prefix`/`tags` (defined in `APIRouter(...)`)
    2. `ROUTER_CONFIG['prefix'|'tags']` (only if router doesn't set them)
    3. Defaults from file path (only if still missing)
    """
    routers: list[tuple[APIRouter, dict[str, Any]]] = []

    for py_file in _iter_route_files(routes_dir):
        module_path = _infer_module_path(routes_dir, py_file)

        try:
            module = importlib.import_module(module_path)
        except Exception as e:
            msg = (
                f"Failed to import route module '{module_path}'.\n"
                f"  File: {py_file}\n"
                f"  Hint: Ensure the package is importable and dependencies are installed"
            )
            raise RouterDiscoveryError(msg) from e

        if not hasattr(module, "router"):
            msg = (
                f"Router file '{py_file.name}' does not export a 'router' variable.\n"
                f"  File: {py_file}\n"
                f"  Module: {module_path}"
            )
            raise RouterDiscoveryError(msg)

        router = module.router

        if not isinstance(router, APIRouter):
            msg = (
                f"Router file '{py_file.name}' exports 'router' but it's not an APIRouter "
                f"instance.\n"
                f"  File: {py_file}\n"
                f"  Module: {module_path}\n"
                f"  Type: {type(router).__name__}"
            )
            raise RouterDiscoveryError(msg)

        router_config = _load_router_config(module, py_file, module_path)

        # Build kwargs for include_router.
        # Key idea: DO NOT pass prefix/tags if the router already defines them,
        # otherwise they will be applied twice.
        include_kwargs: dict[str, Any] = {
            key: value
            for key, value in router_config.items()
            if key not in {_CONFIG_PREFIX_KEY, _CONFIG_TAGS_KEY}
        }

        if not router.prefix:
            if _CONFIG_PREFIX_KEY in router_config:
                prefix_value = router_config[_CONFIG_PREFIX_KEY]
                if not isinstance(prefix_value, str):
                    msg = (
                        f"ROUTER_CONFIG['prefix'] must be a string.\n"
                        f"  File: {py_file}\n"
                        f"  Module: {module_path}\n"
                        f"  Type: {type(prefix_value).__name__}"
                    )
                    raise RouterDiscoveryError(msg)
                include_kwargs[_CONFIG_PREFIX_KEY] = prefix_value
            else:
                route_path = py_file.relative_to(routes_dir).with_suffix("")
                include_kwargs[_CONFIG_PREFIX_KEY] = f"/api/{route_path.as_posix()}"

        if not router.tags:
            if _CONFIG_TAGS_KEY in router_config:
                include_kwargs[_CONFIG_TAGS_KEY] = _normalize_tags(
                    router_config[_CONFIG_TAGS_KEY], py_file, module_path
                )
            else:
                include_kwargs[_CONFIG_TAGS_KEY] = [py_file.stem]

        routers.append((router, include_kwargs))

    return routers


def register_routers(app: FastAPI, routes_dir: Path | None = None) -> None:
    """Discover and register routers with a FastAPI app.

    Fails fast on startup if a route module can't be imported or doesn't export a
    valid `router`.
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

    logger.info("Discovering routes in: %s", routes_dir)

    routers = discover_routers(routes_dir)

    if not routers:
        logger.warning("No routers discovered (only files starting with _ found)")
        return

    logger.info("Found %s router(s)", len(routers))

    for router, config in routers:
        try:
            app.include_router(router, **config)
            effective_prefix = config.get("prefix") or router.prefix or ""
            effective_tags = config.get("tags") or list(router.tags or [])
            logger.info("  - %s (tags: %s)", effective_prefix, effective_tags)
        except Exception as e:
            msg = (
                f"Failed to register router with prefix '{config.get('prefix', 'unknown')}'.\n"
                f"  Config: {config}\n"
                f"  Error: {e}"
            )
            raise RouterDiscoveryError(msg) from e
