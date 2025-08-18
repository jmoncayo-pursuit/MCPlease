"""Security manager for MCP server with authentication and session management."""

import asyncio
import logging
import ssl
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field

from .auth import Authenticator, create_authenticator

logger = logging.getLogger(__name__)


@dataclass
class SecuritySession:
    """Security session information."""
    session_id: str
    user_info: Dict[str, Any]
    authenticated_at: float
    last_activity: float
    permissions: Set[str] = field(default_factory=set)
    client_info: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self, timeout_seconds: int) -> bool:
        """Check if session is expired."""
        return time.time() - self.last_activity > timeout_seconds
    
    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = time.time()


class MCPSecurityManager:
    """Security manager for MCP server with authentication and session isolation."""
    
    def __init__(
        self,
        auth_config: Optional[Dict[str, Any]] = None,
        session_timeout_minutes: int = 60,
        enable_tls: bool = False,
        tls_cert_path: Optional[str] = None,
        tls_key_path: Optional[str] = None,
        require_auth: bool = False
    ):
        """Initialize security manager.
        
        Args:
            auth_config: Authentication configuration
            session_timeout_minutes: Session timeout in minutes
            enable_tls: Whether to enable TLS/SSL
            tls_cert_path: Path to TLS certificate file
            tls_key_path: Path to TLS private key file
            require_auth: Whether authentication is required
        """
        self.session_timeout_seconds = session_timeout_minutes * 60
        self.enable_tls = enable_tls
        self.tls_cert_path = tls_cert_path
        self.tls_key_path = tls_key_path
        self.require_auth = require_auth
        
        # Session management
        self.active_sessions: Dict[str, SecuritySession] = {}
        self.session_lock = asyncio.Lock()
        
        # Authentication
        self.authenticators: List[Authenticator] = []
        self._setup_authenticators(auth_config or {})
        
        # TLS context
        self.tls_context: Optional[ssl.SSLContext] = None
        if self.enable_tls:
            self._setup_tls()
        
        # Cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        
        logger.info(f"Initialized security manager (TLS: {enable_tls}, Auth required: {require_auth})")
    
    def _setup_authenticators(self, auth_config: Dict[str, Any]) -> None:
        """Set up authenticators from configuration.
        
        Args:
            auth_config: Authentication configuration
        """
        # Default token authenticator if no config provided
        if not auth_config:
            if self.require_auth:
                self.authenticators.append(create_authenticator("token"))
                logger.info("Added default token authenticator")
            return
        
        # Set up configured authenticators
        for auth_type, config in auth_config.items():
            try:
                authenticator = create_authenticator(auth_type, **config)
                self.authenticators.append(authenticator)
                logger.info(f"Added {auth_type} authenticator")
            except Exception as e:
                logger.error(f"Failed to create {auth_type} authenticator: {e}")
    
    def _setup_tls(self) -> None:
        """Set up TLS/SSL context."""
        if not self.tls_cert_path or not self.tls_key_path:
            logger.warning("TLS enabled but certificate/key paths not provided")
            return
        
        try:
            self.tls_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            self.tls_context.load_cert_chain(self.tls_cert_path, self.tls_key_path)
            logger.info("TLS context configured successfully")
        except Exception as e:
            logger.error(f"Failed to setup TLS context: {e}")
            self.tls_context = None
    
    async def start(self) -> None:
        """Start the security manager."""
        # Start session cleanup task
        self._cleanup_task = asyncio.create_task(self._session_cleanup_loop())
        logger.info("Security manager started")
    
    async def stop(self) -> None:
        """Stop the security manager."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
        
        # Clear all sessions
        async with self.session_lock:
            self.active_sessions.clear()
        
        logger.info("Security manager stopped")
    
    async def authenticate_request(
        self, 
        credentials: Optional[Dict[str, Any]] = None,
        client_info: Optional[Dict[str, Any]] = None
    ) -> Optional[SecuritySession]:
        """Authenticate a request and create/update session.
        
        Args:
            credentials: Authentication credentials
            client_info: Client information
            
        Returns:
            Security session if authenticated, None otherwise
        """
        # If authentication not required, create anonymous session
        if not self.require_auth:
            import uuid
            session_id = f"anon_{uuid.uuid4().hex[:8]}_{int(time.time() * 1000)}"
            session = SecuritySession(
                session_id=session_id,
                user_info={"user_id": "anonymous", "username": "anonymous"},
                authenticated_at=time.time(),
                last_activity=time.time(),
                client_info=client_info or {}
            )
            
            async with self.session_lock:
                self.active_sessions[session_id] = session
            
            logger.debug(f"Created anonymous session: {session_id}")
            return session
        
        # Require credentials if authentication is required
        if not credentials:
            logger.debug("Authentication required but no credentials provided")
            return None
        
        # Try each authenticator
        for authenticator in self.authenticators:
            try:
                user_info = await authenticator.authenticate(credentials)
                if user_info:
                    # Create authenticated session
                    import uuid
                    session_id = f"auth_{user_info.get('user_id', 'unknown')}_{uuid.uuid4().hex[:8]}_{int(time.time() * 1000)}"
                    session = SecuritySession(
                        session_id=session_id,
                        user_info=user_info,
                        authenticated_at=time.time(),
                        last_activity=time.time(),
                        permissions=set(user_info.get("permissions", [])),
                        client_info=client_info or {}
                    )
                    
                    async with self.session_lock:
                        self.active_sessions[session_id] = session
                    
                    logger.info(f"Authenticated user {user_info.get('user_id')} with session {session_id}")
                    return session
                    
            except Exception as e:
                logger.warning(f"Authentication error with {type(authenticator).__name__}: {e}")
                continue
        
        logger.debug("Authentication failed with all authenticators")
        return None
    
    async def validate_session(self, session_id: str) -> Optional[SecuritySession]:
        """Validate and update an existing session.
        
        Args:
            session_id: Session ID to validate
            
        Returns:
            Security session if valid, None otherwise
        """
        async with self.session_lock:
            session = self.active_sessions.get(session_id)
            
            if not session:
                return None
            
            # Check if session is expired
            if session.is_expired(self.session_timeout_seconds):
                del self.active_sessions[session_id]
                logger.debug(f"Session {session_id} expired and removed")
                return None
            
            # Update activity
            session.update_activity()
            return session
    
    async def revoke_session(self, session_id: str) -> bool:
        """Revoke a session.
        
        Args:
            session_id: Session ID to revoke
            
        Returns:
            True if session was revoked, False if not found
        """
        async with self.session_lock:
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
                logger.info(f"Revoked session: {session_id}")
                return True
            return False
    
    async def check_permission(self, session_id: str, permission: str) -> bool:
        """Check if a session has a specific permission.
        
        Args:
            session_id: Session ID
            permission: Permission to check
            
        Returns:
            True if session has permission, False otherwise
        """
        session = await self.validate_session(session_id)
        if not session:
            return False
        
        # Anonymous sessions have basic permissions
        if not self.require_auth:
            return permission in ["read", "tools/call", "tools/list"]
        
        return permission in session.permissions
    
    def get_tls_context(self) -> Optional[ssl.SSLContext]:
        """Get TLS context for secure connections.
        
        Returns:
            SSL context if TLS is enabled, None otherwise
        """
        return self.tls_context
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics.
        
        Returns:
            Dictionary with session statistics
        """
        async with self.session_lock:
            total_sessions = len(self.active_sessions)
            authenticated_sessions = sum(
                1 for session in self.active_sessions.values()
                if session.user_info.get("user_id") != "anonymous"
            )
            
            return {
                "total_sessions": total_sessions,
                "authenticated_sessions": authenticated_sessions,
                "anonymous_sessions": total_sessions - authenticated_sessions,
                "session_timeout_minutes": self.session_timeout_seconds // 60,
                "tls_enabled": self.enable_tls,
                "auth_required": self.require_auth,
                "authenticator_count": len(self.authenticators)
            }
    
    async def _session_cleanup_loop(self) -> None:
        """Background task to clean up expired sessions."""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                async with self.session_lock:
                    expired_sessions = [
                        session_id for session_id, session in self.active_sessions.items()
                        if session.is_expired(self.session_timeout_seconds)
                    ]
                    
                    for session_id in expired_sessions:
                        del self.active_sessions[session_id]
                    
                    if expired_sessions:
                        logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in session cleanup: {e}")