from .rbac import Permission

ENFORCEMENT_MATRIX: dict[tuple[str, str], list[Permission]] = {
    ("POST", "/favorites"): ["write:content"],
    ("DELETE", "/favorites/{anime_id}"): ["write:content"],
    ("POST", "/watch/progress"): ["write:content"],
    ("PATCH", "/users/me"): ["write:profile"],
}
