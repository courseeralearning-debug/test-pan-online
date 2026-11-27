"""Regression: full functional + contract checks. Runs on main (or FORCE_REGRESSION)."""

import pytest

from qa_client import ApiError, validate_post, validate_user

pytestmark = pytest.mark.regression


@pytest.mark.parametrize("user_id", range(1, 11))
def test_user_schema(api, user_id: int) -> None:
    user = api.get_user(user_id)
    assert validate_user(user) == [], f"user {user_id}: {validate_user(user)}"


@pytest.mark.parametrize("user_id", [1, 5, 10])
def test_posts_filtered_by_user(api, user_id: int) -> None:
    posts = api.list_posts(user_id)
    assert posts, "expected at least one post"
    assert all(p["userId"] == user_id for p in posts)
    assert all(validate_post(p) == [] for p in posts)


def test_create_post(api) -> None:
    created = api.create_post(1, "ci title", "ci body")
    assert created["title"] == "ci title"
    assert created["userId"] == 1
    assert "id" in created


def test_unknown_user_returns_404(api) -> None:
    with pytest.raises(ApiError) as exc:
        api.get_user(99999)
    assert exc.value.status == 404
