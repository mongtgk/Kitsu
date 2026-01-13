from __future__ import annotations

import logging
from typing import Iterable

from fastapi import Depends, Request

from . import rbac
from ..dependencies import get_optional_user
from ..errors import PermissionError
from ..models.user import User

logger = logging.getLogger("kitsu.rbac")


def get_current_role(user: User | None) -> rbac.Role:
    return rbac.resolve_role(user)


def get_current_permissions(user: User | None) -> list[rbac.Permission]:
    role = rbac.resolve_role(user)
    return rbac.resolve_permissions(role)


def _log_deny(request: Request, role: rbac.Role, required: Iterable[rbac.Permission]) -> None:
    required_list = tuple(required)
    logger.warning(
        "RBAC deny: role=%s path=%s required_permissions=%s",
        role,
        request.url.path,
        ",".join(required_list) or "none",
    )


def require_permission(permission: rbac.Permission):
    async def dependency(
        request: Request,
        user: User | None = Depends(get_optional_user),
    ) -> None:
        role = rbac.resolve_role(user)
        permissions = rbac.resolve_permissions(role)
        if permission in permissions:
            return
        _log_deny(request, role, (permission,))
        raise PermissionError()

    return dependency


def require_any_permission(permissions: Iterable[rbac.Permission]):
    required_permissions = tuple(permissions)

    async def dependency(
        request: Request,
        user: User | None = Depends(get_optional_user),
    ) -> None:
        role = rbac.resolve_role(user)
        current_permissions = rbac.resolve_permissions(role)
        if any(permission in current_permissions for permission in required_permissions):
            return
        _log_deny(request, role, required_permissions)
        raise PermissionError()

    return dependency
