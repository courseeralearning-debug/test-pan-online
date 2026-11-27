"""Smoke: is the environment up and answering on its critical paths? Runs on every branch."""

import pytest

pytestmark = pytest.mark.smoke


def test_get_user(api) -> None:
    user = api.get_user(1)
    assert user["id"] == 1


def test_list_posts_not_empty(api) -> None:
    assert len(api.list_posts()) > 0
