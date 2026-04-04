#!/bin/bash

# AWS EC2 Deployment Automation Script
# Policy Helper AI - Automated Setup
# Run this on your EC2 instance after SSH connection
# Usage: chmod +x deploy-aws.sh && sudo ./deploy-aws.sh

set -e  # Exit on error

echo "================================"
echo "Policy Helper AI - AWS EC2 Setup"
echo "================================"
echo ""

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/var/www/policy-helper-ai"
APP_USER="ubuntu"
APP_NAME="policy-helper-ai"
GITHUB_REPO="${GITHUB_REPO:-https://github.com/Surajmeher1/Policy-Helper-AI.git}"
DOMAIN="${DOMAIN:-}"

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    error "This script must be run with sudo: sudo ./deploy-aws.sh"
fi

# Check if .env file exists locally (before running script)
if [ ! -f "$APP_DIR/.env" ] && [ ! -f "./.env" ]; then
    warn ".env file not found. You will need to create it after setup."
    warn "Copy from .env.example: cp .env.example .env"
    info "Required variables: GROQ_API_KEY, HF_TOKEN, SECRET_KEY"
fi

# Step 1: Update system
log "Step 1: Updating system packages..."
apt update
apt upgrade -y 2>/dev/null || warn "Some packages may have failed to upgrade"

# Step 2: Install dependencies
log "Step 2: Installing dependencies..."
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    build-essential \
    nginx \
    curl \
    wget \
    certbot \
    python3-certbot-nginx \
    curl \
    jq

log "${GREEN}Dependencies installed successfully${NC}"

# Step 3: Create app directory
log "Step 3: Setting up application directory..."
mkdir -p "$APP_DIR"
chown "$APP_USER:$APP_USER" "$APP_DIR"

# Step 4: Clone repository
log "Step 4: Cloning repository..."
if [ -d "$APP_DIR/.git" ]; then
    info "Repository already exists, pulling latest changes..."
    cd "$APP_DIR"
    sudo -u "$APP_USER" git pull origin main 2>/dev/null || warn "Could not pull from GitHub"
else
    if [ -n "$(find "$APP_DIR" -mindepth 1 -maxdepth 1 2>/dev/null | head -n 1)" ]; then
        error "$APP_DIR exists but is not a git checkout. Remove its contents or clone the repository manually before rerunning this script."
    fi

    info "Cloning from GitHub: $GITHUB_REPO"
    sudo -u "$APP_USER" bash -c "cd /var/www && git clone '$GITHUB_REPO' '$(basename "$APP_DIR")'" || {
        error "Failed to clone repository. Check the GitHub URL, network access, and repository permissions."
    }
fi

cd "$APP_DIR"

if [ ! -f "$APP_DIR/requirements.txt" ]; then
    error "requirements.txt was not found in $APP_DIR. The repository checkout is incomplete. Verify the clone succeeded and contains the project files."
fi

# Step 5: Create virtual environment
log "Step 5: Creating Python virtual environment..."
if [ ! -d "$APP_DIR/venv" ]; then
    sudo -u "$APP_USER" python3 -m venv venv
else
    info "Virtual environment already exists"
fi

# Step 6: Install Python dependencies
log "Step 6: Installing Python packages..."
sudo -u "$APP_USER" bash -c "
    source $APP_DIR/venv/bin/activate
    pip install --upgrade pip --quiet
    pip install -r $APP_DIR/requirements.txt --quiet
" || error "Failed to install Python packages"

log "${GREEN}Python packages installed successfully${NC}"

# Step 7: Create instance directory for database
log "Step 7: Creating instance directory for SQLite database..."
mkdir -p "$APP_DIR/instance"
chown "$APP_USER:$APP_USER" "$APP_DIR/instance"
chmod 755 "$APP_DIR/instance"

# Step 8: Create .env file if not exists
log "Step 8: Checking .env configuration..."
if [ ! -f "$APP_DIR/.env" ]; then
    warn ".env file not found. Creating template..."
    sudo -u "$APP_USER" cp "$APP_DIR/.env.example" "$APP_DIR/.env"
    warn "${YELLOW}⚠️  IMPORTANT: Edit .env with your API keys:${NC}"
    warn "   nano $APP_DIR/.env"
    warn ""
    warn "Required:"
    warn "   - GROQ_API_KEY (from https://console.groq.com)"
    warn "   - HF_TOKEN (from https://huggingface.co/settings/tokens)"
    warn "   - SECRET_KEY (generate: python3 -c \"import secrets; print(secrets.token_hex(32))\")"
    warn ""
    chmod 600 "$APP_DIR/.env"
else
    info ".env file found"
fi

# Step 9: Create Gunicorn systemd service
log "Step 9: Creating Gunicorn systemd service..."
cat > "/etc/systemd/system/${APP_NAME}.service" << 'EOF'
[Unit]
Description=Policy Helper AI Flask Application
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/var/www/policy-helper-ai
Environment="PATH=/var/www/policy-helper-ai/venv/bin"
EnvironmentFile=/var/www/policy-helper-ai/.env

ExecStart=/var/www/policy-helper-ai/venv/bin/gunicorn \
    --workers 3 \
    --worker-class sync \
    --bind unix:/run/policy-helper-ai.sock \
    --timeout 120 \
    --access-logfile /var/log/policy-helper-ai/access.log \
    --error-logfile /var/log/policy-helper-ai/error.log \
    app:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

