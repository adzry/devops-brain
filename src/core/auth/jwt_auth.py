"""
JWT Authentication

JSON Web Token based authentication.
"""

import os
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional

import jwt


@dataclass
class JWTConfig:
    """JWT configuration."""
    secret_key: str = field(default_factory=lambda: os.environ.get("JWT_SECRET", secrets.token_hex(32)))
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    issuer: str = "devops-brain"
    audience: str = "devops-brain-api"


@dataclass
class TokenPayload:
    """JWT token payload."""
    sub: str  # Subject (user ID)
    exp: datetime  # Expiration
    iat: datetime  # Issued at
    jti: str  # JWT ID
    iss: str  # Issuer
    aud: str  # Audience
    type: str  # Token type (access/refresh)
    roles: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class JWTAuth:
    """
    JWT authentication handler.
    
    Features:
    - Access and refresh tokens
    - Role-based access control
    - Token blacklisting
    - Automatic refresh
    """
    
    def __init__(self, config: Optional[JWTConfig] = None):
        self.config = config or JWTConfig()
        self._blacklist: set[str] = set()
    
    def create_access_token(
        self,
        user_id: str,
        roles: Optional[list[str]] = None,
        permissions: Optional[list[str]] = None,
        **extra_claims,
    ) -> str:
        """Create an access token."""
        now = datetime.utcnow()
        expires = now + timedelta(minutes=self.config.access_token_expire_minutes)
        
        payload = {
            "sub": user_id,
            "exp": expires,
            "iat": now,
            "jti": secrets.token_hex(16),
            "iss": self.config.issuer,
            "aud": self.config.audience,
            "type": "access",
            "roles": roles or [],
            "permissions": permissions or [],
            **extra_claims,
        }
        
        return jwt.encode(payload, self.config.secret_key, algorithm=self.config.algorithm)
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create a refresh token."""
        now = datetime.utcnow()
        expires = now + timedelta(days=self.config.refresh_token_expire_days)
        
        payload = {
            "sub": user_id,
            "exp": expires,
            "iat": now,
            "jti": secrets.token_hex(16),
            "iss": self.config.issuer,
            "aud": self.config.audience,
            "type": "refresh",
        }
        
        return jwt.encode(payload, self.config.secret_key, algorithm=self.config.algorithm)
    
    def verify_token(self, token: str) -> Optional[TokenPayload]:
        """Verify and decode a token."""
        try:
            payload = jwt.decode(
                token,
                self.config.secret_key,
                algorithms=[self.config.algorithm],
                audience=self.config.audience,
                issuer=self.config.issuer,
            )
            
            # Check blacklist
            if payload.get("jti") in self._blacklist:
                return None
            
            return TokenPayload(
                sub=payload["sub"],
                exp=datetime.fromisoformat(payload["exp"]) if isinstance(payload["exp"], str) else datetime.utcfromtimestamp(payload["exp"]),
                iat=datetime.fromisoformat(payload["iat"]) if isinstance(payload["iat"], str) else datetime.utcfromtimestamp(payload["iat"]),
                jti=payload["jti"],
                iss=payload["iss"],
                aud=payload["aud"],
                type=payload["type"],
                roles=payload.get("roles", []),
                permissions=payload.get("permissions", []),
                metadata=payload.get("metadata", {}),
            )
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[tuple[str, str]]:
        """Refresh an access token using a refresh token."""
        payload = self.verify_token(refresh_token)
        
        if not payload or payload.type != "refresh":
            return None
        
        # Blacklist old refresh token
        self._blacklist.add(payload.jti)
        
        # Create new tokens
        access_token = self.create_access_token(payload.sub)
        new_refresh_token = self.create_refresh_token(payload.sub)
        
        return access_token, new_refresh_token
    
    def revoke_token(self, token: str) -> bool:
        """Revoke a token by adding to blacklist."""
        payload = self.verify_token(token)
        if payload:
            self._blacklist.add(payload.jti)
            return True
        return False
    
    def has_role(self, token: str, role: str) -> bool:
        """Check if token has a specific role."""
        payload = self.verify_token(token)
        return payload is not None and role in payload.roles
    
    def has_permission(self, token: str, permission: str) -> bool:
        """Check if token has a specific permission."""
        payload = self.verify_token(token)
        return payload is not None and permission in payload.permissions
    
    def create_api_key(
        self,
        name: str,
        permissions: Optional[list[str]] = None,
        expires_days: int = 365,
    ) -> str:
        """Create a long-lived API key."""
        now = datetime.utcnow()
        expires = now + timedelta(days=expires_days)
        
        payload = {
            "sub": f"api_key:{name}",
            "exp": expires,
            "iat": now,
            "jti": secrets.token_hex(16),
            "iss": self.config.issuer,
            "aud": self.config.audience,
            "type": "api_key",
            "permissions": permissions or ["read"],
        }
        
        return jwt.encode(payload, self.config.secret_key, algorithm=self.config.algorithm)
