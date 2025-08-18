"""TLS/SSL configuration utilities for MCP server."""

import ssl
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TLSConfig:
    """TLS configuration for secure connections."""
    
    cert_file: Optional[str] = None
    key_file: Optional[str] = None
    ca_file: Optional[str] = None
    verify_mode: ssl.VerifyMode = ssl.CERT_NONE
    check_hostname: bool = False
    ciphers: Optional[str] = None
    
    def create_context(self, purpose: ssl.Purpose = ssl.Purpose.SERVER_AUTH) -> Optional[ssl.SSLContext]:
        """Create SSL context from configuration.
        
        Args:
            purpose: SSL purpose (SERVER_AUTH or CLIENT_AUTH)
            
        Returns:
            SSL context if configuration is valid, None otherwise
        """
        if not self.cert_file or not self.key_file:
            logger.warning("TLS cert_file and key_file are required")
            return None
        
        try:
            # Create SSL context
            context = ssl.create_default_context(purpose)
            
            # Load certificate and key
            cert_path = Path(self.cert_file)
            key_path = Path(self.key_file)
            
            if not cert_path.exists():
                logger.error(f"Certificate file not found: {self.cert_file}")
                return None
            
            if not key_path.exists():
                logger.error(f"Key file not found: {self.key_file}")
                return None
            
            context.load_cert_chain(str(cert_path), str(key_path))
            
            # Configure verification
            context.verify_mode = self.verify_mode
            context.check_hostname = self.check_hostname
            
            # Load CA certificates if provided
            if self.ca_file:
                ca_path = Path(self.ca_file)
                if ca_path.exists():
                    context.load_verify_locations(str(ca_path))
                else:
                    logger.warning(f"CA file not found: {self.ca_file}")
            
            # Set ciphers if provided
            if self.ciphers:
                context.set_ciphers(self.ciphers)
            
            logger.info("TLS context created successfully")
            return context
            
        except Exception as e:
            logger.error(f"Failed to create TLS context: {e}")
            return None
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "TLSConfig":
        """Create TLS config from dictionary.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            TLS configuration instance
        """
        verify_mode_map = {
            "none": ssl.CERT_NONE,
            "optional": ssl.CERT_OPTIONAL,
            "required": ssl.CERT_REQUIRED
        }
        
        verify_mode = verify_mode_map.get(
            config.get("verify_mode", "none").lower(),
            ssl.CERT_NONE
        )
        
        return cls(
            cert_file=config.get("cert_file"),
            key_file=config.get("key_file"),
            ca_file=config.get("ca_file"),
            verify_mode=verify_mode,
            check_hostname=config.get("check_hostname", False),
            ciphers=config.get("ciphers")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert TLS config to dictionary.
        
        Returns:
            Configuration dictionary
        """
        verify_mode_map = {
            ssl.CERT_NONE: "none",
            ssl.CERT_OPTIONAL: "optional",
            ssl.CERT_REQUIRED: "required"
        }
        
        return {
            "cert_file": self.cert_file,
            "key_file": self.key_file,
            "ca_file": self.ca_file,
            "verify_mode": verify_mode_map.get(self.verify_mode, "none"),
            "check_hostname": self.check_hostname,
            "ciphers": self.ciphers
        }


def generate_self_signed_cert(
    cert_file: str,
    key_file: str,
    hostname: str = "localhost",
    days: int = 365
) -> bool:
    """Generate a self-signed certificate for testing.
    
    Args:
        cert_file: Path to save certificate
        key_file: Path to save private key
        hostname: Hostname for certificate
        days: Certificate validity in days
        
    Returns:
        True if certificate was generated successfully
    """
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from datetime import datetime, timedelta
        import ipaddress
        
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        
        # Create certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "MCPlease MCP Server"),
            x509.NameAttribute(NameOID.COMMON_NAME, hostname),
        ])
        
        # Add subject alternative names
        san_list = [x509.DNSName(hostname)]
        if hostname == "localhost":
            san_list.extend([
                x509.DNSName("127.0.0.1"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                x509.IPAddress(ipaddress.IPv6Address("::1"))
            ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=days)
        ).add_extension(
            x509.SubjectAlternativeName(san_list),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        
        # Write certificate
        with open(cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        # Write private key
        with open(key_file, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        logger.info(f"Generated self-signed certificate: {cert_file}")
        return True
        
    except ImportError:
        logger.error("cryptography library required for certificate generation")
        return False
    except Exception as e:
        logger.error(f"Failed to generate self-signed certificate: {e}")
        return False