log "Gunicorn service file created"

# Step 10: Create logs directory
log "Step 10: Creating logs directory..."
mkdir -p /var/log/policy-helper-ai
chown "$APP_USER:$APP_USER" /var/log/policy-helper-ai
chmod 755 /var/log/policy-helper-ai

# Step 11: Configure Nginx
log "Step 11: Configuring Nginx..."
cat > "/etc/nginx/sites-available/${APP_NAME}" << 'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;

    server_name _;

    client_max_body_size 50M;

    location / {
        proxy_pass http://unix:/run/policy-helper-ai.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 120s;
    }

    location /static/ {
        alias /var/www/policy-helper-ai/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

log "Nginx configuration created"

# Step 12: Enable Nginx site
log "Step 12: Enabling Nginx site..."
ln -sf "/etc/nginx/sites-available/${APP_NAME}" "/etc/nginx/sites-enabled/${APP_NAME}"
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
if nginx -t > /dev/null 2>&1; then
    log "Nginx configuration is valid"
else
    error "Nginx configuration test failed! Check /etc/nginx/sites-available/${APP_NAME}"
fi

# Step 13: Enable and start services
log "Step 13: Enabling and starting services..."
systemctl daemon-reload
systemctl enable "$APP_NAME"
systemctl enable nginx

# Wait a moment for systemd to register services
sleep 2

# Start the services
systemctl start "$APP_NAME" || warn "Failed to auto-start $APP_NAME service"
systemctl start nginx || warn "Failed to auto-start nginx"

# Give services time to start
sleep 3

# Step 14: Verify services
log "Step 14: Verifying services..."
if systemctl is-active --quiet "$APP_NAME"; then
    log "${GREEN}✓${NC} $APP_NAME is running"
else
    error "$APP_NAME service is not running. Check logs: sudo journalctl -u $APP_NAME -n 20"
fi

if systemctl is-active --quiet nginx; then
    log "${GREEN}✓${NC} Nginx is running"
else
    error "Nginx is not running. Check logs: sudo journalctl -u nginx -n 20"
fi

# Step 15: Final status
log "Step 15: Deployment Summary"
echo ""
echo "${CYAN}====================================${NC}"
echo "${CYAN}Policy Helper AI - Deployed!${NC}"
echo "${CYAN}====================================${NC}"
echo ""

# Get public IP
PUBLIC_IP=$(ec2-metadata --public-ipv4 2>/dev/null | cut -d " " -f 2 || curl -s http://169.254.169.254/latest/meta-data/public-ipv4)

echo -e "${GREEN}Application URL:${NC} http://$PUBLIC_IP"
echo ""
echo -e "${YELLOW}IMPORTANT NEXT STEPS:${NC}"
echo "1. Configure .env file with API keys:"
echo "   nano $APP_DIR/.env"
echo ""
echo "2. Add your API keys:"
echo "   - GROQ_API_KEY=xxx"
echo "   - HF_TOKEN=xxx"
echo "   - SECRET_KEY=xxx (generate if needed)"
echo ""
echo "3. Restart application to apply changes:"
echo "   sudo systemctl restart $APP_NAME"
echo ""
echo "4. Check application logs:"
echo "   tail -f /var/log/policy-helper-ai/error.log"
echo ""
echo "5. (Optional) Set up HTTPS:"
echo "   - Point your domain to: $PUBLIC_IP"
echo "   - Run: sudo certbot --nginx -d your-domain.com"
echo ""
echo "6. (Optional) Use AWS RDS instead of SQLite:"
echo "   - Create RDS instance in AWS Console"
echo "   - Update DB_TYPE, DB_HOST, DB_USER, DB_PASSWORD in .env"
echo "   - Add pymysql or psycopg2-binary to requirements.txt"
echo ""
echo -e "${CYAN}====================================${NC}"
echo "Service Status:"
sudo systemctl status "$APP_NAME" --no-pager | head -10
echo ""
echo "For detailed logs:"
echo "   sudo journalctl -u $APP_NAME -f"
echo -e "${CYAN}====================================${NC}"

log "Deployment completed successfully!"

# Start services
systemctl restart "$APP_NAME"
systemctl restart nginx

log "Services started successfully"

# Step 14: Verify services
log "Step 14: Verifying services..."
if systemctl is-active --quiet "$APP_NAME"; then
    log "✓ Gunicorn service is running"
else
    error "✗ Gunicorn service failed to start"
    systemctl status "$APP_NAME"
fi

if systemctl is-active --quiet nginx; then
    log "✓ Nginx is running"
else
    error "✗ Nginx failed to start"
fi

# Summary
echo ""
echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
log "Application directory: $APP_DIR"
log "Service name: $APP_NAME"
log "Logs: /var/log/policy-helper-ai/"
echo ""
echo "Next steps:"
echo "1. Edit $APP_DIR/.env with your configuration"
echo "2. (Optional) Set up SSL: sudo certbot --nginx"
echo "3. Test your application: visit http://YOUR_PUBLIC_IP"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u $APP_NAME -f"
echo "  sudo tail -f /var/log/nginx/error.log"
echo ""
echo "To restart the app:"
echo "  sudo systemctl restart $APP_NAME"
echo ""
