# Firewall Configuration Guide

This guide provides firewall configuration recommendations for MCPlease MCP Server deployments.

## Overview

The MCPlease MCP Server uses the following ports by default:
- **8000**: SSE (Server-Sent Events) transport for HTTP-based MCP connections
- **8001**: WebSocket transport for real-time MCP connections
- **4040**: Ngrok web interface (when using ngrok tunneling)

## Port Management

### Required Ports

| Port | Protocol | Purpose | Required |
|------|----------|---------|----------|
| 8000 | HTTP/HTTPS | SSE transport | Yes |
| 8001 | HTTP/HTTPS/WS/WSS | WebSocket transport | Yes |
| 4040 | HTTP | Ngrok web interface | Optional |

### Optional Ports

- **22**: SSH (for remote management)
- **80/443**: HTTP/HTTPS (if using reverse proxy)

## Firewall Rules by Platform

### Ubuntu/Debian (ufw)

```bash
# Enable firewall
sudo ufw enable

# Allow SSH (if needed for remote management)
sudo ufw allow 22/tcp

# Allow MCP server ports
sudo ufw allow 8000/tcp comment "MCP SSE transport"
sudo ufw allow 8001/tcp comment "MCP WebSocket transport"

# Allow ngrok web interface (optional)
sudo ufw allow 4040/tcp comment "Ngrok web interface"

# Allow specific IP ranges (recommended)
sudo ufw allow from 192.168.0.0/16 to any port 8000
sudo ufw allow from 192.168.0.0/16 to any port 8001

# Check status
sudo ufw status verbose
```

### CentOS/RHEL/Fedora (firewalld)

```bash
# Start and enable firewalld
sudo systemctl start firewalld
sudo systemctl enable firewalld

# Add MCP server ports
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-port=8001/tcp

# Add ngrok port (optional)
sudo firewall-cmd --permanent --add-port=4040/tcp

# Allow specific networks (recommended)
sudo firewall-cmd --permanent --add-rich-rule="rule family='ipv4' source address='192.168.0.0/16' port protocol='tcp' port='8000' accept"
sudo firewall-cmd --permanent --add-rich-rule="rule family='ipv4' source address='192.168.0.0/16' port protocol='tcp' port='8001' accept"

# Reload configuration
sudo firewall-cmd --reload

# Check status
sudo firewall-cmd --list-all
```

### Raspberry Pi (iptables)

```bash
# Allow MCP server ports
sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8001 -j ACCEPT

# Allow from specific networks only (recommended)
sudo iptables -A INPUT -s 192.168.0.0/16 -p tcp --dport 8000 -j ACCEPT
sudo iptables -A INPUT -s 192.168.0.0/16 -p tcp --dport 8001 -j ACCEPT

# Allow ngrok port (optional)
sudo iptables -A INPUT -p tcp --dport 4040 -j ACCEPT

# Save rules (Debian/Ubuntu)
sudo iptables-save > /etc/iptables/rules.v4

# Save rules (CentOS/RHEL)
sudo service iptables save
```

## Network Security Policies

### Development Environment

For development environments, use a permissive policy:

```python
from mcplease_mcp.security.network import create_default_network_policy

# Allow local networks
policy = create_default_network_policy()
```

This allows:
- Local networks (127.0.0.0/8, 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12)
- 100 requests per minute per IP
- 10 concurrent connections per IP
- No TLS requirement

### Production Environment

For production environments, use a restrictive policy:

```python
from mcplease_mcp.security.network import create_production_network_policy

# Strict security
policy = create_production_network_policy()
```

This enforces:
- 50 requests per minute per IP
- 5 concurrent connections per IP
- TLS required
- Only specified IPs/networks allowed

### Custom Network Policy

```python
from mcplease_mcp.security.network import NetworkPolicy

policy = NetworkPolicy(
    # Allow specific IPs
    allowed_ips={"192.168.1.100", "10.0.0.50"},
    
    # Block specific IPs
    blocked_ips={"192.168.1.200"},
    
    # Allow specific networks
    allowed_networks={"192.168.1.0/24", "10.0.0.0/8"},
    
    # Block specific networks
    blocked_networks={"172.16.0.0/12"},
    
    # Rate limiting
    rate_limit_per_ip=30,  # requests per minute
    max_connections_per_ip=3,
    
    # Security requirements
    require_tls=True,
    allowed_ports={8000, 8001}
)
```

## Cloud Provider Configurations

### AWS Security Groups

```json
{
  "GroupName": "mcplease-mcp-server",
  "Description": "Security group for MCPlease MCP Server",
  "SecurityGroupRules": [
    {
      "IpProtocol": "tcp",
      "FromPort": 8000,
      "ToPort": 8000,
      "CidrIp": "10.0.0.0/8",
      "Description": "MCP SSE transport from VPC"
    },
    {
      "IpProtocol": "tcp",
      "FromPort": 8001,
      "ToPort": 8001,
      "CidrIp": "10.0.0.0/8",
      "Description": "MCP WebSocket transport from VPC"
    }
  ]
}
```

