from __future__ import annotations

from . import rbac
from ..models.user import User


def get_current_role(user: User | None) -> rbac.Role:
    return rbac.resolve_role(user)


def get_current_permissions(user: User | None) -> list[rbac.Permission]:
    role = rbac.resolve_role(user)
    return rbac.resolve_permissions(role)
