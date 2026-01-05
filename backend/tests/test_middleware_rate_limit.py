import pytest
import os
from starlette.requests import Request
from starlette.responses import Response

from app.middleware.rate_limit import RateLimitMiddleware


@pytest.mark.asyncio
async def test_rate_limit_skipped_when_testing_env(monkeypatch):
    # Ensure TESTING env var causes middleware to bypass limits
    monkeypatch.setenv("TESTING", "1")

    mw = RateLimitMiddleware(app=None)

    scope = {"type": "http", "method": "GET", "path": "/test", "client": ("127.0.0.1", 1234), "headers": []}
    request = Request(scope)

    async def call_next(req):
        return Response("ok", status_code=200)

    resp = await mw.dispatch(request, call_next)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_rate_limit_blocks_and_headers(monkeypatch):
    monkeypatch.delenv("TESTING", raising=False)

    mw = RateLimitMiddleware(app=None, requests_per_minute=1, requests_per_hour=1)

    scope = {"type": "http", "method": "GET", "path": "/test", "client": ("127.0.0.1", 1234), "headers": []}
    request = Request(scope)

    async def call_next(req):
        return Response("ok", status_code=200)

    # First request should pass and include headers
    resp1 = await mw.dispatch(request, call_next)
    assert resp1.status_code == 200
    assert "X-RateLimit-Limit-Minute" in resp1.headers

    # Second request should be blocked (exceeds per-minute and per-hour)
    with pytest.raises(Exception) as exc:
        await mw.dispatch(request, call_next)
    # Expect HTTPException with 429 status
    assert "Too many" in str(exc.value) or "Rate limit" in str(exc.value)
