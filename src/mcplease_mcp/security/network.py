"""Network security and multi-user support for MCP server."""

import asyncio
import ipaddress
import logging
import ssl
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional, List, Set, Union
import hashlib
import secrets

from .tls import TLSConfig, generate_self_signed_cert

logger = logging.getLogger(__name__)


@dataclass
class NetworkPolicy:
    """Network access policy configuration."""
    
    allowed_ips: Set[str] = field(default_factory=set)
    blocked_ips: Set[str] = field(default_factory=set)
    allowed_networks: Set[str] = field(default_factory=set)
    blocked_networks: Set[str] = field(default_factory=set)
    rate_limit_per_ip: int = 100  # requests per minute
    max_connections_per_ip: int = 10
    require_tls: bool = False
    allowed_ports: Set[int] = field(default_factory=lambda: {8000, 8001})


@dataclass
class UserSession:
    """Multi-user session tracking."""
    
    user_id: str
    session_id: str
    ip_address: str
    user_agent: str
    created_at: float
    last_activity: float
    request_count: int = 0
    connection_count: int = 0
    permissions: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)


class NetworkSecurityManager:
    """Network security and multi-user session manager."""
    
    def __init__(
        self,
        network_policy: Optional[NetworkPolicy] = None,
        tls_config: Optional[TLSConfig] = None,
        enable_rate_limiting: bool = True,
        enable_connection_limiting: bool = True,
        session_timeout_minutes: int = 60
    ):
        """Initialize network security manager.
        
        Args:
            network_policy: Network access policy
            tls_config: TLS configuration
            enable_rate_limiting: Whether to enable rate limiting
            enable_connection_limiting: Whether to enable connection limiting
            session_timeout_minutes: Session timeout in minutes
        """
        self.network_policy = network_policy or NetworkPolicy()
        self.tls_config = tls_config
        self.enable_rate_limiting = enable_rate_limiting
        self.enable_connection_limiting = enable_connection_limiting
        self.session_timeout_seconds = session_timeout_minutes * 60
        
        # Multi-user session tracking
        self.user_sessions: Dict[str, UserSession] = {}
        self.ip_sessions: Dict[str, List[str]] = {}  # IP -> list of session IDs
        self.session_lock = asyncio.Lock()
        
        # Rate limiting
        self.rate_limit_buckets: Dict[str, List[float]] = {}  # IP -> timestamps
        self.rate_limit_lock = asyncio.Lock()
        
        # Connection tracking
        self.active_connections: Dict[str, int] = {}  # IP -> connection count
        self.connection_lock = asyncio.Lock()
        
        # TLS context
        self.tls_context: Optional[ssl.SSLContext] = None
        if self.tls_config:
            self.tls_context = self.tls_config.create_context(ssl.Purpose.CLIENT_AUTH)
        
        # Cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        
        logger.info("Initialized network security manager")
    
    async def start(self) -> None:
        """Start the network security manager."""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Network security manager started")
    
    async def stop(self) -> None:
        """Stop the network security manager."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
        
        # Clear all tracking data
        async with self.session_lock:
            self.user_sessions.clear()
            self.ip_sessions.clear()
        
        async with self.rate_limit_lock:
            self.rate_limit_buckets.clear()
        
        async with self.connection_lock:
            self.active_connections.clear()
        
        logger.info("Network security manager stopped")
    
    async def validate_network_access(
        self, 
        client_ip: str, 
        port: int,
        protocol: str = "http"
    ) -> tuple[bool, Optional[str]]:
        """Validate network access for a client.
        
        Args:
            client_ip: Client IP address
            port: Target port
            protocol: Protocol (http, https, ws, wss)
            
        Returns:
            Tuple of (allowed, reason)
        """
        try:
            # Check if port is allowed
            if port not in self.network_policy.allowed_ports:
                return False, f"Port {port} not allowed"
            
            # Check TLS requirement
            if self.network_policy.require_tls and protocol in ["http", "ws"]:
                return False, "TLS required for this connection"
            
            # Check IP-based access control
            client_addr = ipaddress.ip_address(client_ip)
            
            # Check blocked IPs
            if client_ip in self.network_policy.blocked_ips:
                return False, f"IP {client_ip} is blocked"
            
            # Check blocked networks
            for blocked_network in self.network_policy.blocked_networks:
                if client_addr in ipaddress.ip_network(blocked_network, strict=False):
                    return False, f"IP {client_ip} is in blocked network {blocked_network}"
            
            # Check allowed IPs and networks (if specified)
            if self.network_policy.allowed_ips or self.network_policy.allowed_networks:
                allowed = False
                
                # Check allowed IPs
                if client_ip in self.network_policy.allowed_ips:
                    allowed = True
                
                # Check allowed networks
                if not allowed:
                    for allowed_network in self.network_policy.allowed_networks:
                        if client_addr in ipaddress.ip_network(allowed_network, strict=False):
                            allowed = True
                            break
                
                if not allowed:
                    return False, f"IP {client_ip} not in allowed list"
            
            return True, None
            
        except ValueError as e:
            return False, f"Invalid IP address: {e}"
        except Exception as e:
            logger.error(f"Error validating network access: {e}")
            return False, "Network validation error"
    
    async def check_rate_limit(self, client_ip: str) -> tuple[bool, Optional[str]]:
        """Check rate limit for a client IP.
        
        Args:
            client_ip: Client IP address
            
        Returns:
            Tuple of (allowed, reason)
        """
        if not self.enable_rate_limiting:
            return True, None
        
        async with self.rate_limit_lock:
            now = time.time()
            window_start = now - 60  # 1 minute window
            
            # Get or create bucket for this IP
            if client_ip not in self.rate_limit_buckets:
                self.rate_limit_buckets[client_ip] = []
            
            bucket = self.rate_limit_buckets[client_ip]
            
            # Remove old timestamps
            bucket[:] = [ts for ts in bucket if ts > window_start]
            
            # Check if rate limit exceeded
            if len(bucket) >= self.network_policy.rate_limit_per_ip:
                return False, f"Rate limit exceeded for IP {client_ip}"
            
            # Add current timestamp
            bucket.append(now)
            
            return True, None
    
    async def check_connection_limit(self, client_ip: str) -> tuple[bool, Optional[str]]:
        """Check connection limit for a client IP.
        
        Args:
            client_ip: Client IP address
            
        Returns:
            Tuple of (allowed, reason)
        """
        if not self.enable_connection_limiting:
            return True, None
        
        async with self.connection_lock:
            current_connections = self.active_connections.get(client_ip, 0)
            
            if current_connections >= self.network_policy.max_connections_per_ip:
                return False, f"Connection limit exceeded for IP {client_ip}"
            
            return True, None
    
    async def register_connection(self, client_ip: str) -> None:
        """Register a new connection from a client IP.
        
        Args:
            client_ip: Client IP address
        """
        async with self.connection_lock:
            self.active_connections[client_ip] = self.active_connections.get(client_ip, 0) + 1
            logger.debug(f"Registered connection from {client_ip} (total: {self.active_connections[client_ip]})")
    
    async def unregister_connection(self, client_ip: str) -> None:
        """Unregister a connection from a client IP.
        
        Args:
            client_ip: Client IP address
        """
        async with self.connection_lock:
            if client_ip in self.active_connections:
                self.active_connections[client_ip] -= 1
                if self.active_connections[client_ip] <= 0:
                    del self.active_connections[client_ip]
                logger.debug(f"Unregistered connection from {client_ip}")
    
    async def create_user_session(
        self,
        user_id: str,
        session_id: str,
        client_ip: str,
        user_agent: str = "",
        permissions: Optional[Set[str]] = None
    ) -> UserSession:
        """Create a new user session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            client_ip: Client IP address
            user_agent: User agent string
            permissions: User permissions
            
        Returns:
            Created user session
        """
        async with self.session_lock:
            session = UserSession(
                user_id=user_id,
                session_id=session_id,
                ip_address=client_ip,
                user_agent=user_agent,
                created_at=time.time(),
                last_activity=time.time(),
                permissions=permissions or set()
            )
            
            self.user_sessions[session_id] = session
            
            # Track sessions by IP
            if client_ip not in self.ip_sessions:
                self.ip_sessions[client_ip] = []
            self.ip_sessions[client_ip].append(session_id)
            
            logger.info(f"Created user session {session_id} for user {user_id} from {client_ip}")
            return session
    
    async def get_user_session(self, session_id: str) -> Optional[UserSession]:
        """Get a user session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            User session if found and valid
        """
        async with self.session_lock:
            session = self.user_sessions.get(session_id)
            
            if not session:
                return None
            
            # Check if session is expired
            if time.time() - session.last_activity > self.session_timeout_seconds:
                await self._remove_session(session_id)
                return None
            
            # Update last activity
            session.last_activity = time.time()
            return session
    
    async def update_session_activity(self, session_id: str) -> bool:
        """Update session activity timestamp.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was updated
        """
        async with self.session_lock:
            session = self.user_sessions.get(session_id)
            if session:
                session.last_activity = time.time()
                session.request_count += 1
                return True
            return False
    
    async def revoke_user_session(self, session_id: str) -> bool:
        """Revoke a user session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was revoked
        """
        async with self.session_lock:
            return await self._remove_session(session_id)
    
    async def revoke_user_sessions(self, user_id: str) -> int:
        """Revoke all sessions for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of sessions revoked
        """
        async with self.session_lock:
            sessions_to_remove = [
                session_id for session_id, session in self.user_sessions.items()
                if session.user_id == user_id
            ]
            
            for session_id in sessions_to_remove:
                await self._remove_session(session_id)
            
            logger.info(f"Revoked {len(sessions_to_remove)} sessions for user {user_id}")
            return len(sessions_to_remove)
    
    async def revoke_ip_sessions(self, client_ip: str) -> int:
        """Revoke all sessions from an IP address.
        
        Args:
            client_ip: Client IP address
            
        Returns:
            Number of sessions revoked
        """
        async with self.session_lock:
            sessions_to_remove = self.ip_sessions.get(client_ip, []).copy()
            
            for session_id in sessions_to_remove:
                await self._remove_session(session_id)
            
            logger.info(f"Revoked {len(sessions_to_remove)} sessions from IP {client_ip}")
            return len(sessions_to_remove)
    
    async def _remove_session(self, session_id: str) -> bool:
        """Remove a session (internal method, assumes lock is held).
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was removed
        """
        session = self.user_sessions.get(session_id)
        if not session:
            return False
        
        # Remove from user sessions
        del self.user_sessions[session_id]
        
        # Remove from IP sessions
        if session.ip_address in self.ip_sessions:
            try:
                self.ip_sessions[session.ip_address].remove(session_id)
                if not self.ip_sessions[session.ip_address]:
                    del self.ip_sessions[session.ip_address]
            except ValueError:
                pass  # Session ID not in list
        
        return True
    
    async def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics.
        
        Returns:
            Dictionary with security statistics
        """
        async with self.session_lock:
            total_sessions = len(self.user_sessions)
            unique_users = len(set(session.user_id for session in self.user_sessions.values()))
            unique_ips = len(self.ip_sessions)
        
        async with self.connection_lock:
            total_connections = sum(self.active_connections.values())
            unique_connection_ips = len(self.active_connections)
        
        return {
            "total_sessions": total_sessions,
            "unique_users": unique_users,
            "unique_session_ips": unique_ips,
            "total_connections": total_connections,
            "unique_connection_ips": unique_connection_ips,
            "rate_limiting_enabled": self.enable_rate_limiting,
            "connection_limiting_enabled": self.enable_connection_limiting,
            "tls_enabled": self.tls_context is not None,
            "session_timeout_minutes": self.session_timeout_seconds // 60,
            "network_policy": {
                "allowed_ips": len(self.network_policy.allowed_ips),
                "blocked_ips": len(self.network_policy.blocked_ips),
                "allowed_networks": len(self.network_policy.allowed_networks),
                "blocked_networks": len(self.network_policy.blocked_networks),
                "rate_limit_per_ip": self.network_policy.rate_limit_per_ip,
                "max_connections_per_ip": self.network_policy.max_connections_per_ip,
                "require_tls": self.network_policy.require_tls
            }
        }
    
    def get_tls_context(self) -> Optional[ssl.SSLContext]:
        """Get TLS context for secure connections.
        
        Returns:
            SSL context if TLS is configured
        """
        return self.tls_context
    
    async def setup_tls_certificates(
        self,
        cert_dir: Path,
        hostname: str = "localhost",
        force_regenerate: bool = False
    ) -> bool:
        """Set up TLS certificates for secure connections.
        
        Args:
            cert_dir: Directory to store certificates
            hostname: Hostname for certificate
            force_regenerate: Whether to regenerate existing certificates
            
        Returns:
            True if certificates were set up successfully
        """
        cert_dir = Path(cert_dir)
        cert_dir.mkdir(parents=True, exist_ok=True)
        
        cert_file = cert_dir / "server.crt"
        key_file = cert_dir / "server.key"
        
        # Generate certificates if they don't exist or force regeneration
        if force_regenerate or not cert_file.exists() or not key_file.exists():
            logger.info(f"Generating TLS certificates for {hostname}")
            
            if generate_self_signed_cert(str(cert_file), str(key_file), hostname):
                logger.info("TLS certificates generated successfully")
            else:
                logger.error("Failed to generate TLS certificates")
                return False
        
        # Update TLS configuration
        self.tls_config = TLSConfig(
            cert_file=str(cert_file),
            key_file=str(key_file),
            verify_mode=ssl.CERT_NONE,
            check_hostname=False
        )
        
        # Create TLS context
        self.tls_context = self.tls_config.create_context(ssl.Purpose.CLIENT_AUTH)
        
        if self.tls_context:
            logger.info("TLS context created successfully")
            return True
        else:
            logger.error("Failed to create TLS context")
            return False
    
    async def _cleanup_loop(self) -> None:
        """Background cleanup task for expired sessions and rate limit buckets."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                now = time.time()
                
                # Clean up expired sessions
                async with self.session_lock:
                    expired_sessions = [
                        session_id for session_id, session in self.user_sessions.items()
                        if now - session.last_activity > self.session_timeout_seconds
                    ]
                    
                    for session_id in expired_sessions:
                        await self._remove_session(session_id)
                    
                    if expired_sessions:
                        logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
                
                # Clean up old rate limit buckets
                async with self.rate_limit_lock:
                    window_start = now - 60  # 1 minute window
                    
                    for ip in list(self.rate_limit_buckets.keys()):
                        bucket = self.rate_limit_buckets[ip]
                        bucket[:] = [ts for ts in bucket if ts > window_start]
                        
                        # Remove empty buckets
                        if not bucket:
                            del self.rate_limit_buckets[ip]
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in network security cleanup: {e}")


def create_default_network_policy() -> NetworkPolicy:
    """Create a default network policy for development.
    
    Returns:
        Default network policy
    """
    return NetworkPolicy(
        allowed_networks={"127.0.0.0/8", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"},
        rate_limit_per_ip=100,
        max_connections_per_ip=10,
        require_tls=False,
        allowed_ports={8000, 8001, 4040}  # Include ngrok port
    )


def create_production_network_policy() -> NetworkPolicy:
    """Create a production network policy with stricter security.
    
    Returns:
        Production network policy
    """
    return NetworkPolicy(
        rate_limit_per_ip=50,
        max_connections_per_ip=5,
        require_tls=True,
        allowed_ports={8000, 8001}
    )