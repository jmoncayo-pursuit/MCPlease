"""Ngrok tunneling integration for secure remote access."""

import asyncio
import json
import logging
import subprocess
import time
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import httpx
import os

logger = logging.getLogger(__name__)


@dataclass
class NgrokTunnel:
    """Ngrok tunnel information."""
    
    name: str
    public_url: str
    local_port: int
    protocol: str
    tunnel_id: str
    created_at: float


class NgrokManager:
    """Manager for ngrok tunnels."""
    
    def __init__(
        self,
        auth_token: Optional[str] = None,
        config_path: Optional[str] = None,
        region: str = "us"
    ):
        """Initialize ngrok manager.
        
        Args:
            auth_token: Ngrok auth token
            config_path: Path to ngrok config file
            region: Ngrok region (us, eu, ap, au, sa, jp, in)
        """
        self.auth_token = auth_token or os.getenv("NGROK_AUTH_TOKEN")
        self.config_path = config_path
        self.region = region
        self.tunnels: Dict[str, NgrokTunnel] = {}
        self._ngrok_process: Optional[subprocess.Popen] = None
        self._api_url = "http://localhost:4040/api"
        
        logger.info(f"Initialized ngrok manager (region: {region})")
    
    async def start_ngrok_agent(self) -> bool:
        """Start the ngrok agent process.
        
        Returns:
            True if started successfully
        """
        if self._ngrok_process and self._ngrok_process.poll() is None:
            logger.info("Ngrok agent already running")
            return True
        
        try:
            # Build ngrok command
            cmd = ["ngrok", "start", "--none"]
            
            if self.auth_token:
                cmd.extend(["--authtoken", self.auth_token])
            
            if self.config_path:
                cmd.extend(["--config", self.config_path])
            
            cmd.extend(["--region", self.region])
            
            # Start ngrok process
            logger.info("Starting ngrok agent")
            self._ngrok_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for ngrok to be ready
            max_wait = 30
            wait_time = 0
            while wait_time < max_wait:
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(f"{self._api_url}/tunnels")
                        if response.status_code == 200:
                            logger.info("Ngrok agent started successfully")
                            return True
                except:
                    pass
                
                await asyncio.sleep(1)
                wait_time += 1
            
            logger.error("Ngrok agent failed to start within timeout")
            return False
            
        except FileNotFoundError:
            logger.error("Ngrok binary not found. Please install ngrok.")
            return False
        except Exception as e:
            logger.error(f"Failed to start ngrok agent: {e}")
            return False
    
    async def stop_ngrok_agent(self) -> None:
        """Stop the ngrok agent process."""
        if self._ngrok_process:
            logger.info("Stopping ngrok agent")
            self._ngrok_process.terminate()
            try:
                self._ngrok_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._ngrok_process.kill()
                self._ngrok_process.wait()
            
            self._ngrok_process = None
            self.tunnels.clear()
            logger.info("Ngrok agent stopped")
    
    async def create_tunnel(
        self,
        name: str,
        port: int,
        protocol: str = "http",
        subdomain: Optional[str] = None,
        auth: Optional[str] = None,
        bind_tls: bool = True
    ) -> Optional[NgrokTunnel]:
        """Create a new ngrok tunnel.
        
        Args:
            name: Tunnel name
            port: Local port to tunnel
            protocol: Protocol (http, tcp)
            subdomain: Custom subdomain (requires paid plan)
            auth: Basic auth (username:password)
            bind_tls: Whether to bind TLS
            
        Returns:
            NgrokTunnel if created successfully
        """
        if not await self.start_ngrok_agent():
            return None
        
        try:
            # Build tunnel configuration
            tunnel_config = {
                "name": name,
                "addr": f"localhost:{port}",
                "proto": protocol,
                "bind_tls": bind_tls
            }
            
            if subdomain:
                tunnel_config["subdomain"] = subdomain
            
            if auth:
                tunnel_config["auth"] = auth
            
            # Create tunnel via API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self._api_url}/tunnels",
                    json=tunnel_config
                )
                
                if response.status_code == 201:
                    tunnel_data = response.json()
                    
                    tunnel = NgrokTunnel(
                        name=name,
                        public_url=tunnel_data["public_url"],
                        local_port=port,
                        protocol=protocol,
                        tunnel_id=tunnel_data["name"],
                        created_at=time.time()
                    )
                    
                    self.tunnels[name] = tunnel
                    logger.info(f"Created tunnel '{name}': {tunnel.public_url} -> localhost:{port}")
                    return tunnel
                else:
                    logger.error(f"Failed to create tunnel: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error creating tunnel '{name}': {e}")
            return None
    
    async def delete_tunnel(self, name: str) -> bool:
        """Delete a tunnel.
        
        Args:
            name: Tunnel name
            
        Returns:
            True if deleted successfully
        """
        if name not in self.tunnels:
            logger.warning(f"Tunnel '{name}' not found")
            return False
        
        try:
            tunnel = self.tunnels[name]
            
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self._api_url}/tunnels/{tunnel.tunnel_id}"
                )
                
                if response.status_code == 204:
                    del self.tunnels[name]
                    logger.info(f"Deleted tunnel '{name}'")
                    return True
                else:
                    logger.error(f"Failed to delete tunnel: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error deleting tunnel '{name}': {e}")
            return False
    
    async def list_tunnels(self) -> List[NgrokTunnel]:
        """List all active tunnels.
        
        Returns:
            List of active tunnels
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self._api_url}/tunnels")
                
                if response.status_code == 200:
                    data = response.json()
                    tunnels = []
                    
                    for tunnel_data in data.get("tunnels", []):
                        tunnel = NgrokTunnel(
                            name=tunnel_data["name"],
                            public_url=tunnel_data["public_url"],
                            local_port=int(tunnel_data["config"]["addr"].split(":")[-1]),
                            protocol=tunnel_data["proto"],
                            tunnel_id=tunnel_data["name"],
                            created_at=time.time()  # API doesn't provide creation time
                        )
                        tunnels.append(tunnel)
                    
                    return tunnels
                else:
                    logger.error(f"Failed to list tunnels: {response.text}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error listing tunnels: {e}")
            return []
    
    async def get_tunnel_status(self, name: str) -> Optional[Dict[str, Any]]:
        """Get tunnel status and metrics.
        
        Args:
            name: Tunnel name
            
        Returns:
            Tunnel status information
        """
        if name not in self.tunnels:
            return None
        
        try:
            tunnel = self.tunnels[name]
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self._api_url}/tunnels/{tunnel.tunnel_id}"
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Failed to get tunnel status: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting tunnel status: {e}")
            return None
    
    def get_tunnel_info(self, name: str) -> Optional[NgrokTunnel]:
        """Get tunnel information.
        
        Args:
            name: Tunnel name
            
        Returns:
            Tunnel information if found
        """
        return self.tunnels.get(name)
    
    async def setup_mcp_tunnels(
        self,
        sse_port: int = 8000,
        ws_port: int = 8001,
        subdomain_prefix: Optional[str] = None
    ) -> Dict[str, NgrokTunnel]:
        """Set up tunnels for MCP server endpoints.
        
        Args:
            sse_port: SSE transport port
            ws_port: WebSocket transport port
            subdomain_prefix: Prefix for custom subdomains
            
        Returns:
            Dictionary of created tunnels
        """
        tunnels = {}
        
        # Create SSE tunnel
        sse_subdomain = f"{subdomain_prefix}-sse" if subdomain_prefix else None
        sse_tunnel = await self.create_tunnel(
            name="mcp-sse",
            port=sse_port,
            protocol="http",
            subdomain=sse_subdomain,
            bind_tls=True
        )
        
        if sse_tunnel:
            tunnels["sse"] = sse_tunnel
        
        # Create WebSocket tunnel
        ws_subdomain = f"{subdomain_prefix}-ws" if subdomain_prefix else None
        ws_tunnel = await self.create_tunnel(
            name="mcp-websocket",
            port=ws_port,
            protocol="http",  # WebSocket over HTTP
            subdomain=ws_subdomain,
            bind_tls=True
        )
        
        if ws_tunnel:
            tunnels["websocket"] = ws_tunnel
        
        if tunnels:
            logger.info(f"Created {len(tunnels)} MCP tunnels")
            for transport, tunnel in tunnels.items():
                logger.info(f"  {transport}: {tunnel.public_url}")
        
        return tunnels
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on ngrok service.
        
        Returns:
            Health check results
        """
        health = {
            "ngrok_agent_running": False,
            "api_accessible": False,
            "tunnel_count": 0,
            "tunnels": []
        }
        
        try:
            # Check if ngrok process is running
            if self._ngrok_process and self._ngrok_process.poll() is None:
                health["ngrok_agent_running"] = True
            
            # Check API accessibility
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self._api_url}/tunnels")
                if response.status_code == 200:
                    health["api_accessible"] = True
                    
                    data = response.json()
                    tunnels = data.get("tunnels", [])
                    health["tunnel_count"] = len(tunnels)
                    health["tunnels"] = [
                        {
                            "name": t["name"],
                            "public_url": t["public_url"],
                            "proto": t["proto"]
                        }
                        for t in tunnels
                    ]
        
        except Exception as e:
            logger.debug(f"Ngrok health check error: {e}")
        
        return health


# Global ngrok manager instance
ngrok_manager = NgrokManager()


async def setup_pi_tunnels(
    sse_port: int = 8000,
    ws_port: int = 8001,
    auth_token: Optional[str] = None
) -> Dict[str, NgrokTunnel]:
    """Set up ngrok tunnels for Raspberry Pi deployment.
    
    Args:
        sse_port: SSE transport port
        ws_port: WebSocket transport port
        auth_token: Ngrok auth token
        
    Returns:
        Dictionary of created tunnels
    """
    if auth_token:
        ngrok_manager.auth_token = auth_token
    
    return await ngrok_manager.setup_mcp_tunnels(
        sse_port=sse_port,
        ws_port=ws_port,
        subdomain_prefix="mcplease-pi"
    )