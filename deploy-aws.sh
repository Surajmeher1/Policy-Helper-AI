#!/bin/bash

# AWS EC2 Deployment Automation Script
# Policy Helper AI - Automated Setup
# Run this on your EC2 instance after SSH connection

set -e  # Exit on error

echo "================================"
echo "Policy Helper AI - AWS EC2 Setup"
echo "================================"
echo ""

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/var/www/policy-helper-ai"
APP_USER="ubuntu"
APP_NAME="policy-helper-ai"
GITHUB_REPO="https://github.com/YOUR_USERNAME/Policy-Helper-AI.git"

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root (for sudo commands)
if [ "$EUID" -ne 0 ]; then 
    error "This script must be run with sudo"
    exit 1
fi

# Step 1: Update system
log "Step 1: Updating system packages..."
apt update
apt upgrade -y

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
    python3-certbot-nginx

log "Dependencies installed successfully"

# Step 3: Create app directory
log "Step 3: Setting up application directory..."
mkdir -p "$APP_DIR"
chown "$APP_USER:$APP_USER" "$APP_DIR"

# Step 4: Clone repository
log "Step 4: Cloning repository..."
sudo -u "$APP_USER" git clone "$GITHUB_REPO" "$APP_DIR" 2>/dev/null || {
    warn "Could not clone from GitHub. Make sure repository is public or credentials are set."
    warn "Continuing with local setup..."
}

# Step 5: Create virtual environment
log "Step 5: Creating Python virtual environment..."
sudo -u "$APP_USER" python3 -m venv "$APP_DIR/venv"

# Step 6: Install Python dependencies
log "Step 6: Installing Python packages..."
sudo -u "$APP_USER" bash -c "source $APP_DIR/venv/bin/activate && \
    pip install --upgrade pip && \
    pip install -r $APP_DIR/requirements.txt"

log "Python packages installed successfully"

# Step 7: Create instance directory for database
log "Step 7: Creating instance directory for SQLite database..."
mkdir -p "$APP_DIR/instance"
chown "$APP_USER:$APP_USER" "$APP_DIR/instance"
chmod 755 "$APP_DIR/instance"

# Step 8: Create Gunicorn systemd service
log "Step 8: Creating Gunicorn systemd service..."
cat > "/etc/systemd/system/${APP_NAME}.service" << 'EOF'
[Unit]
Description=Policy Helper AI Flask Application
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/var/www/policy-helper-ai
Environment="PATH=/var/www/policy-helper-ai/venv/bin"
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

# Step 9: Create logs directory
log "Step 9: Creating logs directory..."
mkdir -p /var/log/policy-helper-ai
chown "$APP_USER:$APP_USER" /var/log/policy-helper-ai
chmod 755 /var/log/policy-helper-ai

# Step 10: Configure Nginx
log "Step 10: Configuring Nginx..."
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

# Step 11: Enable Nginx site
log "Step 11: Enabling Nginx site..."
ln -sf "/etc/nginx/sites-available/${APP_NAME}" "/etc/nginx/sites-enabled/${APP_NAME}"
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
if nginx -t > /dev/null 2>&1; then
    log "Nginx configuration is valid"
else
    error "Nginx configuration test failed!"
    exit 1
fi

# Step 12: Create .env file template
log "Step 12: Creating .env file..."
if [ ! -f "$APP_DIR/.env" ]; then
    cat > "$APP_DIR/.env" << 'EOF'
FLASK_ENV=production
FLASK_APP=app
SECRET_KEY=CHANGE_THIS_TO_A_RANDOM_STRING
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
EOF
    chown "$APP_USER:$APP_USER" "$APP_DIR/.env"
    chmod 600 "$APP_DIR/.env"
    
    warn "Please edit $APP_DIR/.env with your configuration"
    warn "Generate a secure SECRET_KEY: python3 -c \"import secrets; print(secrets.token_hex(32))\""
else
    log ".env file already exists"
fi

# Step 13: Enable and start services
log "Step 13: Enabling and starting services..."
systemctl daemon-reload
systemctl enable "$APP_NAME"
systemctl enable nginx

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
