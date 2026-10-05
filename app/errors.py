import time
from collections import defaultdict, deque
from fastapi import Request
from app.config import settings


class AppError(Exception):
    def __init__(self, status: int, message: str):
        self.status, self.message = status, message


def ok(data=None) -> dict:
    return {"success": True, "data": data if data is not None else {}}


class RateLimiter:
    """In-memory sliding window per client IP. Use Redis for multi-process deployments."""

    def __init__(self, limit: int, window: int = 60):
        self.limit, self.window, self.hits = limit, window, defaultdict(deque)

    def __call__(self, request: Request) -> None:
        if not settings.RATE_LIMIT:
            return
        key = request.client.host if request.client else "unknown"
        q, now = self.hits[key], time.monotonic()
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) >= self.limit:
            raise AppError(429, "ส่งคำขอถี่เกินไป กรุณาลองใหม่ภายหลัง")
        q.append(now)
