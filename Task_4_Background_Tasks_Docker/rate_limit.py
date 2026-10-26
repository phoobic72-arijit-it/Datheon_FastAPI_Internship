"""Bounded, per-client sliding-window rate limiting for the submit route."""

import math
import os
import time
from collections import deque
from threading import Lock

from fastapi import HTTPException, Request


class RateLimiter:
    def __init__(self):
        self.limit = int(os.getenv("RATE_LIMIT_REQUESTS", "5"))
        self.window = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
        if self.limit < 1 or self.window < 1:
            raise ValueError("Rate limit settings must be positive integers")
        self.clients = {}
        self.lock = Lock()
        self.cleanup_at = 0.0

    def __call__(self, request: Request):
        now = time.monotonic()
        client = request.client.host if request.client else "unknown"

        with self.lock:
            if now >= self.cleanup_at:
                for key in list(self.clients):
                    if not self.clients[key] or self.clients[key][-1] <= now - self.window:
                        del self.clients[key]
                self.cleanup_at = now + self.window

            if client not in self.clients and len(self.clients) >= 10000:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limiter capacity reached; try again later",
                    headers={"Retry-After": str(self.window)},
                )

            timestamps = self.clients.setdefault(client, deque())
            while timestamps and timestamps[0] <= now - self.window:
                timestamps.popleft()

            if len(timestamps) >= self.limit:
                retry_after = max(1, math.ceil(self.window - (now - timestamps[0])))
                raise HTTPException(
                    status_code=429,
                    detail=f"Maximum {self.limit} webhook submissions per {self.window} seconds",
                    headers={"Retry-After": str(retry_after)},
                )

            timestamps.append(now)


limiter = RateLimiter()
