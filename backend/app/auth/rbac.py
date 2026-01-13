from __future__ import annotations

from typing import Final, Iterable

from ..models.user import User

Role = str
Permission = str

BASE_ROLES: Final[tuple[Role, ...]] = ("guest", "user", "admin")
BASE_PERMISSIONS: Final[tuple[Permission, ...]] = (
    "read:profile",
    "write:profile",
    "read:content",
    "write:content",
    "admin:*",
)

ROLE_PERMISSIONS: Final[dict[Role, tuple[Permission, ...]]] = {
    "guest": ("read:content",),
    "user": ("read:profile", "write:profile", "read:content", "write:content"),
    "admin": BASE_PERMISSIONS,
}


def resolve_role(user: User | None) -> Role:
    if user is None:
        return "guest"
    if getattr(user, "is_admin", False):
        return "admin"
    return "user"


def resolve_permissions(role: Role) -> list[Permission]:
    return list(ROLE_PERMISSIONS.get(role, ()))


def get_current_role(user: User | None) -> Role:
    return resolve_role(user)


def get_current_permissions(user: User | None) -> list[Permission]:
    role = resolve_role(user)
    return resolve_permissions(role)
