#!/bin/bash
set -e

# Single Deploy Script for Policy Helper AI - AWS EC2 Ubuntu 22.04+
# Run as root: sudo bash deploy.sh

echo "=================================================="
echo "Policy Helper AI - Complete Production Deployment"
echo "=================================================="

APP_DIR="/var/www/policy-helper-ai"
REPO_URL="https://github.com/Surajmeher1/Policy-Helper-AI.git"

# 1. UPDATE SYSTEM
echo -e "\n[1/10] Updating system packages..."
apt-get update
apt-get upgrade -y
apt-get install -y curl wget git build-essential python3-dev python3-pip python3-venv nginx unzip net-tools

# 2. CREATE APPLICATION DIRECTORIES
echo -e "\n[2/10] Creating application directories..."
mkdir -p $APP_DIR
mkdir -p /var/log/gunicorn
mkdir -p /var/log/nginx
useradd -m -s /bin/bash www-data 2>/dev/null || true
chown -R www-data:www-data $APP_DIR
chown -R www-data:www-data /var/log/gunicorn

# 3. SETUP 4GB SWAP
echo -e "\n[3/10] Setting up 4GB swap..."
if [ ! -f /swapfile ]; then
    fallocate -l 4G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo "/swapfile none swap sw 0 0" >> /etc/fstab
    echo "vm.swappiness=10" >> /etc/sysctl.conf
    sysctl -p > /dev/null
    echo "✓ Swap configured"
else
    echo "✓ Swap already exists"
fi

# 4. CLONE/UPDATE REPOSITORY
echo -e "\n[4/10] Cloning repository..."
if [ -d "$APP_DIR/.git" ]; then
    cd $APP_DIR
    git pull origin main
else
    rm -rf $APP_DIR
    git clone $REPO_URL $APP_DIR
fi
chown -R www-data:www-data $APP_DIR

# 5. CREATE PYTHON VIRTUAL ENVIRONMENT
echo -e "\n[5/10] Creating Python virtual environment..."
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate

# 6. INSTALL DEPENDENCIES
echo -e "\n[6/10] Installing Python dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install gunicorn

# 7. CREATE .env FILE
echo -e "\n[7/10] Setting up environment variables..."
if [ ! -f $APP_DIR/.env ]; then
    cat > $APP_DIR/.env << 'ENVFILE'
FLASK_ENV=production
SECRET_KEY=change-this-to-a-random-secure-string
GROQ_API_KEY=your-groq-api-key-here
HF_TOKEN=your-huggingface-token-here
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
DB_TYPE=sqlite
ENVFILE
    echo "✓ Created .env file"
else
    echo "✓ .env file already exists"
fi
chown www-data:www-data $APP_DIR/.env
chmod 600 $APP_DIR/.env

# 8. CREATE SYSTEMD SERVICE FILE
echo -e "\n[8/10] Installing systemd service..."
cat > /etc/systemd/system/policy-helper-ai.service << 'SERVICEFILE'
[Unit]
Description=Policy Helper AI - Flask Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/policy-helper-ai
Environment="PATH=/var/www/policy-helper-ai/venv/bin"
ExecStart=/var/www/policy-helper-ai/venv/bin/gunicorn \
    --workers=2 \
    --worker-class=gthread \
    --threads=4 \
    --worker-connections=1000 \
    --bind=127.0.0.1:5000 \
    --timeout=120 \
    --access-logfile=/var/log/gunicorn/access.log \
    --error-logfile=/var/log/gunicorn/error.log \
    --log-level=info \
    app:app

Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/var/log/gunicorn /var/www/policy-helper-ai/instance

[Install]
WantedBy=multi-user.target
SERVICEFILE

systemctl daemon-reload
systemctl enable policy-helper-ai.service
echo "✓ Systemd service configured"

# 9. CREATE NGINX CONFIGURATION
echo -e "\n[9/10] Configuring Nginx..."
cat > /etc/nginx/sites-available/policy-helper-ai << 'NGINXFILE'
upstream policy_helper_ai {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    listen [::]:80;
    server_name _;
    client_max_body_size 50M;

    access_log /var/log/nginx/policy-helper-ai-access.log;
    error_log /var/log/nginx/policy-helper-ai-error.log;

    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    gzip on;
    gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss;
    gzip_min_length 1000;

    location / {
        proxy_pass http://policy_helper_ai;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $server_name;
        proxy_redirect off;
        
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }

    location /static/ {
        alias /var/www/policy-helper-ai/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /health {
        access_log off;
        proxy_pass http://policy_helper_ai;
    }
}
NGINXFILE

rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/policy-helper-ai /etc/nginx/sites-enabled/
nginx -t > /dev/null
systemctl enable nginx
systemctl restart nginx
echo "✓ Nginx configured"

# 10. CONFIGURE FIREWALL
echo -e "\n[10/10] Configuring firewall..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
echo "y" | ufw enable 2>/dev/null || true
echo "✓ Firewall configured"

# START SERVICES
echo -e "\n=================================================="
echo "Starting services..."
systemctl start policy-helper-ai
systemctl start nginx

# CHECK STATUS
sleep 2
echo ""
echo "=================================================="
echo "✓ DEPLOYMENT COMPLETE!"
echo "=================================================="
echo ""
echo "📝 NEXT STEPS:"
echo "1. Edit environment variables:"
echo "   sudo nano /var/www/policy-helper-ai/.env"
echo "   (Add your actual API keys)"
echo ""
echo "2. Restart service to apply changes:"
echo "   sudo systemctl restart policy-helper-ai"
echo ""
echo "📊 CHECK STATUS:"
echo "   sudo systemctl status policy-helper-ai"
echo "   sudo journalctl -u policy-helper-ai -f"
echo ""
echo "📋 VIEW LOGS:"
echo "   sudo tail -f /var/log/gunicorn/error.log"
echo "   sudo tail -f /var/log/nginx/policy-helper-ai-error.log"
echo ""
echo "🌐 Your app should be running at:"
echo "   http://<your-ec2-public-ip>"
echo ""
echo "⚠️  IMPORTANT: Update .env with your actual API keys!"
echo "=================================================="
