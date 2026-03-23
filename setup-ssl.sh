#!/bin/bash

# Quick SSL Setup Script for AWS EC2
# Run this after initial deployment to enable HTTPS

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    error "This script must be run with sudo"
    exit 1
fi

echo "================================"
echo "Policy Helper AI - SSL Setup"
echo "================================"
echo ""

# Read domain name
read -p "Enter your domain name (e.g., example.com): " DOMAIN
if [ -z "$DOMAIN" ]; then
    error "Domain name is required"
    exit 1
fi

log "Setting up SSL for domain: $DOMAIN"

# Install certbot if not already installed
if ! command -v certbot &> /dev/null; then
    log "Installing certbot..."
    apt update
    apt install -y certbot python3-certbot-nginx
fi

# Get SSL certificate
log "Getting SSL certificate from Let's Encrypt..."
certbot --nginx \
    -d "$DOMAIN" \
    --agree-tos \
    --no-eff-email \
    --email admin@"$DOMAIN" \
    --redirect

if [ $? -eq 0 ]; then
    log "✓ SSL certificate installed successfully"
    log "Your domain will auto-redirect from HTTP to HTTPS"
    
    # Restart Nginx
    systemctl restart nginx
    log "Nginx restarted"
    
    echo ""
    echo "================================"
    echo "SSL Setup Complete!"
    echo "================================"
    echo ""
    log "HTTPS is now enabled at: https://$DOMAIN"
    echo "Certificate will auto-renew in 90 days via certbot timer"
    echo ""
else
    error "Failed to obtain SSL certificate"
    warn "Make sure:"
    warn "1. Domain is pointing to this server's IP"
    warn "2. Port 80 and 443 are open in security group"
    warn "3. Domain is registered and DNS is propagated"
    exit 1
fi
