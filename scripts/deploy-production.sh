#!/bin/bash

# Production deployment script for MCPlease MCP Server
# This script sets up a complete production environment with monitoring

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DEPLOYMENT_NAME="mcplease-production"
DOMAIN="${1:-}"
EMAIL="${2:-}"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if running as root
    if [[ $EUID -eq 0 ]]; then
        log_warning "Running as root. Consider using a non-root user for production."
    fi
    
    log_success "Prerequisites check passed"
}

create_directories() {
    log_info "Creating production directories..."
    
    mkdir -p "$PROJECT_DIR"/{config,models,logs,ssl,backup,secrets,monitoring}
    mkdir -p "$PROJECT_DIR"/monitoring/{grafana,alertmanager}
    
    log_success "Directories created"
}

setup_ssl_certificates() {
    if [[ -z "$DOMAIN" ]]; then
        log_warning "No domain specified, using self-signed certificates"
        generate_self_signed_cert
    else
        log_info "Setting up SSL certificates for domain: $DOMAIN"
        setup_letsencrypt_cert
    fi
}

generate_self_signed_cert() {
    log_info "Generating self-signed SSL certificate..."
    
    local ssl_dir="$PROJECT_DIR/ssl"
    local key_file="$ssl_dir/mcplease.key"
    local cert_file="$ssl_dir/mcplease.pem"
    
    # Generate private key
    openssl genrsa -out "$key_file" 2048
    
    # Generate certificate
    openssl req -new -x509 -key "$key_file" -out "$cert_file" -days 365 -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
    
    # Combine key and cert for HAProxy
    cat "$key_file" "$cert_file" > "$ssl_dir/mcplease.pem"
    
    log_success "Self-signed certificate generated"
}

