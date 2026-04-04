#!/bin/bash

# Update Script for AWS EC2
# Use this to pull latest code and restart application

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

APP_DIR="/var/www/policy-helper-ai"
APP_NAME="policy-helper-ai"

echo "================================"
echo "Policy Helper AI - Update Script"
echo "================================"
echo ""

# Navigate to app directory
if [ ! -d "$APP_DIR" ]; then
    error "Application directory not found: $APP_DIR. Deploy the app first."
    exit 1
fi

cd "$APP_DIR"

log "Current directory: $(pwd)"

if [ ! -f "$APP_DIR/requirements.txt" ]; then
    error "requirements.txt not found in $APP_DIR. The deployment looks incomplete. Re-run the deployment script or restore the repository files first."
    exit 1
fi

# Pull latest code
log "Pulling latest code from repository..."
git pull origin main

if [ $? -ne 0 ]; then
    error "Failed to pull from repository"
    exit 1
fi

log "✓ Code updated successfully"

# Update dependencies
log "Updating Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

log "✓ Dependencies updated successfully"

# Restart application
log "Restarting application..."
sudo systemctl restart "$APP_NAME"

# Verify
if sudo systemctl is-active --quiet "$APP_NAME"; then
    log "✓ Application restarted successfully"
else
    error "Failed to restart application"
    sudo systemctl status "$APP_NAME"
    exit 1
fi

echo ""
echo "================================"
echo "Update Complete!"
echo "================================"
echo ""
log "Application is running at the latest version"
echo ""
