"""Declarative mapping of protected endpoints to required permissions.

Each key is a (METHOD, PATH) tuple, and the value is a tuple of permissions
that satisfy the endpoint's RBAC enforcement.
"""
from .rbac import Permission

ENFORCEMENT_MATRIX: dict[tuple[str, str], tuple[Permission, ...]] = {
    ("POST", "/favorites"): ("write:content",),
    ("DELETE", "/favorites/{anime_id}"): ("write:content",),
    ("POST", "/watch/progress"): ("write:content",),
    ("PATCH", "/users/me"): ("write:profile",),
}