### Google Cloud Firewall Rules

```bash
# Create firewall rule for MCP server
gcloud compute firewall-rules create mcplease-mcp-server \
    --allow tcp:8000,tcp:8001 \
    --source-ranges 10.0.0.0/8 \
    --description "Allow MCP server traffic from internal network"
```

### Azure Network Security Group

```json
{
  "securityRules": [
    {
      "name": "AllowMCPSSE",
      "properties": {
        "protocol": "Tcp",
        "sourcePortRange": "*",
        "destinationPortRange": "8000",
        "sourceAddressPrefix": "10.0.0.0/8",
        "destinationAddressPrefix": "*",
        "access": "Allow",
        "priority": 1000,
        "direction": "Inbound"
      }
    },
    {
      "name": "AllowMCPWebSocket",
      "properties": {
        "protocol": "Tcp",
        "sourcePortRange": "*",
        "destinationPortRange": "8001",
        "sourceAddressPrefix": "10.0.0.0/8",
        "destinationAddressPrefix": "*",
        "access": "Allow",
        "priority": 1001,
        "direction": "Inbound"
      }
    }
  ]
}
```

## Docker Network Configuration

### Docker Compose with Network Isolation

```yaml
version: '3.8'

services:
  mcplease-mcp:
    image: mcplease/mcp-server:latest
    ports:
      - "127.0.0.1:8000:8000"  # Bind to localhost only
      - "127.0.0.1:8001:8001"
    networks:
      - mcp_internal
    environment:
      - MCP_NETWORK_POLICY=production

networks:
  mcp_internal:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### Docker with Custom Network Policy

```bash
# Run with restricted network access
docker run -d \
  --name mcplease-mcp \
  -p 127.0.0.1:8000:8000 \
  -p 127.0.0.1:8001:8001 \
  -e MCP_ALLOWED_NETWORKS="192.168.1.0/24,10.0.0.0/8" \
  -e MCP_RATE_LIMIT_PER_IP=50 \
  -e MCP_MAX_CONNECTIONS_PER_IP=5 \
  -e MCP_REQUIRE_TLS=true \
  mcplease/mcp-server:latest
```

## Monitoring and Logging

### Enable Connection Logging

```python
import logging

# Configure logging for network security
logging.getLogger('mcplease_mcp.security.network').setLevel(logging.INFO)
```

### Monitor Security Events

The server provides security statistics via the health endpoint:

```bash
curl http://localhost:8000/health | jq '.components.network_security_manager'
```

Example response:
```json
{
  "status": "healthy",
  "stats": {
    "total_sessions": 5,
    "unique_users": 3,
    "unique_session_ips": 2,
    "total_connections": 8,
    "unique_connection_ips": 3,
    "rate_limiting_enabled": true,
    "connection_limiting_enabled": true,
    "tls_enabled": true,
    "session_timeout_minutes": 60,
    "network_policy": {
      "allowed_ips": 2,
      "blocked_ips": 1,
      "allowed_networks": 3,
      "blocked_networks": 0,
      "rate_limit_per_ip": 50,
      "max_connections_per_ip": 5,
      "require_tls": true
    }
  }
}
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Check if firewall is blocking the ports
   - Verify the server is listening on the correct interface
   - Check network policy configuration

2. **Rate Limited**
   - Increase rate limit in network policy
   - Check if multiple clients are sharing the same IP
   - Monitor rate limit statistics

3. **TLS Errors**
   - Verify TLS certificates are valid
   - Check if client supports the required TLS version
   - Ensure TLS is properly configured

### Debug Commands

```bash
# Check if ports are open
netstat -tlnp | grep -E ':(8000|8001)'

# Test connectivity
telnet localhost 8000
curl -v http://localhost:8000/health

# Check firewall status
sudo ufw status verbose  # Ubuntu
sudo firewall-cmd --list-all  # CentOS/RHEL

# Monitor connections
ss -tuln | grep -E ':(8000|8001)'
```

## Security Best Practices

1. **Principle of Least Privilege**
   - Only allow necessary IPs and networks
   - Use restrictive rate limits
   - Enable TLS for production

2. **Network Segmentation**
   - Use VPNs for remote access
   - Isolate MCP server in private networks
   - Use reverse proxies for external access

3. **Monitoring and Alerting**
   - Monitor connection patterns
   - Set up alerts for rate limit violations
   - Log security events

4. **Regular Updates**
   - Keep firewall rules updated
   - Review network policies regularly
   - Update security configurations

5. **Defense in Depth**
   - Combine firewall rules with application-level security
   - Use multiple layers of protection
   - Implement proper authentication and authorization