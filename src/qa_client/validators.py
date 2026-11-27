"""Schema checks: return a list of problems (empty list = valid)."""

from __future__ import annotations

from typing import Any

USER_FIELDS: dict[str, type] = {"id": int, "name": str, "username": str, "email": str}
POST_FIELDS: dict[str, type] = {"id": int, "userId": int, "title": str, "body": str}


def _check(obj: dict[str, Any], schema: dict[str, type]) -> list[str]:
    errors = []
    for name, expected in schema.items():
        if name not in obj:
            errors.append(f"missing field: {name}")
        elif not isinstance(obj[name], expected):
            errors.append(f"{name}: expected {expected.__name__}, got {type(obj[name]).__name__}")
    return errors


def validate_user(user: dict[str, Any]) -> list[str]:
    errors = _check(user, USER_FIELDS)
    if isinstance(user.get("email"), str) and "@" not in user["email"]:
        errors.append("email: not a valid address")
    return errors


def validate_post(post: dict[str, Any]) -> list[str]:
    errors = _check(post, POST_FIELDS)
    if isinstance(post.get("title"), str) and not post["title"].strip():
        errors.append("title: empty")
    return errors
