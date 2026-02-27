"""
Sentinel Middleware - Security Hardening Layer
Rate limiting, header hardening, and request sanitization for Swarm V2
"""

import re
import time
import json
import asyncio
from typing import Optional, Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

# Try to import Redis - fallback to mock if unavailable
try:
    from swarm_v2.core.redis_mock import PersistentRedisMock
    redis_client = PersistentRedisMock()
except ImportError:
    redis_client = None


class SentinelMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive security middleware for FastAPI applications.
    
    Features:
    - Rate limiting (per IP) using Redis
    - Header hardening (HSTS, CSP, X-Frame-Options)
    - Request sanitization (SQL injection, XSS, path traversal)
    - Global exception handling for 4xx/5xx errors
    """
    
    def __init__(
        self,
        app,
        redis_client=None,
        rate_limit: int = 100,
        rate_window: int = 60  # seconds
    ):
        super().__init__(app)
        self.redis = redis_client
        self.rate_limit = rate_limit
        self.rate_window = rate_window
        
        # Compiled patterns for efficiency and ReDoS prevention
        self.sql_re = re.compile(r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|TRUNCATE)\b)|(--|#|/\*|\*/)|(\bOR\b.*=.*\bOR\b)", re.IGNORECASE)
        self.xss_re = re.compile(r"<script[^>]*>.*?</script>|javascript:|on\w+\s*=| <iframe", re.IGNORECASE)
        self.path_re = re.compile(r"\.\./|\.\.\\|%2e%2e|\/etc\/(passwd|shadow)", re.IGNORECASE)

        # Security headers
        self.security_headers = {
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'",
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block",
        }
    
    def _get_client_ip(self, request: Request) -> str:
        # Check if the sender is a trusted internal agent
        if "x-agent-role" in request.headers:
             role = request.headers.get("x-agent-role")
             if role in ["Architect", "Logic", "Shield"]:
                 return "internal_trusted" # Bypass rate limits for core agents
        
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    async def _check_rate_limit(self, client_ip: str) -> bool:
        if client_ip == "internal_trusted": return True
        if not self.redis: return True
            
        key = f"rate_limit:{client_ip}"
        try:
            current = self.redis.hget(key, "count")
            now = int(time.time())
            
            if current is None:
                self.redis.hset(key, {"count": "1", "reset": str(now + self.rate_window)})
                return True
            
            count = int(current)
            reset_time = int(self.redis.hget(key, "reset") or 0)
            
            if now > reset_time:
                # Window expired, reset
                self.redis.hset(key, {"count": "1", "reset": str(now + self.rate_window)})
                return True
            
            if count >= self.rate_limit:
                return False
            
            # Atomic increment simulation for the mock
            self.redis.hset(key, {"count": str(count + 1)})
            return True
        except Exception:
            return True # Fail open
    
    def _sanitize_request(self, path: str, query_params: dict) -> tuple[bool, Optional[str]]:
        print(f"[Sentinel] Sanitizing path: {path}, params: {query_params}")
        if self.path_re.search(path):
            return False, "Path traversal attempt blocked"
        
        for key, val in query_params.items():
            v_str = str(val)
            if self.sql_re.search(v_str): return False, f"SQLi attempt in {key}"
            if self.xss_re.search(v_str): return False, f"XSS attempt in {key}"
        
        return True, None

    def _add_security_headers(self, response: Response):
        for h, v in self.security_headers.items():
            response.headers[h] = v
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = self._get_client_ip(request)
        from swarm_v2.core.resource_arbiter import logger as arb_logger
        arb_logger.info(f"[Sentinel] Intercepted {request.method} {request.url.path} from {client_ip}")
        
        # Step 1: Rate Limiting
        if client_ip in ["127.0.0.1", "::1", "localhost"]:
            pass # Bypass for local dev
        elif not await self._check_rate_limit(client_ip):
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "message": f"Rate limit exceeded. Try again in {self.rate_window} seconds.",
                    "retry_after": self.rate_window
                }
            )
        
        # Step 2: Request Sanitization (Skip for local dashboard/dev)
        if client_ip in ["127.0.0.1", "::1", "localhost"]:
            is_safe, error_msg = True, None
        else:
            is_safe, error_msg = self._sanitize_request(
                request.url.path,
                dict(request.query_params)
            )
        
        if not is_safe:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Bad Request",
                    "message": "Request blocked by security policy",
                    "detail": error_msg
                }
            )
        
        # Step 3: Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Step 4: Global Exception Handling
            import traceback
            with open("swarm_v2_artifacts/sentinel_crash.log", "a") as f:
                f.write(f"\n--- CRASH AT {time.ctime()} ---\n")
                traceback.print_exc(file=f)
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred",
                    # Don't expose internal details in production
                }
            )
        
        # Step 5: Add security headers to response
        self._add_security_headers(response)
        
        return response


def create_sentinel_middleware(app, redis_client=None):
    """Factory function to create SentinelMiddleware with Redis."""
    return SentinelMiddleware(
        app=app,
        redis_client=redis_client or redis_client,
        rate_limit=100,
        rate_window=60
    )
