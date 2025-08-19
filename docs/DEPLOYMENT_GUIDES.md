# MCPlease MCP Server - Deployment Guides

**Complete deployment guides for all deployment scenarios**

**Version**: 1.0.0  
**Last Updated**: January 18, 2025  
**Supported Platforms**: x86_64, ARM64, Raspberry Pi

---

## Table of Contents

1. [Local Development](#local-development)
2. [Remote Server Deployment](#remote-server-deployment)
3. [Raspberry Pi Deployment](#raspberry-pi-deployment)
4. [Docker Deployment](#docker-deployment)
5. [Production Deployment](#production-deployment)
6. [Monitoring & Maintenance](#monitoring--maintenance)

---

## Local Development

### Prerequisites

- **Python**: 3.9+ (3.11+ recommended)
- **Package Manager**: uv (recommended) or pip
- **IDE**: VSCode with Continue.dev extension or Cursor IDE

### Quick Setup

```bash
# Clone repository
git clone https://github.com/jmoncayo-pursuit/MCPlease.git
cd MCPlease

# Install dependencies with uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # or restart terminal
uv sync --frozen

# Start development server
uv run python -m mcplease_mcp.main --transport stdio
```

### IDE Configuration

#### VSCode + Continue.dev

1. **Install Continue.dev Extension**
   ```bash
   code --install-extension continue.continue
   ```

2. **Auto-configure MCP Server**
   ```bash
   # The server automatically creates VSCode configuration
   # Check .vscode/mcp.json for configuration details
   ```

3. **Test Integration**
   - Restart VSCode
   - Press `Ctrl+I` to open Continue chat
   - Ask for code completion or explanation

#### Cursor IDE

1. **Enable MCP Support**
   - Cursor has built-in MCP support
   - No additional configuration needed

2. **Test Integration**
   - Use AI-powered coding features
   - Test code completion and explanation

### Development Commands

```bash
# Run tests
uv run pytest tests/ -v

# Run specific test suites
uv run pytest tests/test_protocol_handler.py -v
uv run pytest tests/test_ai_tools.py -v

# Start with debugging
uv run python -m mcplease_mcp.main --transport stdio --debug

# Check server health
curl http://localhost:8000/health
```

---

## Remote Server Deployment

### Server Requirements

- **OS**: Ubuntu 20.04+, CentOS 8+, or similar
- **Python**: 3.9+
- **Memory**: 16GB+ (8GB minimum)
- **Storage**: 50GB+ (for AI models)
- **Network**: Public IP or VPN access

### Installation Steps

```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install Python and dependencies
sudo apt install -y python3.11 python3.11-venv python3.11-dev
sudo apt install -y build-essential git curl

# 3. Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# 4. Clone and setup
git clone https://github.com/jmoncayo-pursuit/MCPlease.git
cd MCPlease
uv sync --frozen

# 5. Create systemd service
sudo tee /etc/systemd/system/mcplease-mcp.service > /dev/null <<EOF
[Unit]
Description=MCPlease MCP Server
After=network.target

[Service]
Type=simple
User=mcplease
WorkingDirectory=/home/mcplease/MCPlease
Environment=PATH=/home/mcplease/.cargo/bin:/usr/bin:/bin
ExecStart=/home/mcplease/.cargo/bin/uv run python -m mcplease_mcp.main --transport sse --port 8000 --transport websocket --port 8001 --enable-tls --require-auth
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 6. Create user and set permissions
sudo useradd -m -s /bin/bash mcplease
sudo chown -R mcplease:mcplease /home/mcplease/MCPlease

# 7. Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable mcplease-mcp
sudo systemctl start mcplease-mcp

# 8. Check status
sudo systemctl status mcplease-mcp
```

### Security Configuration

```bash
# 1. Configure firewall
sudo ufw enable
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 8000/tcp  # SSE transport
sudo ufw allow 8001/tcp  # WebSocket transport

# 2. Generate TLS certificates
sudo apt install -y certbot
sudo certbot certonly --standalone -d your-domain.com

# 3. Configure TLS in server
sudo tee /home/mcplease/MCPlease/config/tls.conf > /dev/null <<EOF
[tls]
cert_file = /etc/letsencrypt/live/your-domain.com/fullchain.pem
key_file = /etc/letsencrypt/live/your-domain.com/privkey.pem
require_tls = true
EOF

# 4. Set up authentication
sudo tee /home/mcplease/MCPlease/config/auth.conf > /dev/null <<EOF
[auth]
require_auth = true
api_key = your-secure-api-key-here
session_timeout_minutes = 60
EOF
```

### Client Configuration

```json
// Client configuration for remote server
{
  "mcpServers": {
    "mcplease-remote": {
      "url": "https://your-domain.com:8000",
      "headers": {
        "Authorization": "Bearer your-api-key-here"
      }
    }
  }
}
```

---

## Raspberry Pi Deployment

### Pi Requirements

- **Model**: Raspberry Pi 4B 8GB+ (recommended) or Pi 5
- **OS**: Raspberry Pi OS 64-bit (Bookworm)
- **Storage**: 64GB+ microSD card
- **Power**: 3A+ power supply
- **Network**: Ethernet or WiFi

### Automated Deployment

```bash
# 1. Download deployment script
curl -O https://raw.githubusercontent.com/jmoncayo-pursuit/MCPlease/main/scripts/deploy-pi.sh
chmod +x deploy-pi.sh

# 2. Set environment variables
export NGROK_AUTH_TOKEN="your-ngrok-token"
export MCPLEASE_MODEL="gpt-oss-20b"
export MCPLEASE_ENABLE_TLS=true

# 3. Run deployment
./deploy-pi.sh
```

### Manual Deployment Steps

```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install dependencies
sudo apt install -y python3.11 python3.11-venv python3.11-dev
sudo apt install -y build-essential git curl wget

# 3. Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# 4. Clone repository
git clone https://github.com/jmoncayo-pursuit/MCPlease.git
cd MCPlease

# 5. Install dependencies
uv sync --frozen

# 6. Configure for Pi optimization
cat > config/pi.conf <<EOF
[hardware]
platform = raspberry_pi
memory_limit_gb = 6
cpu_cores = 4

[ai_model]
model_name = gpt-oss-20b
quantization = int8
max_memory_gb = 6

[performance]
enable_optimization = true
use_mps = false
use_cuda = false
EOF

# 7. Create systemd service
sudo tee /etc/systemd/system/mcplease-mcp.service > /dev/null <<EOF
[Unit]
Description=MCPlease MCP Server (Pi)
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/MCPlease
Environment=PATH=/home/pi/.cargo/bin:/usr/bin:/bin
Environment=MCPLEASE_CONFIG=/home/pi/MCPlease/config/pi.conf
ExecStart=/home/pi/.cargo/bin/uv run python -m mcplease_mcp.main --transport sse --port 8000 --host 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 8. Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable mcplease-mcp
sudo systemctl start mcplease-mcp
```

### Ngrok Tunneling Setup

```bash
# 1. Install ngrok
curl -O https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-arm64.tgz
tar xvzf ngrok-v3-stable-linux-arm64.tgz
sudo mv ngrok /usr/local/bin

# 2. Configure ngrok
ngrok config add-authtoken $NGROK_AUTH_TOKEN

# 3. Create ngrok service
sudo tee /etc/systemd/system/ngrok.service > /dev/null <<EOF
[Unit]
Description=Ngrok Tunnel for MCP Server
After=network.target mcplease-mcp.service

[Service]
Type=simple
User=pi
ExecStart=/usr/local/bin/ngrok http 8000 --log=stdout
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 4. Start ngrok
sudo systemctl enable ngrok
sudo systemctl start ngrok

# 5. Get public URL
ngrok http 8000
# Note the https://xxxx.ngrok.io URL
```

### Pi-Specific Optimizations

```bash
# 1. Enable GPU memory split
sudo raspi-config nonint do_memory_split 128

# 2. Enable hardware acceleration
echo 'dtoverlay=vc4-kms-v3d' | sudo tee -a /boot/config.txt

# 3. Optimize swap
sudo dphys-swapfile swapoff
sudo sed -i 's/CONF_SWAPSIZE=100/CONF_SWAPSIZE=2048/' /etc/dphys-swapfile
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# 4. Set performance governor
echo 'GOVERNOR=performance' | sudo tee /etc/default/cpufrequtils
sudo systemctl restart cpufrequtils
```

---

## Docker Deployment

### Single Container

```bash
# 1. Pull image
docker pull ghcr.io/jmoncayo-pursuit/mcplease:latest

# 2. Run container
docker run -d \
  --name mcplease-mcp \
  -p 8000:8000 \
  -p 8001:8001 \
  -v /path/to/models:/app/models \
  -v /path/to/config:/app/config \
  -e MCPLEASE_MODEL=gpt-oss-20b \
  -e MCPLEASE_ENABLE_TLS=false \
  ghcr.io/jmoncayo-pursuit/mcplease:latest
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  mcplease-mcp:
    image: ghcr.io/jmoncayo-pursuit/mcplease:latest
    container_name: mcplease-mcp
    ports:
      - "8000:8000"  # SSE transport
      - "8001:8001"  # WebSocket transport
    volumes:
      - ./models:/app/models
      - ./config:/app/config
      - ./logs:/app/logs
    environment:
      - MCPLEASE_MODEL=gpt-oss-20b
      - MCPLEASE_ENABLE_TLS=true
      - MCPLEASE_LOG_LEVEL=INFO
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - mcplease-network

  nginx:
    image: nginx:alpine
    container_name: mcplease-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - mcplease-mcp
    restart: unless-stopped
    networks:
      - mcplease-network

networks:
  mcplease-network:
    driver: bridge

volumes:
  models:
  config:
  logs:
```

### Multi-Architecture Build

```bash
# 1. Build for multiple architectures
docker buildx create --use
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag ghcr.io/jmoncayo-pursuit/mcplease:latest \
  --push .

# 2. Build specific architecture
docker buildx build \
  --platform linux/arm64 \
  --tag ghcr.io/jmoncayo-pursuit/mcplease:arm64 \
  --load .
```

---

## Production Deployment

### High Availability Setup

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  mcplease-mcp-1:
    image: ghcr.io/jmoncayo-pursuit/mcplease:latest
    container_name: mcplease-mcp-1
    ports:
      - "8000:8000"
      - "8001:8001"
    environment:
      - MCPLEASE_MODEL=gpt-oss-20b
      - MCPLEASE_ENABLE_TLS=true
      - MCPLEASE_CLUSTER_MODE=true
      - MCPLEASE_NODE_ID=node-1
    volumes:
      - ./models:/app/models
      - ./config:/app/config
    restart: unless-stopped
    networks:
      - mcplease-cluster

  mcplease-mcp-2:
    image: ghcr.io/jmoncayo-pursuit/mcplease:latest
    container_name: mcplease-mcp-2
    ports:
      - "8002:8000"
      - "8003:8001"
    environment:
      - MCPLEASE_MODEL=gpt-oss-20b
      - MCPLEASE_ENABLE_TLS=true
      - MCPLEASE_CLUSTER_MODE=true
      - MCPLEASE_NODE_ID=node-2
    volumes:
      - ./models:/app/models
      - ./config:/app/config
    restart: unless-stopped
    networks:
      - mcplease-cluster

  haproxy:
    image: haproxy:alpine
    container_name: mcplease-haproxy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./haproxy.cfg:/usr/local/etc/haproxy/haproxy.cfg
      - ./ssl:/etc/ssl/private
    depends_on:
      - mcplease-mcp-1
      - mcplease-mcp-2
    restart: unless-stopped
    networks:
      - mcplease-cluster

  redis:
    image: redis:7-alpine
    container_name: mcplease-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    restart: unless-stopped
    networks:
      - mcplease-cluster

networks:
  mcplease-cluster:
    driver: bridge

volumes:
  redis-data:
```

### Load Balancer Configuration

```haproxy
# haproxy.cfg
global
    log stdout format raw local0 info
    maxconn 4096

defaults
    log global
    mode http
    option httplog
    option dontlognull
    timeout connect 5000
    timeout client 50000
    timeout server 50000

frontend http_front
    bind *:80
    bind *:443 ssl crt /etc/ssl/private/mcplease.pem
    redirect scheme https if !{ ssl_fc }
    
    acl is_health_check path /health
    use_backend health_check if is_health_check
    
    default_backend mcplease_backend

backend health_check
    server health localhost:8000/health

backend mcplease_backend
    balance roundrobin
    option httpchk GET /health
    http-check expect status 200
    
    server mcplease-1 mcplease-mcp-1:8000 check
    server mcplease-2 mcplease-mcp-2:8000 check
    
    # Health check endpoint
    option httpchk GET /health
    http-check expect status 200
```

### Monitoring Setup

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: mcplease-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: mcplease-grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    restart: unless-stopped

volumes:
  prometheus-data:
  grafana-data:
```

---

## Monitoring & Maintenance

### Health Checks

```bash
# Check server health
curl -f http://localhost:8000/health

# Check specific components
curl http://localhost:8000/health | jq '.components'

# Check performance metrics
curl http://localhost:8000/metrics
```

### Log Management

```bash
# View real-time logs
docker logs -f mcplease-mcp

# View specific log files
tail -f logs/mcplease-mcp.log

# Rotate logs
sudo logrotate -f /etc/logrotate.d/mcplease
```

### Backup Procedures

```bash
# Backup configuration
tar -czf mcplease-config-$(date +%Y%m%d).tar.gz config/

# Backup models
rsync -av models/ backup/models/

# Backup logs
tar -czf mcplease-logs-$(date +%Y%m%d).tar.gz logs/
```

### Update Procedures

```bash
# Update container
docker pull ghcr.io/jmoncayo-pursuit/mcplease:latest
docker stop mcplease-mcp
docker rm mcplease-mcp
docker run -d --name mcplease-mcp [previous-options] ghcr.io/jmoncayo-pursuit/mcplease:latest

# Update system packages
sudo apt update && sudo apt upgrade -y

# Restart services
sudo systemctl restart mcplease-mcp
```

### Troubleshooting

```bash
# Check service status
sudo systemctl status mcplease-mcp

# Check logs
sudo journalctl -u mcplease-mcp -f

# Check resource usage
htop
free -h
df -h

# Test connectivity
telnet localhost 8000
curl -v http://localhost:8000/health

# Check firewall
sudo ufw status verbose
```

---

## Performance Tuning

### System Optimization

```bash
# Increase file descriptor limits
echo '* soft nofile 65536' | sudo tee -a /etc/security/limits.conf
echo '* hard nofile 65536' | sudo tee -a /etc/security/limits.conf

# Optimize kernel parameters
echo 'net.core.somaxconn = 65536' | sudo tee -a /etc/sysctl.conf
echo 'net.ipv4.tcp_max_syn_backlog = 65536' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### Application Tuning

```ini
# config/performance.conf
[performance]
max_workers = 8
max_connections = 1000
request_timeout = 30
enable_compression = true
enable_caching = true

[memory]
max_memory_gb = 12
enable_gc = true
gc_threshold = 0.8

[ai_model]
batch_size = 4
max_concurrent_requests = 10
model_cache_size = 2048
```

---

## Security Best Practices

### Network Security

```bash
# Restrict access to specific networks
sudo ufw allow from 192.168.0.0/16 to any port 8000
sudo ufw allow from 192.168.0.0/16 to any port 8001

# Enable rate limiting
sudo ufw limit 22/tcp
```

### Authentication

```bash
# Use strong API keys
openssl rand -hex 32

# Rotate keys regularly
# Set up key rotation schedule

# Monitor authentication attempts
tail -f logs/auth.log | grep "authentication"
```

### TLS Configuration

```bash
# Use strong cipher suites
# Disable weak protocols
# Regular certificate renewal
# Monitor certificate expiration
```

---

*For additional support and troubleshooting, refer to the main documentation and GitHub repository.*
