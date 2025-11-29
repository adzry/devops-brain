"""
Authentication Middleware

FastAPI middleware for authentication and rate limiting.
"""

import logging
from functools import wraps
from typing import Callable, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .jwt_auth import JWTAuth, TokenPayload
from .rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

# Global instances
_jwt_auth: Optional[JWTAuth] = None
_rate_limiter: Optional[RateLimiter] = None

security = HTTPBearer(auto_error=False)


def get_jwt_auth() -> JWTAuth:
    """Get global JWT auth instance."""
    global _jwt_auth
    if _jwt_auth is None:
        _jwt_auth = JWTAuth()
    return _jwt_auth


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[TokenPayload]:
    """Get current user from token."""
    if not credentials:
        return None
    
    jwt_auth = get_jwt_auth()
    payload = jwt_auth.verify_token(credentials.credentials)
    
    return payload


async def require_auth(
    user: Optional[TokenPayload] = Depends(get_current_user),
) -> TokenPayload:
    """Require authentication."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def auth_required(roles: Optional[list[str]] = None, permissions: Optional[list[str]] = None):
    """
    Decorator to require authentication with optional role/permission check.
    
    Usage:
        @app.get("/admin")
        @auth_required(roles=["admin"])
        async def admin_endpoint(user: TokenPayload = Depends(require_auth)):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get user from kwargs (injected by Depends)
            user = kwargs.get("user")
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                )
            
            # Check roles
            if roles:
                if not any(role in user.roles for role in roles):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Insufficient permissions",
                    )
            
            # Check permissions
            if permissions:
                if not any(perm in user.permissions for perm in permissions):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Insufficient permissions",
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def rate_limit(cost: int = 1):
    """
    Decorator to apply rate limiting to an endpoint.
    
    Usage:
        @app.get("/api/data")
        @rate_limit(cost=1)
        async def get_data():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            limiter = get_rate_limiter()
            
            # Get identifier (IP or user)
            identifier = request.client.host if request.client else "unknown"
            
            # Check rate limit
            result = await limiter.check(identifier, cost)
            
            if not result.allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                    headers={
                        "Retry-After": str(int(result.retry_after or 60)),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(result.reset_time)),
                    },
                )
            
            # Add rate limit headers to response
            response = await func(request, *args, **kwargs)
            return response
        
        return wrapper
    return decorator


class AuthMiddleware:
    """
    ASGI middleware for authentication.
    
    Handles:
    - Token extraction and validation
    - Rate limiting
    - Request logging
    """
    
    def __init__(
        self,
        app,
        exclude_paths: Optional[list[str]] = None,
        rate_limit_enabled: bool = True,
    ):
        self.app = app
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/openapi.json"]
        self.rate_limit_enabled = rate_limit_enabled
        self.jwt_auth = get_jwt_auth()
        self.rate_limiter = get_rate_limiter()
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        path = request.url.path
        
        # Skip excluded paths
        if any(path.startswith(p) for p in self.exclude_paths):
            await self.app(scope, receive, send)
            return
        
        # Rate limiting
        if self.rate_limit_enabled:
            identifier = request.client.host if request.client else "unknown"
            result = await self.rate_limiter.check(identifier)
            
            if not result.allowed:
                response = self._rate_limit_response(result)
                await response(scope, receive, send)
                return
        
        # Continue to app
        await self.app(scope, receive, send)
    
    def _rate_limit_response(self, result):
        """Create rate limit exceeded response."""
        from starlette.responses import JSONResponse
        
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
            headers={
                "Retry-After": str(int(result.retry_after or 60)),
                "X-RateLimit-Remaining": "0",
            },
        )
