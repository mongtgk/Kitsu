from __future__ import annotations

import logging
from typing import Annotated, Iterable

from fastapi import Depends, HTTPException, Request, status

from . import rbac
from ..dependencies import get_current_role
from ..errors import PermissionError

logger = logging.getLogger("kitsu.rbac")


def _log_deny(request: Request | None, role: rbac.Role, required: Iterable[rbac.Permission]) -> None:
    required_permissions = ",".join(required)
    if required_permissions == "":
        required_permissions = "none"
    path = request.url.path if request else "unknown"
    logger.warning(
        "RBAC deny: role=%s path=%s required_permissions=%s",
        role,
        path,
        required_permissions,
    )


def require_permission(permission: rbac.Permission):
    async def dependency(
        role: Annotated[rbac.Role, Depends(get_current_role)],
        request: Request,
    ) -> None:
        permissions = rbac.resolve_permissions(role)
        if permission in permissions:
            return
        _log_deny(request, role, (permission,))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=PermissionError.message
        )

    return dependency


def require_any_permission(permissions: Iterable[rbac.Permission]):
    required_permissions = tuple(permissions)

    async def dependency(
        role: Annotated[rbac.Role, Depends(get_current_role)],
        request: Request,
    ) -> None:
        current_permissions = rbac.resolve_permissions(role)
        if any(permission in current_permissions for permission in required_permissions):
            return
        _log_deny(request, role, required_permissions)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=PermissionError.message
        )

    return dependency
