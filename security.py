"""Shared hardening helpers for the PAF internal services.

Every request (except /ping) must carry the shared secret in the
`X-Internal-Key` header. The service refuses to start without a key, so a
missing/forgotten environment variable can never leave it open.
"""
import hmac
import logging
import os
import threading
import time
from collections import defaultdict, deque

from dotenv import load_dotenv
from fastapi import HTTPException, Request, Security
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

logger = logging.getLogger("paf.service")

MIN_KEY_LENGTH = 32


def _load_key() -> bytes:
    key = os.getenv("INTERNAL_API_KEY", "").strip()
    if len(key) < MIN_KEY_LENGTH:
        raise RuntimeError(
            "INTERNAL_API_KEY is missing or shorter than 32 characters. Generate one with: "
            'python -c "import secrets; print(secrets.token_urlsafe(48))" '
            "and put the SAME value in this service's .env and in the Django backend's .env."
        )
    return key.encode("utf-8")


_API_KEY = _load_key()
_api_key_header = APIKeyHeader(name="X-Internal-Key", auto_error=False)


def require_api_key(request: Request, supplied: str = Security(_api_key_header)):
    """FastAPI dependency: constant-time comparison of the shared secret."""
    ok = bool(supplied) and hmac.compare_digest(supplied.encode("utf-8", "ignore"), _API_KEY)
    if not ok:
        logger.warning(
            "Rejected request to %s: missing/invalid X-Internal-Key (client=%s)",
            request.url.path,
            request.client.host if request.client else "?",
        )
        raise HTTPException(status_code=401, detail="Unauthorized")


class SlidingWindowLimiter:
    """Small in-memory sliding-window limiter (per process; run one uvicorn worker)."""

    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window = window_seconds
        self._hits = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] > self.window:
                hits.popleft()
            if len(hits) >= self.limit:
                return False
            hits.append(now)
            if len(self._hits) > 5000:  # keep memory bounded
                for k in [k for k, v in self._hits.items() if not v or now - v[-1] > self.window]:
                    self._hits.pop(k, None)
            return True


def env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


def env_flag(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


def error_response(status_code: int, message: str) -> JSONResponse:
    """Same JSON shape the Django backend already reads ({"status": ...})."""
    return JSONResponse(status_code=status_code, content={"status": "error", "message": message, "data": None})


def mask_phone(number: str) -> str:
    return f"{number[:4]}****{number[-3:]}" if len(number) >= 8 else "****"


def mask_email(address: str) -> str:
    local, _, domain = address.partition("@")
    return f"{local[:1]}***@{domain}" if domain else "***"
