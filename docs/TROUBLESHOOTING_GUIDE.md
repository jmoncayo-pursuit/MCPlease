# MCPlease MCP Server - Troubleshooting Guide

**Complete troubleshooting guide for common issues and solutions**

**Version**: 1.0.0  
**Last Updated**: January 18, 2025  
**Coverage**: All deployment scenarios and common issues

---

## Table of Contents

1. [Quick Diagnosis](#quick-diagnosis)
2. [Common Issues](#common-issues)
3. [Error Codes & Solutions](#error-codes--solutions)
4. [Performance Issues](#performance-issues)
5. [Network & Connectivity](#network--connectivity)
6. [AI Model Issues](#ai-model-issues)
7. [IDE Integration Problems](#ide-integration-problems)
8. [Deployment Issues](#deployment-issues)
9. [Debug Commands](#debug-commands)
10. [Getting Help](#getting-help)

---

## Quick Diagnosis

### Health Check Commands

```bash
# Basic health check
curl -f http://localhost:8000/health

# Detailed health report
curl http://localhost:8000/health | jq '.'

# Component-specific health
curl http://localhost:8000/health | jq '.components'

# Performance metrics
curl http://localhost:8000/metrics
```

### Status Indicators

| Status | Meaning | Action Required |
|--------|---------|----------------|
| ✅ **Healthy** | All systems operational | None |
| ⚠️ **Warning** | Minor issues detected | Monitor closely |
| ❌ **Critical** | Major issues detected | Immediate attention |
| 🔴 **Unknown** | Status cannot be determined | Check logs |

---

## Common Issues

### 1. Server Won't Start

#### Symptoms
- Server process exits immediately
- "Address already in use" errors
- Permission denied errors

#### Solutions

**Port Conflict**
```bash
# Check what's using the port
sudo netstat -tlnp | grep :8000
sudo lsof -i :8000

# Kill conflicting process
sudo kill -9 <PID>

# Or use different port
python -m mcplease_mcp.main --transport sse --port 8002
```

**Permission Issues**
```bash
# Check file permissions
ls -la mcplease_mcp/main.py

# Fix permissions
chmod +x mcplease_mcp/main.py
chmod 755 mcplease_mcp/

# Check user permissions
whoami
sudo chown -R $USER:$USER .
```

**Missing Dependencies**
```bash
# Reinstall dependencies
uv sync --frozen

# Check Python version
python --version  # Should be 3.9+

# Verify uv installation
uv --version
```

### 2. Connection Refused

#### Symptoms
- "Connection refused" errors
- Can't connect from IDE
- Network timeout errors

#### Solutions

**Check Server Status**
```bash
# Check if server is running
ps aux | grep mcplease
pgrep -f mcplease

# Check service status
sudo systemctl status mcplease-mcp
```

**Verify Port Binding**
```bash
# Check what ports are listening
sudo netstat -tlnp | grep -E ':(8000|8001)'
sudo ss -tuln | grep -E ':(8000|8001)'

# Test local connectivity
telnet localhost 8000
curl -v http://localhost:8000/health
```

**Firewall Issues**
```bash
# Check firewall status
sudo ufw status verbose

# Allow MCP ports
sudo ufw allow 8000/tcp
sudo ufw allow 8001/tcp

# Check iptables
sudo iptables -L -n | grep -E '8000|8001'
```

### 3. Authentication Failures

#### Symptoms
- "Unauthorized" errors
- "Invalid token" messages
- Session expiration errors

#### Solutions

**Check API Key**
```bash
# Verify API key in config
cat config/auth.conf | grep api_key

# Generate new API key
openssl rand -hex 32

# Update configuration
sed -i 's/old_key/new_key/' config/auth.conf
```

**Session Issues**
```bash
# Check session timeout
grep session_timeout config/auth.conf

# Clear expired sessions
curl -X POST http://localhost:8000/auth/clear-sessions \
  -H "Authorization: Bearer your-api-key"
```

**Token Format**
```bash
# Ensure proper Bearer token format
curl -H "Authorization: Bearer your-token" \
  http://localhost:8000/health
```

---

## Error Codes & Solutions

### MCP Protocol Errors

| Error Code | Message | Cause | Solution |
|------------|---------|-------|----------|
| -32600 | Invalid Request | Malformed JSON-RPC | Check request format |
| -32601 | Method not found | Unsupported MCP method | Verify method name |
| -32602 | Invalid params | Tool argument validation failed | Check argument schema |
| -32603 | Internal error | Server-side processing error | Check server logs |

### HTTP Status Codes

| Status | Meaning | Solution |
|--------|---------|----------|
| 400 | Bad Request | Check request format and parameters |
| 401 | Unauthorized | Verify authentication credentials |
| 403 | Forbidden | Check permissions and network policies |
| 404 | Not Found | Verify endpoint URL and method |
| 429 | Too Many Requests | Reduce request rate or increase limits |
| 500 | Internal Server Error | Check server logs for details |
| 502 | Bad Gateway | Check upstream service status |
| 503 | Service Unavailable | Server overloaded or maintenance mode |

### Custom Error Codes

| Code | Message | Solution |
|------|---------|----------|
| -32001 | Tool execution failed | Check AI model status and logs |
| -32002 | Authentication required | Provide valid API key or token |
| -32003 | Rate limited | Wait or increase rate limits |
| -32004 | Model not ready | Wait for AI model to load |
| -32005 | Resource exhausted | Check system resources |

---

## Performance Issues

### 1. Slow Response Times

#### Symptoms
- Tool execution takes >10 seconds
- High latency in IDE
- Timeout errors

#### Solutions

**Check System Resources**
```bash
# Monitor CPU and memory
htop
free -h
df -h

# Check for memory pressure
cat /proc/meminfo | grep -E "(MemAvailable|MemFree)"

# Monitor disk I/O
iostat -x 1
```

**AI Model Optimization**
```bash
# Check model loading status
curl http://localhost:8000/health | jq '.components.ai_adapter'

# Verify model quantization
ls -la models/ | grep -E "(int8|int4|fp16)"

# Check GPU utilization (if applicable)
nvidia-smi
```

**Performance Tuning**
```bash
# Adjust worker processes
echo 'max_workers = 4' >> config/performance.conf

# Enable caching
echo 'enable_caching = true' >> config/performance.conf

# Restart server
sudo systemctl restart mcplease-mcp
```

### 2. High Memory Usage

#### Symptoms
- Out of memory errors
- System becomes unresponsive
- AI model fails to load

#### Solutions

**Memory Monitoring**
```bash
# Check memory usage
free -h
cat /proc/meminfo

# Monitor memory pressure
cat /proc/pressure/memory

# Check swap usage
swapon --show
```

**Memory Optimization**
```bash
# Reduce model memory usage
echo 'quantization = int8' >> config/ai_model.conf
echo 'max_memory_gb = 8' >> config/ai_model.conf

# Enable memory cleanup
echo 'enable_gc = true' >> config/performance.conf

# Restart with memory limits
python -m mcplease_mcp.main --max-memory 8GB
```

### 3. High CPU Usage

#### Symptoms
- System becomes sluggish
- High CPU temperature
- Battery drain (laptops)

#### Solutions

**CPU Monitoring**
```bash
# Check CPU usage
top
htop
cat /proc/loadavg

# Monitor CPU frequency
cat /proc/cpuinfo | grep MHz
```

**CPU Optimization**
```bash
# Limit worker processes
echo 'max_workers = 2' >> config/performance.conf

# Enable CPU throttling
echo 'cpu_throttle = true' >> config/performance.conf

# Use lower precision models
echo 'precision = fp16' >> config/ai_model.conf
```

---

## Network & Connectivity

### 1. Network Timeouts

#### Symptoms
- Connection timeouts
- Slow network performance
- Intermittent connectivity

#### Solutions

**Network Diagnostics**
```bash
# Test network connectivity
ping -c 4 8.8.8.8
traceroute google.com

# Check DNS resolution
nslookup google.com
dig google.com

# Test specific ports
telnet google.com 80
nc -zv google.com 80
```

**Network Configuration**
```bash
# Check network interfaces
ip addr show
ifconfig

# Check routing table
ip route show
route -n

# Test local network
ping -c 4 192.168.1.1
```

### 2. Firewall Issues

#### Symptoms
- Can't connect from external clients
- Port scanning shows closed ports
- Network policy violations

#### Solutions

**Firewall Configuration**
```bash
# Check firewall status
sudo ufw status verbose
sudo firewall-cmd --list-all

# Allow MCP ports
sudo ufw allow 8000/tcp comment "MCP SSE transport"
sudo ufw allow 8001/tcp comment "MCP WebSocket transport"

# Check iptables rules
sudo iptables -L -n | grep -E '8000|8001'
```

**Network Policies**
```bash
# Check network policy configuration
cat config/network.conf

# Allow specific IP ranges
echo 'allowed_networks = ["192.168.0.0/16"]' >> config/network.conf

# Restart network security manager
curl -X POST http://localhost:8000/security/reload-policies
```

### 3. TLS/SSL Issues

#### Symptoms
- Certificate errors
- TLS handshake failures
- HTTPS connection refused

#### Solutions

**Certificate Verification**
```bash
# Check certificate validity
openssl x509 -in /path/to/cert.pem -text -noout

# Verify certificate chain
openssl verify -CAfile /path/to/ca.pem /path/to/cert.pem

# Check certificate expiration
openssl x509 -in /path/to/cert.pem -noout -dates
```

**TLS Configuration**
```bash
# Check TLS configuration
cat config/tls.conf

# Test TLS connection
openssl s_client -connect localhost:8000 -servername localhost

# Verify TLS protocols
nmap --script ssl-enum-ciphers -p 8000 localhost
```

---

## AI Model Issues

### 1. Model Loading Failures

#### Symptoms
- "Model not ready" errors
- High memory usage during loading
- Model download failures

#### Solutions

**Model Status Check**
```bash
# Check model loading status
curl http://localhost:8000/health | jq '.components.ai_adapter'

# Check model files
ls -la models/
du -sh models/

# Verify model integrity
python -c "import torch; print(torch.load('models/model.pt', map_location='cpu'))"
```

**Model Download Issues**
```bash
# Check download progress
tail -f logs/download.log

# Resume interrupted download
python download_model.py --resume

# Verify checksums
sha256sum models/model.pt
```

**Memory Issues**
```bash
# Check available memory
free -h

# Use smaller model variant
echo 'model_name = gpt-oss-20b-int8' >> config/ai_model.conf

# Enable model offloading
echo 'enable_offloading = true' >> config/ai_model.conf
```

### 2. Model Performance Issues

#### Symptoms
- Slow inference
- High memory usage
- Poor response quality

#### Solutions

**Model Optimization**
```bash
# Check quantization
echo 'quantization = int8' >> config/ai_model.conf

# Enable model caching
echo 'enable_cache = true' >> config/ai_model.conf

# Adjust batch size
echo 'batch_size = 1' >> config/ai_model.conf
```

**Hardware Acceleration**
```bash
# Check GPU availability
nvidia-smi
lspci | grep -i vga

# Enable CUDA (if available)
echo 'use_cuda = true' >> config/ai_model.conf

# Enable MPS (Mac)
echo 'use_mps = true' >> config/ai_model.conf
```

---

## IDE Integration Problems

### 1. VSCode Integration Issues

#### Symptoms
- Continue.dev not working
- MCP server not detected
- Configuration errors

#### Solutions

**Extension Installation**
```bash
# Install Continue.dev extension
code --install-extension continue.continue

# Check extension status
code --list-extensions | grep continue

# Restart VSCode after installation
code --quit
code .
```

**Configuration Issues**
```bash
# Check MCP configuration
cat .vscode/mcp.json

# Verify server configuration
cat .vscode/settings.json

# Test MCP server manually
python -m mcplease_mcp.main --transport stdio
```

**Connection Testing**
```bash
# Test stdio transport
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05"}}' | python -m mcplease_mcp.main --transport stdio
```

### 2. Cursor IDE Issues

#### Symptoms
- AI features not working
- MCP connection failed
- Configuration errors

#### Solutions

**MCP Support**
```bash
# Check Cursor version
cursor --version

# Verify MCP configuration
cat ~/.cursor/mcp.json

# Test MCP server
python -m mcplease_mcp.main --transport stdio
```

**AI Feature Testing**
```bash
# Test code completion
# Use Cursor's AI features with simple prompts

# Check error logs
tail -f ~/.cursor/logs/error.log
```

### 3. JetBrains Integration

#### Symptoms
- MCP plugin not working
- Connection timeouts
- Configuration errors

#### Solutions

**Plugin Installation**
```bash
# Install MCP plugin from JetBrains marketplace
# Restart IDE after installation

# Check plugin status
# Go to Settings > Plugins > MCP
```

**Configuration**
```bash
# Configure MCP server
# Settings > Tools > MCP Servers

# Test connection
# Use MCP server test button
```

---

## Deployment Issues

### 1. Docker Issues

#### Symptoms
- Container won't start
- Port binding errors
- Volume mount failures

#### Solutions

**Container Status**
```bash
# Check container status
docker ps -a
docker logs mcplease-mcp

# Check container resources
docker stats mcplease-mcp

# Verify image
docker images | grep mcplease
```

**Port Binding**
```bash
# Check port conflicts
sudo netstat -tlnp | grep -E ':(8000|8001)'

# Use different ports
docker run -p 8002:8000 -p 8003:8001 mcplease/mcp-server:latest

# Check container networking
docker network ls
docker network inspect bridge
```

**Volume Mounts**
```bash
# Check volume permissions
ls -la /path/to/models/
ls -la /path/to/config/

# Fix permissions
sudo chown -R 1000:1000 /path/to/models/
sudo chown -R 1000:1000 /path/to/config/

# Verify volume mounts
docker inspect mcplease-mcp | jq '.[0].Mounts'
```

### 2. Systemd Service Issues

#### Symptoms
- Service won't start
- Service crashes on startup
- Permission denied errors

#### Solutions

**Service Status**
```bash
# Check service status
sudo systemctl status mcplease-mcp

# View service logs
sudo journalctl -u mcplease-mcp -f

# Check service configuration
sudo systemctl cat mcplease-mcp
```

**Service Configuration**
```bash
# Verify service file
cat /etc/systemd/system/mcplease-mcp.service

# Check user permissions
id mcplease
ls -la /home/mcplease/MCPlease/

# Fix permissions
sudo chown -R mcplease:mcplease /home/mcplease/MCPlease/
```

**Environment Issues**
```bash
# Check environment variables
sudo systemctl show mcplease-mcp --property=Environment

# Test service manually
sudo -u mcplease /home/mcplease/.cargo/bin/uv run python -m mcplease_mcp.main
```

### 3. Raspberry Pi Issues

#### Symptoms
- High temperature warnings
- Memory errors
- Slow performance

#### Solutions

**Temperature Management**
```bash
# Check temperature
vcgencmd measure_temp

# Enable cooling
echo 'dtoverlay=vc4-kms-v3d' | sudo tee -a /boot/config.txt

# Add heatsink/fan if needed
```

**Memory Optimization**
```bash
# Check memory usage
free -h
cat /proc/meminfo

# Optimize swap
sudo dphys-swapfile swapoff
sudo sed -i 's/CONF_SWAPSIZE=100/CONF_SWAPSIZE=2048/' /etc/dphys-swapfile
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

**Performance Tuning**
```bash
# Set performance governor
echo 'GOVERNOR=performance' | sudo tee /etc/default/cpufrequtils
sudo systemctl restart cpufrequtils

# Optimize GPU memory
sudo raspi-config nonint do_memory_split 128
```

---

## Debug Commands

### System Information

```bash
# System overview
uname -a
cat /etc/os-release
lscpu
free -h
df -h

# Process information
ps aux | grep mcplease
pgrep -f mcplease
```

### Network Diagnostics

```bash
# Network interfaces
ip addr show
ifconfig
ip route show

# Connectivity tests
ping -c 4 8.8.8.8
traceroute google.com
telnet localhost 8000
```

### Service Debugging

```bash
# Service status
sudo systemctl status mcplease-mcp
sudo journalctl -u mcplease-mcp -f

# Manual testing
sudo -u mcplease /home/mcplease/.cargo/bin/uv run python -m mcplease_mcp.main --debug
```

### Log Analysis

```bash
# View logs
tail -f logs/mcplease-mcp.log
tail -f logs/error.log
tail -f logs/access.log

# Search logs
grep "ERROR" logs/mcplease-mcp.log
grep "authentication" logs/auth.log
```

---

## Getting Help

### Self-Service Resources

1. **Documentation**
   - API Documentation: `docs/API_DOCUMENTATION.md`
   - Deployment Guides: `docs/DEPLOYMENT_GUIDES.md`
   - Quick Start Guide: `QUICK_START_GUIDE.md`

2. **Logs and Monitoring**
   - Server logs: `logs/mcplease-mcp.log`
   - Health endpoint: `http://localhost:8000/health`
   - Metrics endpoint: `http://localhost:8000/metrics`

3. **Configuration Files**
   - Main config: `config/settings.conf`
   - AI model config: `config/ai_model.conf`
   - Security config: `config/security.conf`

### Community Support

1. **GitHub Issues**
   - Report bugs: Create new issue
   - Feature requests: Use issue template
   - Search existing issues for solutions

2. **GitHub Discussions**
   - Ask questions
   - Share solutions
   - Get community help

3. **Documentation Contributions**
   - Improve guides
   - Add examples
   - Fix documentation issues

### Escalation Path

1. **Check logs and health status**
2. **Review this troubleshooting guide**
3. **Search GitHub issues and discussions**
4. **Create detailed issue report**
5. **Provide system information and logs**

### Issue Report Template

```markdown
## Issue Description
Brief description of the problem

## Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.11.0]
- MCPlease Version: [e.g., 1.0.0]
- Deployment: [e.g., Local, Docker, Pi]

## Logs
```
[Paste relevant log entries]
```

## Configuration
```
[Paste relevant configuration]
```

## Additional Information
Any other details that might help
```

---

*This troubleshooting guide is maintained as part of the MCPlease MCP Server project. For additional support, please visit our GitHub repository.*
