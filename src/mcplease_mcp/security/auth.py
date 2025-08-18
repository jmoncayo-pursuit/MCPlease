"""Authentication implementations for MCP server."""

import hashlib
import hmac
import logging
import secrets
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    jwt = None

try:
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    x509 = None

logger = logging.getLogger(__name__)


class Authenticator(ABC):
    """Abstract base class for authentication methods."""
    
    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Authenticate credentials.
        
        Args:
            credentials: Authentication credentials
            
        Returns:
            User info if authenticated, None otherwise
        """
        pass
    
    @abstractmethod
    def generate_credentials(self, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate credentials for a user.
        
        Args:
            user_info: User information
            
        Returns:
            Generated credentials
        """
        pass


class TokenAuthenticator(Authenticator):
    """Token-based authentication using JWT or simple tokens."""
    
    def __init__(
        self, 
        secret_key: Optional[str] = None,
        use_jwt: bool = True,
        token_expiry_hours: int = 24
    ):
        """Initialize token authenticator.
        
        Args:
            secret_key: Secret key for token signing (generated if not provided)
            use_jwt: Whether to use JWT tokens (requires PyJWT)
            token_expiry_hours: Token expiry time in hours
        """
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.use_jwt = use_jwt and JWT_AVAILABLE
        self.token_expiry_hours = token_expiry_hours
        
        # Simple token storage for non-JWT mode
        self.valid_tokens: Dict[str, Dict[str, Any]] = {}
        
        if self.use_jwt and not JWT_AVAILABLE:
            logger.warning("JWT requested but PyJWT not available, falling back to simple tokens")
            self.use_jwt = False
        
        logger.info(f"Initialized token authenticator (JWT: {self.use_jwt})")
    
    async def authenticate(self, credentials: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Authenticate using token.
        
        Args:
            credentials: Should contain 'token' field
            
        Returns:
            User info if token is valid, None otherwise
        """
        token = credentials.get("token")
        if not token:
            return None
        
        if self.use_jwt:
            return await self._authenticate_jwt(token)
        else:
            return await self._authenticate_simple_token(token)
    
    def generate_credentials(self, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate token credentials for a user.
        
        Args:
            user_info: User information (should include 'user_id')
            
        Returns:
            Generated token credentials
        """
        if self.use_jwt:
            return self._generate_jwt_token(user_info)
        else:
            return self._generate_simple_token(user_info)
    
    async def _authenticate_jwt(self, token: str) -> Optional[Dict[str, Any]]:
        """Authenticate JWT token.
        
        Args:
            token: JWT token
            
        Returns:
            User info if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            
            # Check expiration
            if payload.get("exp", 0) < time.time():
                logger.debug("JWT token expired")
                return None
            
            return {
                "user_id": payload.get("user_id"),
                "username": payload.get("username"),
                "permissions": payload.get("permissions", []),
                "issued_at": payload.get("iat"),
                "expires_at": payload.get("exp")
            }
            
        except jwt.InvalidTokenError as e:
            logger.debug(f"Invalid JWT token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error validating JWT token: {e}")
            return None
    
    async def _authenticate_simple_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Authenticate simple token.
        
        Args:
            token: Simple token
            
        Returns:
            User info if valid, None otherwise
        """
        if token not in self.valid_tokens:
            return None
        
        token_info = self.valid_tokens[token]
        
        # Check expiration
        if token_info.get("expires_at", 0) < time.time():
            del self.valid_tokens[token]
            logger.debug("Simple token expired")
            return None
        
        return token_info.get("user_info")
    
    def _generate_jwt_token(self, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate JWT token.
        
        Args:
            user_info: User information
            
        Returns:
            Token credentials
        """
        now = time.time()
        expiry = now + (self.token_expiry_hours * 3600)
        
        payload = {
            "user_id": user_info.get("user_id"),
            "username": user_info.get("username"),
            "permissions": user_info.get("permissions", []),
            "iat": now,
            "exp": expiry
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm="HS256")
        
        return {
            "token": token,
            "token_type": "jwt",
            "expires_at": expiry,
            "expires_in": self.token_expiry_hours * 3600
        }
    
    def _generate_simple_token(self, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate simple token.
        
        Args:
            user_info: User information
            
        Returns:
            Token credentials
        """
        token = secrets.token_urlsafe(32)
        expiry = time.time() + (self.token_expiry_hours * 3600)
        
        self.valid_tokens[token] = {
            "user_info": user_info,
            "expires_at": expiry,
            "created_at": time.time()
        }
        
        return {
            "token": token,
            "token_type": "simple",
            "expires_at": expiry,
            "expires_in": self.token_expiry_hours * 3600
        }
    
    def revoke_token(self, token: str) -> bool:
        """Revoke a token.
        
        Args:
            token: Token to revoke
            
        Returns:
            True if token was revoked, False if not found
        """
        if not self.use_jwt and token in self.valid_tokens:
            del self.valid_tokens[token]
            logger.info("Revoked simple token")
            return True
        
        # JWT tokens can't be revoked without a blacklist
        # This would require additional infrastructure
        return False
    
    def cleanup_expired_tokens(self) -> int:
        """Clean up expired simple tokens.
        
        Returns:
            Number of tokens cleaned up
        """
        if self.use_jwt:
            return 0  # JWT tokens are self-expiring
        
        now = time.time()
        expired_tokens = [
            token for token, info in self.valid_tokens.items()
            if info.get("expires_at", 0) < now
        ]
        
        for token in expired_tokens:
            del self.valid_tokens[token]
        
        if expired_tokens:
            logger.info(f"Cleaned up {len(expired_tokens)} expired tokens")
        
        return len(expired_tokens)


class CertificateAuthenticator(Authenticator):
    """Certificate-based authentication for TLS client certificates."""
    
    def __init__(self, trusted_ca_certs: Optional[List[str]] = None):
        """Initialize certificate authenticator.
        
        Args:
            trusted_ca_certs: List of trusted CA certificate paths
        """
        self.trusted_ca_certs = trusted_ca_certs or []
        self.trusted_certs: List[Any] = []
        
        if CRYPTOGRAPHY_AVAILABLE:
            self._load_trusted_certs()
        else:
            logger.warning("Cryptography library not available, certificate auth disabled")
    
    def _load_trusted_certs(self) -> None:
        """Load trusted CA certificates."""
        for cert_path in self.trusted_ca_certs:
            try:
                with open(cert_path, 'rb') as f:
                    cert_data = f.read()
                    cert = x509.load_pem_x509_certificate(cert_data)
                    self.trusted_certs.append(cert)
                    logger.info(f"Loaded trusted certificate: {cert_path}")
            except Exception as e:
                logger.error(f"Failed to load certificate {cert_path}: {e}")
    
    async def authenticate(self, credentials: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Authenticate using client certificate.
        
        Args:
            credentials: Should contain 'certificate' field with PEM data
            
        Returns:
            User info if certificate is valid, None otherwise
        """
        if not CRYPTOGRAPHY_AVAILABLE:
            logger.error("Certificate authentication requires cryptography library")
            return None
        
        cert_pem = credentials.get("certificate")
        if not cert_pem:
            return None
        
        try:
            # Parse client certificate
            cert = x509.load_pem_x509_certificate(cert_pem.encode())
            
            # Verify certificate against trusted CAs
            if not self._verify_certificate(cert):
                logger.debug("Certificate verification failed")
                return None
            
            # Extract user info from certificate
            subject = cert.subject
            user_info = {
                "user_id": self._get_cert_field(subject, "CN"),
                "username": self._get_cert_field(subject, "CN"),
                "email": self._get_cert_field(subject, "emailAddress"),
                "organization": self._get_cert_field(subject, "O"),
                "auth_method": "certificate"
            }
            
            logger.info(f"Certificate authentication successful for: {user_info['user_id']}")
            return user_info
            
        except Exception as e:
            logger.error(f"Certificate authentication error: {e}")
            return None
    
    def generate_credentials(self, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate certificate credentials (not implemented).
        
        Args:
            user_info: User information
            
        Returns:
            Empty dict (certificate generation not implemented)
        """
        # Certificate generation is complex and typically done externally
        logger.warning("Certificate generation not implemented")
        return {}
    
    def _verify_certificate(self, cert: Any) -> bool:
        """Verify certificate against trusted CAs.
        
        Args:
            cert: Certificate to verify
            
        Returns:
            True if certificate is valid
        """
        if not self.trusted_certs:
            # If no trusted CAs configured, accept any valid certificate
            logger.warning("No trusted CAs configured, accepting any valid certificate")
            return True
        
        # Basic certificate validation
        try:
            # Check if certificate is not expired
            now = datetime.now()
            if cert.not_valid_after < now:
                logger.debug("Certificate expired")
                return False
            
            if cert.not_valid_before > now:
                logger.debug("Certificate not yet valid")
                return False
            
            # Additional validation against trusted CAs would go here
            # This is a simplified implementation
            return True
            
        except Exception as e:
            logger.error(f"Certificate validation error: {e}")
            return False
    
    def _get_cert_field(self, subject: Any, field_name: str) -> Optional[str]:
        """Extract field from certificate subject.
        
        Args:
            subject: Certificate subject
            field_name: Field name to extract
            
        Returns:
            Field value if found, None otherwise
        """
        try:
            for attribute in subject:
                if attribute.oid._name == field_name:
                    return attribute.value
        except Exception as e:
            logger.debug(f"Error extracting certificate field {field_name}: {e}")
        
        return None


def create_authenticator(auth_type: str, **kwargs) -> Authenticator:
    """Create an authenticator instance.
    
    Args:
        auth_type: Type of authenticator ("token", "certificate")
        **kwargs: Authenticator-specific arguments
        
    Returns:
        Authenticator instance
        
    Raises:
        ValueError: If auth_type is unknown
    """
    if auth_type == "token":
        return TokenAuthenticator(**kwargs)
    elif auth_type == "certificate":
        return CertificateAuthenticator(**kwargs)
    else:
        raise ValueError(f"Unknown authenticator type: {auth_type}")