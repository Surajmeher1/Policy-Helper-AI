#!/bin/bash
set -e

# Production Deployment Script for Policy Helper AI
# Run on Ubuntu 22.04+ EC2 instance as root

echo "=================================================="
echo "Policy Helper AI - Production Deployment"
echo "=================================================="

# 1. UPDATE SYSTEM
echo -e "\n[1/10] Updating system packages..."
apt-get update
apt-get upgrade -y
apt-get install -y curl wget git build-essential python3-dev python3-pip python3-venv nginx supervisor unzip net-tools

# 2. CREATE APPLICATION USER AND DIRECTORIES
echo -e "\n[2/10] Creating application directories..."
useradd -m -s /bin/bash www-data 2>/dev/null || true
mkdir -p /var/www/policy-helper-ai
mkdir -p /var/log/gunicorn
mkdir -p /var/log/nginx
chown -R www-data:www-data /var/www/policy-helper-ai
chown -R www-data:www-data /var/log/gunicorn

# 3. SETUP SWAP (4GB)
echo -e "\n[3/10] Setting up 4GB swap..."
if [ ! -f /swapfile ]; then
    fallocate -l 4G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo "/swapfile none swap sw 0 0" >> /etc/fstab
    echo "vm.swappiness=10" >> /etc/sysctl.conf
    sysctl -p
    echo "Swap setup complete"
else
    echo "Swap already exists"
fi

# 4. CLONE REPOSITORY (update URL if needed)
echo -e "\n[4/10] Cloning repository..."
cd /var/www/policy-helper-ai
if [ -d .git ]; then
    git pull origin main
else
    git clone https://github.com/Surajmeher1/Policy-Helper-AI.git . 2>/dev/null || {
        echo "Git clone failed. Please ensure repo is accessible."
        echo "Manually clone: git clone <your-repo-url> /var/www/policy-helper-ai"
        exit 1
    }
fi
chown -R www-data:www-data /var/www/policy-helper-ai

# 5. CREATE PYTHON VIRTUAL ENVIRONMENT
echo -e "\n[5/10] Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# 6. INSTALL PYTHON DEPENDENCIES
echo -e "\n[6/10] Installing Python dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install gunicorn

# 7. CREATE .env FILE
echo -e "\n[7/10] Setting up environment variables..."
if [ ! -f /var/www/policy-helper-ai/.env ]; then
    cat > /var/www/policy-helper-ai/.env << 'EOF'
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
GROQ_API_KEY=your-groq-api-key-here
HF_TOKEN=your-huggingface-token-here
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
EOF
    echo "Created .env file. IMPORTANT: Edit /var/www/policy-helper-ai/.env with your actual keys"
else
    echo ".env file already exists"
fi
chown www-data:www-data /var/www/policy-helper-ai/.env
chmod 600 /var/www/policy-helper-ai/.env

# 8. SETUP SYSTEMD SERVICE
echo -e "\n[8/10] Installing systemd service..."
cp policy-helper-ai.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable policy-helper-ai.service

# 9. SETUP NGINX
echo -e "\n[9/10] Configuring Nginx..."
cp policy-helper-ai.nginx /etc/nginx/sites-available/policy-helper-ai
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/policy-helper-ai /etc/nginx/sites-enabled/

# Test nginx config
nginx -t
systemctl enable nginx
systemctl restart nginx

# 10. CONFIGURE FIREWALL
echo -e "\n[10/10] Configuring firewall..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
echo "y" | ufw enable 2>/dev/null || true

# START SERVICES
echo -e "\n=================================================="
echo "Starting services..."
systemctl start policy-helper-ai
systemctl start nginx

# VERIFY
echo -e "\n=================================================="
echo "Deployment Complete!"
echo "=================================================="
echo ""
echo "⚠️  IMPORTANT: Edit environment variables:"
echo "   sudo nano /var/www/policy-helper-ai/.env"
echo ""
echo "Start service:"
echo "   sudo systemctl start policy-helper-ai"
echo ""
echo "Check status:"
echo "   sudo systemctl status policy-helper-ai"
echo "   sudo journalctl -u policy-helper-ai -f"
echo ""
echo "Check logs:"
echo "   sudo tail -f /var/log/gunicorn/error.log"
echo "   sudo tail -f /var/log/nginx/policy-helper-ai-error.log"
echo ""
echo "Your app should be running on: http://<your-ec2-ip>"
echo "=================================================="