setup_letsencrypt_cert() {
    log_info "Setting up Let's Encrypt certificate for $DOMAIN..."
    
    # Install certbot if not available
    if ! command -v certbot &> /dev/null; then
        log_info "Installing certbot..."
        sudo apt update
        sudo apt install -y certbot
    fi
    
    # Generate certificate
    sudo certbot certonly --standalone -d "$DOMAIN" --email "$EMAIL" --agree-tos --non-interactive
    
    # Copy certificates
    local ssl_dir="$PROJECT_DIR/ssl"
    sudo cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$ssl_dir/mcplease.key"
    sudo cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$ssl_dir/mcplease.crt"
    
    # Combine for HAProxy
    cat "$ssl_dir/mcplease.key" "$ssl_dir/mcplease.crt" > "$ssl_dir/mcplease.pem"
    
    # Set permissions
    sudo chown -R "$USER:$USER" "$ssl_dir"
    chmod 600 "$ssl_dir"/*
    
    log_success "Let's Encrypt certificate setup completed"
}

generate_secrets() {
    log_info "Generating production secrets..."
    
    local secrets_dir="$PROJECT_DIR/secrets"
    
    # Generate PostgreSQL password
    openssl rand -hex 32 > "$secrets_dir/postgres_password.txt"
    
    # Generate Grafana password
    openssl rand -hex 32 > "$secrets_dir/grafana_password.txt"
    
    # Generate MCP API key
    openssl rand -hex 32 > "$secrets_dir/mcplease_api_key.txt"
    
    # Set permissions
    chmod 600 "$secrets_dir"/*
    
    log_success "Secrets generated"
}

create_production_config() {
    log_info "Creating production configuration..."
    
    local config_dir="$PROJECT_DIR/config"
    
    # Main configuration
    cat > "$config_dir/production.conf" <<EOF
[server]
environment = production
log_level = INFO
enable_tls = true
require_auth = true
cluster_mode = true

[performance]
max_workers = 8
max_connections = 1000
request_timeout = 30
enable_compression = true
enable_caching = true

[security]
rate_limit_per_ip = 100
max_connections_per_ip = 10
session_timeout_minutes = 60
require_tls = true

[monitoring]
enable_metrics = true
enable_health_checks = true
metrics_port = 8000
health_check_interval = 30

[ai_model]
model_name = gpt-oss-20b
quantization = int8
max_memory_gb = 12
enable_cache = true
EOF
    
    # Redis configuration
    cat > "$PROJECT_DIR/redis.conf" <<EOF
# Redis production configuration
bind 0.0.0.0
port 6379
timeout 300
tcp-keepalive 60
maxmemory 2gb
maxmemory-policy allkeys-lru
appendonly yes
appendfsync everysec
save 900 1
save 300 10
save 60 10000
EOF
    
    log_success "Production configuration created"
}

setup_monitoring() {
    log_info "Setting up monitoring configuration..."
    
    local monitoring_dir="$PROJECT_DIR/monitoring"
    
    # Prometheus rules
    if [[ ! -f "$monitoring_dir/prometheus-rules.yml" ]]; then
        cp "$PROJECT_DIR/monitoring/prometheus-rules.yml" "$monitoring_dir/"
    fi
    
    # Grafana provisioning
    mkdir -p "$monitoring_dir/grafana/provisioning/datasources"
    mkdir -p "$monitoring_dir/grafana/provisioning/dashboards"
    
    # Prometheus datasource
    cat > "$monitoring_dir/grafana/provisioning/datasources/prometheus.yml" <<EOF
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF
    
    # Dashboard provisioning
    cat > "$monitoring_dir/grafana/provisioning/dashboards/dashboards.yml" <<EOF
apiVersion: 1
providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
EOF
    
    # Copy dashboards
    cp -r "$PROJECT_DIR/monitoring/grafana/dashboards"/* "$monitoring_dir/grafana/dashboards/" 2>/dev/null || true
    
    log_success "Monitoring configuration setup completed"
}

deploy_services() {
    log_info "Deploying production services..."
    
    cd "$PROJECT_DIR"
    
    # Pull latest images
    log_info "Pulling latest Docker images..."
    docker-compose -f docker-compose.production.yml pull
    
    # Start services
    log_info "Starting production services..."
    docker-compose -f docker-compose.production.yml up -d
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 30
    
    log_success "Production services deployed"
}

verify_deployment() {
    log_info "Verifying deployment..."
    
    local health_checks=(
        "http://localhost:8000/health"
        "http://localhost:9090/-/healthy"
        "http://localhost:3000/api/health"
        "http://localhost:8404/stats"
    )
    
    for url in "${health_checks[@]}"; do
        if curl -f -s "$url" > /dev/null; then
            log_success "Health check passed: $url"
        else
            log_error "Health check failed: $url"
            return 1
        fi
    done
    
    log_success "All health checks passed"
}

setup_backup_cron() {
    log_info "Setting up backup cron job..."
    
    local backup_script="$PROJECT_DIR/scripts/backup-production.sh"
    
    # Create backup script
    cat > "$backup_script" <<'EOF'
#!/bin/bash
# Production backup script
cd "$(dirname "$0")/.."
docker-compose -f docker-compose.production.yml run --rm backup
EOF
    
    chmod +x "$backup_script"
    
    # Add to crontab (daily at 2 AM)
    (crontab -l 2>/dev/null; echo "0 2 * * * $backup_script") | crontab -
    
    log_success "Backup cron job configured"
}

setup_log_rotation() {
    log_info "Setting up log rotation..."
    
    local logrotate_config="/etc/logrotate.d/mcplease"
    
    sudo tee "$logrotate_config" > /dev/null <<EOF
$PROJECT_DIR/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
    postrotate
        docker-compose -f $PROJECT_DIR/docker-compose.production.yml restart mcplease-mcp-1 mcplease-mcp-2
    endscript
}
EOF
    
    log_success "Log rotation configured"
}

show_deployment_info() {
    log_success "Production deployment completed successfully!"
    echo
    echo "=== Deployment Information ==="
    echo "Project Directory: $PROJECT_DIR"
    echo "Domain: ${DOMAIN:-localhost (self-signed)}"
    echo "Services:"
    echo "  - MCP Server: http://localhost:8000"
    echo "  - HAProxy Stats: http://localhost:8404/stats"
    echo "  - Prometheus: http://localhost:9090"
    echo "  - Grafana: http://localhost:3000"
    echo "  - Alertmanager: http://localhost:9093"
    echo
    echo "=== Access Credentials ==="
    echo "Grafana: admin / $(cat "$PROJECT_DIR/secrets/grafana_password.txt")"
    echo "HAProxy Stats: admin / admin123"
    echo "MCP API Key: $(cat "$PROJECT_DIR/secrets/mcplease_api_key.txt")"
    echo
    echo "=== Next Steps ==="
    echo "1. Configure your domain DNS to point to this server"
    echo "2. Update SSL certificates if using Let's Encrypt"
    echo "3. Configure monitoring alerts in Grafana"
    echo "4. Set up external monitoring (e.g., UptimeRobot)"
    echo "5. Review and adjust resource limits as needed"
    echo
    echo "=== Useful Commands ==="
    echo "View logs: docker-compose -f docker-compose.production.yml logs -f"
    echo "Restart services: docker-compose -f docker-compose.production.yml restart"
    echo "Update services: docker-compose -f docker-compose.production.yml pull && docker-compose -f docker-compose.production.yml up -d"
    echo "Backup: $PROJECT_DIR/scripts/backup-production.sh"
}

main() {
    echo "=== MCPlease MCP Server Production Deployment ==="
    echo
    
    # Check prerequisites
    check_prerequisites
    
    # Create directories
    create_directories
    
    # Setup SSL
    setup_ssl_certificates
    
    # Generate secrets
    generate_secrets
    
    # Create configuration
    create_production_config
    
    # Setup monitoring
    setup_monitoring
    
    # Deploy services
    deploy_services
    
    # Verify deployment
    verify_deployment
    
    # Setup backup and maintenance
    setup_backup_cron
    setup_log_rotation
    
    # Show deployment info
    show_deployment_info
}

# Run main function
main "$@"
