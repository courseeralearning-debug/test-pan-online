"""Loads non-secret config from config/<env>.env; secrets come only from Jenkins env vars."""

import os
from pathlib import Path

import pytest

from qa_client import ApiClient


def _load(name: str) -> dict[str, str]:
    cfg = {}
    for line in (Path(__file__).parent / "config" / f"{name}.env").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            key, _, value = line.partition("=")
            cfg[key.strip()] = value.strip()
    return cfg


@pytest.fixture(scope="session")
def env_config() -> dict[str, str]:
    cfg = _load(os.environ.get("DEPLOY_ENV", "dev"))
    # Secret: injected by withCredentials in Jenkins, never committed.
    cfg["API_TOKEN"] = os.environ.get("API_TOKEN", "")
    return cfg


@pytest.fixture(scope="session")
def api(env_config: dict[str, str]) -> ApiClient:
    return ApiClient(
        base_url=env_config["BASE_URL"],
        token=env_config["API_TOKEN"],
        timeout=float(env_config.get("TIMEOUT_SECONDS", "10")),
    )
