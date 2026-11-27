from qa_client import validate_post, validate_user

GOOD_USER = {"id": 1, "name": "Leanne", "username": "Bret", "email": "a@b.com"}
GOOD_POST = {"id": 1, "userId": 1, "title": "hello", "body": "text"}


def test_valid_user() -> None:
    assert validate_user(GOOD_USER) == []


def test_user_missing_and_wrong_type() -> None:
    errors = validate_user({"id": "1", "name": "x", "username": "y"})
    assert "missing field: email" in errors
    assert "id: expected int, got str" in errors


def test_user_bad_email() -> None:
    assert validate_user({**GOOD_USER, "email": "nope"}) == ["email: not a valid address"]


def test_valid_post() -> None:
    assert validate_post(GOOD_POST) == []


def test_post_empty_title() -> None:
    assert validate_post({**GOOD_POST, "title": "  "}) == ["title: empty"]
