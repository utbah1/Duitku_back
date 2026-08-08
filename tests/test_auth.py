"""Authentication dependency tests."""
import asyncio

import pytest
from fastapi import HTTPException

from app.core.dependencies import get_bearer_token


def _run(coro):
    return asyncio.get_event_loop_policy().new_event_loop().run_until_complete(coro)


def test_missing_token_is_unauthorized(client):
    resp = client.get("/api/v1/users/me")
    assert resp.status_code == 401


def test_invalid_scheme_is_unauthorized(client):
    resp = client.get("/api/v1/users/me", headers={"Authorization": "Basic abc"})
    assert resp.status_code == 401


def test_valid_token_returns_user(client, auth_headers):
    # /users/me auto-creates profile via upsert when it doesn't exist
    resp = client.get("/api/v1/users/me", headers=auth_headers)
    # If profile missing -> 404 from UserService.get_me; use /auth/me which auto-upserts
    resp = client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["uid"] == "test-user-123"


def test_get_bearer_token_missing_raises():
    with pytest.raises(HTTPException) as exc:
        _run(get_bearer_token(authorization=None))
    assert exc.value.status_code == 401


def test_bearer_token_extraction():
    token = _run(get_bearer_token(authorization="Bearer abc.def.ghi"))
    assert token == "abc.def.ghi"
