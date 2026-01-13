from __future__ import annotations

from typing import Final

from ..models.user import User

Role = str
Permission = str

ROLE_GUEST: Final[Role] = "guest"
ROLE_USER: Final[Role] = "user"
ROLE_ADMIN: Final[Role] = "admin"

PERMISSION_READ_PROFILE: Final[Permission] = "read:profile"
PERMISSION_WRITE_PROFILE: Final[Permission] = "write:profile"
PERMISSION_READ_CONTENT: Final[Permission] = "read:content"
PERMISSION_WRITE_CONTENT: Final[Permission] = "write:content"
PERMISSION_ADMIN_ALL: Final[Permission] = "admin:*"

RolePermissions = dict[Role, tuple[Permission, ...]]

ROLE_PERMISSIONS: Final[RolePermissions] = {
    ROLE_GUEST: (PERMISSION_READ_CONTENT,),
    ROLE_USER: (
        PERMISSION_READ_PROFILE,
        PERMISSION_WRITE_PROFILE,
        PERMISSION_READ_CONTENT,
        PERMISSION_WRITE_CONTENT,
    ),
    ROLE_ADMIN: (
        PERMISSION_READ_PROFILE,
        PERMISSION_WRITE_PROFILE,
        PERMISSION_READ_CONTENT,
        PERMISSION_WRITE_CONTENT,
        PERMISSION_ADMIN_ALL,
    ),
}


def resolve_role(user: User | None) -> Role:
    """
    Derive a role for the current subject.

    The resolver is deterministic and read-only: it does not mutate state
    or enforce access, and defaults to a guest role for anonymous callers.
    """
    if user is None:
        return ROLE_GUEST

    role = getattr(user, "role", None)
    # Optional explicit role attribute supports future extensibility without enforcement.
    if isinstance(role, str) and role in ROLE_PERMISSIONS:
        return role

    return ROLE_USER


def resolve_permissions(role: Role) -> list[Permission]:
    """
    Resolve permissions for a given role without side effects.

    A copy is returned to prevent accidental mutation of the role map.
    """
    return list(ROLE_PERMISSIONS.get(role, ()))
