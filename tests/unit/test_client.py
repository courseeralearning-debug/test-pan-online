"""Unit tests: fake HTTP session, no network, run in milliseconds."""

from typing import Any

import pytest

from qa_client import ApiClient, ApiError


class FakeResponse:
    def __init__(self, status_code: int, payload: Any = None) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> Any:
        return self._payload


class FakeSession:
    def __init__(self, *responses: FakeResponse) -> None:
        self.headers: dict[str, str] = {}
        self.calls: list[tuple[str, str, dict[str, Any]]] = []
        self._responses = list(responses)

    def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append((method, url, kwargs))
        return self._responses.pop(0)


def make_client(*responses: FakeResponse, token: str = "") -> tuple[ApiClient, FakeSession]:
    session = FakeSession(*responses)
    client = ApiClient("https://api.test/", token=token, timeout=5, session=session)  # type: ignore[arg-type]
    return client, session


def test_get_user_builds_url_and_returns_json() -> None:
    client, session = make_client(FakeResponse(200, {"id": 1}))
    assert client.get_user(1) == {"id": 1}
    method, url, kwargs = session.calls[0]
    assert (method, url, kwargs["timeout"]) == ("GET", "https://api.test/users/1", 5)


def test_token_sets_bearer_header() -> None:
    _, session = make_client(token="abc")
    assert session.headers["Authorization"] == "Bearer abc"


def test_no_token_no_header() -> None:
    _, session = make_client()
    assert "Authorization" not in session.headers


@pytest.mark.parametrize(("user_id", "expected"), [(None, None), (3, {"userId": 3})])
def test_list_posts_params(user_id: int | None, expected: dict[str, int] | None) -> None:
    client, session = make_client(FakeResponse(200, []))
    client.list_posts(user_id)
    assert session.calls[0][2]["params"] == expected


def test_create_post_sends_json() -> None:
    client, session = make_client(FakeResponse(201, {"id": 101}))
    assert client.create_post(1, "t", "b") == {"id": 101}
    method, _, kwargs = session.calls[0]
    assert method == "POST"
    assert kwargs["json"] == {"userId": 1, "title": "t", "body": "b"}


@pytest.mark.parametrize("status", [400, 404, 500])
def test_error_status_raises(status: int) -> None:
    client, _ = make_client(FakeResponse(status))
    with pytest.raises(ApiError) as exc:
        client.get_user(1)
    assert exc.value.status == status
