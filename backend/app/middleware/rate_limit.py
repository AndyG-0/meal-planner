"""Rate limiting middleware."""

import logging
import time
from collections import defaultdict
from collections.abc import Callable

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware to prevent API abuse."""

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour

        # Store request timestamps for each IP
        self.request_times: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and apply rate limiting."""
        # Disable rate limiting during tests
        import os
        if os.environ.get("TESTING"):
            return await call_next(request)

        # Skip rate limiting for health check and docs
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        current_time = time.time()

        # Clean up old request times (older than 1 hour)
        one_hour_ago = current_time - 3600
        self.request_times[client_ip] = [
            t for t in self.request_times[client_ip] if t > one_hour_ago
        ]

        # Check rate limits
        recent_requests = self.request_times[client_ip]

        # Check requests per hour
        if len(recent_requests) >= self.requests_per_hour:
            logger.warning("Rate limit exceeded (hourly) for IP: %s", client_ip)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
                headers={"Retry-After": "3600"},
            )

        # Check requests per minute
        one_minute_ago = current_time - 60
        recent_minute = [t for t in recent_requests if t > one_minute_ago]
        if len(recent_minute) >= self.requests_per_minute:
            logger.warning("Rate limit exceeded (per minute) for IP: %s", client_ip)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please slow down.",
                headers={"Retry-After": "60"},
            )

        # Add current request
        self.request_times[client_ip].append(current_time)

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit-Minute"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Limit-Hour"] = str(self.requests_per_hour)
        response.headers["X-RateLimit-Remaining-Minute"] = str(
            max(0, self.requests_per_minute - len(recent_minute) - 1)
        )
        response.headers["X-RateLimit-Remaining-Hour"] = str(
            max(0, self.requests_per_hour - len(recent_requests))
        )

        return response
