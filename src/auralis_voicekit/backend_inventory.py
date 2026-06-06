"""Public-safe backend inventory helpers."""

from __future__ import annotations

from typing import Any

from ._version import __version__
from .backends import BackendRegistry, create_default_registry


def _public_dependency_name(value: str) -> str:
    normalized = value.replace("\\", "/").rstrip("/")
    return normalized.rsplit("/", 1)[-1] if "/" in normalized else value


def backend_inventory(registry: BackendRegistry | None = None) -> dict[str, Any]:
    """Return registered backend availability without local paths or credentials."""

    selected_registry = registry or create_default_registry()
    infos = selected_registry.backend_info()
    backends = [
        {
            "name": info.name,
            "kind": info.kind,
            "available": info.available,
            "reason": info.reason,
            "dependencies": [_public_dependency_name(dependency) for dependency in info.dependencies],
        }
        for info in infos
    ]
    by_kind: dict[str, dict[str, int]] = {}
    for info in infos:
        counts = by_kind.setdefault(info.kind, {"total": 0, "available": 0, "unavailable": 0})
        counts["total"] += 1
        if info.available:
            counts["available"] += 1
        else:
            counts["unavailable"] += 1
    return {
        "version": __version__,
        "backends": backends,
        "counts": {
            "total": len(infos),
            "available": sum(1 for info in infos if info.available),
            "unavailable": sum(1 for info in infos if not info.available),
            "by_kind": by_kind,
        },
        "content_policy": {
            "records_local_paths": False,
            "records_credentials": False,
        },
    }
