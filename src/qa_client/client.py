"""Thin REST client. The session is injectable so unit tests never touch the network."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import requests


class ApiError(Exception):
    """Raised when the API answers with a 4xx/5xx status."""

    def __init__(self, method: str, path: str, status: int) -> None:
        super().__init__(f"{method} {path} -> HTTP {status}")
        self.status = status


@dataclass
class ApiClient:
    base_url: str
    token: str = ""
    timeout: float = 10.0
    session: requests.Session = field(default_factory=requests.Session)

    def __post_init__(self) -> None:
        self.base_url = self.base_url.rstrip("/")
        if self.token:
            self.session.headers["Authorization"] = f"Bearer {self.token}"

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        resp = self.session.request(method, url, timeout=self.timeout, **kwargs)
        if resp.status_code >= 400:
            raise ApiError(method, path, resp.status_code)
        return resp.json()

    def get_user(self, user_id: int) -> dict[str, Any]:
        return self._request("GET", f"/users/{user_id}")

    def list_posts(self, user_id: int | None = None) -> list[dict[str, Any]]:
        params = {"userId": user_id} if user_id is not None else None
        return self._request("GET", "/posts", params=params)

    def create_post(self, user_id: int, title: str, body: str) -> dict[str, Any]:
        payload = {"userId": user_id, "title": title, "body": body}
        return self._request("POST", "/posts", json=payload)
