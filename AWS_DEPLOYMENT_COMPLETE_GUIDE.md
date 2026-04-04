# AWS Complete A-Z Deployment Guide for Policy Helper AI

## Table of Contents
1. [Pre-Deployment Planning](#pre-deployment-planning)
2. [AWS Account & Prerequisites Setup](#aws-account--prerequisites-setup)
3. [Step-by-Step Deployment](#step-by-step-deployment)
4. [Post-Deployment Configuration](#post-deployment-configuration)
5. [Monitoring & Maintenance](#monitoring--maintenance)
6. [Troubleshooting](#troubleshooting)
7. [Cost Optimization](#cost-optimization)

---

## Pre-Deployment Planning

### A. Environment Variables & Secrets
Before deployment, gather these required environment variables:

1. **API Keys**
   - `GROQ_API_KEY` - Get from https://console.groq.com
   - `HF_TOKEN` - Get from https://huggingface.co/settings/tokens

2. **Email Configuration** (Optional but recommended)
   - `MAIL_SERVER` - Default: smtp.gmail.com
   - `MAIL_PORT` - Default: 587
   - `MAIL_USERNAME` - Your Gmail address
   - `MAIL_PASSWORD` - Gmail App Password (not regular password)

3. **Flask Security**
   - `SECRET_KEY` - Generate: `python3 -c "import secrets; print(secrets.token_hex(32))"`
   - `FLASK_ENV` - Set to "production" for AWS

4. **AWS RDS (Optional - for production database)**
   - `DB_HOST` - RDS endpoint
   - `DB_USER` - Database username
   - `DB_PASSWORD` - Database password
   - `DB_NAME` - Database name

### B. What You Need
- AWS free tier account (new: $300 free credits for 12 months)
- Domain name (optional, can use Elastic IP + Elastic DNS)
- SSH key pair for EC2
- Local copy of the project

---

## AWS Account & Prerequisites Setup

### Step 1: Create AWS Account (5 minutes)

1. Go to https://aws.amazon.com
2. Click **"Create an AWS Account"**
3. Sign up with email and credit card (free tier = no charges for 12 months)
4. Verify email and phone
5. Choose **"Personal"** account type
6. Select **AWS Free Tier** plan

### Step 2: Create SSH Key Pair (5 minutes)

1. Go to **AWS Console** → **EC2 Dashboard**
2. On left sidebar → **Key Pairs**
3. Click **"Create key pair"**
   - **Name**: `policy-helper-ai-key`
   - **Type**: RSA
   - **Format**: .pem
4. Click **Create** → Download file and save securely
5. Do NOT share this key

**On Windows:**
```powershell
Get-Item policy-helper-ai-key.pem | ForEach-Object { icacls $_ /inheritance:r /grant:r "%username%:F" }
```

**On Linux/Mac:**
```bash
chmod 400 policy-helper-ai-key.pem
```

### Step 3: Create IAM User (5 minutes)

1. Go to **AWS Console** → **IAM**
2. Click **"Users"** → **"Create user"**
   - **Name**: `policy-helper-ai-deploy`
3. Next → "Attach policies directly"
4. Select policies:
   - `AmazonEC2FullAccess`
   - `AmazonRDSFullAccess` (if using RDS)
   - `AmazonS3FullAccess` (for file uploads)
   - `CloudWatchFullAccess`
5. Create user

---

## Step-by-Step Deployment

### Step 4: Launch EC2 Instance (10 minutes)

#### Option A: Free Tier (T2.Micro - $0/month)
Good for: Testing, low traffic (< 10 concurrent users)

Go to **AWS EC2 Dashboard** → **Launch Instance**

**Configuration:**
```
Name: policy-helper-ai
OS: Ubuntu Server 24.04 LTS (Free tier eligible)
Instance Type: t2.micro
Key Pair: policy-helper-ai-key
Network: Default VPC
Auto-assign IP: Enable
Storage: 20GB gp3 (Free tier: 30GB)
```

#### Option B: Recommended Production (T3.Medium - $30-40/month)
Good for: Production, moderate traffic (< 100 concurrent users)

**Configuration:**
```
Name: policy-helper-ai-prod
OS: Ubuntu Server 24.04 LTS
Instance Type: t3.medium (2 vCPU, 4GB RAM)
Key Pair: policy-helper-ai-key
Network: Default VPC
Auto-assign IP: Enable
Storage: 50GB gp3
```

**Security Group Configuration:**

Create new security group named `policy-helper-sg`:

```
Type          Protocol  Port    Source         Purpose
SSH           TCP       22      YOUR_IP_ONLY   → Restrict for security
HTTP          TCP       80      0.0.0.0/0      → Web traffic
HTTPS         TCP       443     0.0.0.0/0      → Encrypted traffic
```

**⚠️ IMPORTANT:** Replace `0.0.0.0/0` with your IP for SSH. Get your IP:
- Your IP: Run in terminal: `curl ifconfig.me` or `curl icanhazip.com`

Click **Launch Instance**. Wait 2-3 minutes for instance to start.

### Step 5: Connect to EC2 Instance (5 minutes)

**Windows (PowerShell):**
```powershell
# Set key permissions
icacls policy-helper-ai-key.pem /inheritance:r /grant:r "%username%:F"

# Connect (replace INSTANCE_IP)
ssh -i policy-helper-ai-key.pem ubuntu@INSTANCE_IP
```

**Linux/Mac:**
```bash
ssh -i policy-helper-ai-key.pem ubuntu@INSTANCE_IP
```

If successful, you'll see a Ubuntu prompt: `ubuntu@ip-xxx:~$`

### Step 6: Install System Dependencies (10 minutes)

After SSH connection, run these commands:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11 and dependencies
sudo apt install -y \
    python3 python3-pip python3-venv \
    git build-essential curl wget \
    nginx certbot python3-certbot-nginx

# Verify installations
python3 --version
pip3 --version
nginx -v
```

### Step 7: Clone Repository & Setup Application (15 minutes)

```bash
# Create app directory
sudo mkdir -p /var/www/policy-helper-ai
sudo chown ubuntu:ubuntu /var/www/policy-helper-ai
cd /var/www/policy-helper-ai

# Clone repository (HTTPS - no SSH key needed)
git clone https://github.com/YOUR_USERNAME/Policy-Helper-AI.git .
# OR if private, use Personal Access Token:
# git clone https://YOUR_TOKEN@github.com/YOUR_USERNAME/Policy-Helper-AI.git .

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Create database directory
mkdir -p instance
chmod 755 instance
```

### Step 8: Configure Environment Variables (5 minutes)

Create `.env` file with your secrets:

```bash
nano .env
```

Paste the following and update with your values:

```env
# Flask Configuration
FLASK_ENV=production
FLASK_APP=app.py
SECRET_KEY=your_random_secret_key_here_CHANGE_THIS

# API Keys (REQUIRED)
GROQ_API_KEY=your_groq_api_key_here
HF_TOKEN=your_huggingface_token_here
HF_MODEL_NAME=facebook/bart-large-cnn

# Email Configuration (Optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password-here

# Database (Optional - use RDS for production)
# DB_TYPE=mysql
# DB_HOST=your-rds-endpoint.amazonaws.com
# DB_USER=admin
# DB_PASSWORD=secure_password
# DB_NAME=policy_helper_ai
```

**To generate SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

**To get Gmail App Password:**
1. Go to https://myaccount.google.com/apppasswords
2. Select Mail and Windows/Mac/Linux
3. Copy the password (16 characters)

Save file: Press **Ctrl+O**, **Enter**, **Ctrl+X**

Set correct permissions:
```bash
chmod 600 .env
```

### Step 9: Test Application Locally (5 minutes)

```bash
# Activate venv if not already
source venv/bin/activate

# Export environment variables
export $(cat .env | xargs)

# Run Flask development server
flask run --host=0.0.0.0 --port=5000
```

Visit: `http://INSTANCE_IP:5000` in browser

**Expected:** Landing page loads

Press **Ctrl+C** to stop development server.

### Step 10: Create Gunicorn Systemd Service (5 minutes)

```bash
# Create systemd service file
sudo nano /etc/systemd/system/policy-helper-ai.service
```

Paste this configuration:

```ini
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
```

Save file: **Ctrl+O**, **Enter**, **Ctrl+X**

Create logs directory:
```bash
sudo mkdir -p /var/log/policy-helper-ai
sudo chown ubuntu:ubuntu /var/log/policy-helper-ai
```

Enable and start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable policy-helper-ai
sudo systemctl start policy-helper-ai
```

Check status:
```bash
sudo systemctl status policy-helper-ai
```

**Should show:** `active (running)`

### Step 11: Configure Nginx Reverse Proxy (5 minutes)

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/policy-helper-ai
```

Paste this configuration:

```nginx
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;
    
    client_max_body_size 50M;
    
    # Redirect all HTTP to HTTPS (after SSL setup)
    # return 301 https://$host$request_uri;
    
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
```

Save file: **Ctrl+O**, **Enter**, **Ctrl+X**

Enable site:
```bash
sudo ln -sf /etc/nginx/sites-available/policy-helper-ai /etc/nginx/sites-enabled/policy-helper-ai
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### Step 12: Verify Deployment (5 minutes)

```bash
# Check services running
sudo systemctl status policy-helper-ai nginx

# Check logs
tail -f /var/log/policy-helper-ai/error.log

# Test socket
ls -la /run/policy-helper-ai.sock

# Test Nginx
curl http://localhost

# Get instance IP
ec2-metadata --public-ipv4
```

Visit in browser: `http://YOUR_INSTANCE_IP`

**Expected:** Application loads successfully

---

## Post-Deployment Configuration

### Step 13: Set Up HTTPS/SSL (5 minutes)

**If you have a domain:**

```bash
# Stop Nginx temporarily
sudo systemctl stop nginx

# Get SSL certificate
sudo certbot certonly --standalone -d your-domain.com

# Update Nginx config with SSL
sudo nano /etc/nginx/sites-available/policy-helper-ai
```

Update configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2 default_server;
    listen [::]:443 ssl http2 default_server;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    client_max_body_size 50M;
    
    location / {
        proxy_pass http://unix:/run/policy-helper-ai.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_read_timeout 120s;
        proxy_connect_timeout 120s;
    }
    
    location /static/ {
        alias /var/www/policy-helper-ai/static/;
        expires 30d;
    }
}
```

Restart services:
```bash
sudo systemctl start nginx
sudo systemctl restart policy-helper-ai

# Auto-renew certificates
sudo systemctl enable certbot.timer
```

### Step 14: Set Up Database Backup (Optional but Recommended)

**For SQLite (current setup):**

```bash
# Create backup directory
mkdir -p /backups/policy-helper-ai
cd /backups/policy-helper-ai

# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups/policy-helper-ai"
APP_DIR="/var/www/policy-helper-ai"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup database
cp "$APP_DIR/instance/users.db" "$BACKUP_DIR/users.db.$DATE"

# Keep only last 7 days
find "$BACKUP_DIR" -type f -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x backup.sh

# Add to crontab for daily backups at 2 AM
(crontab -l 2>/dev/null; echo "0 2 * * * /backups/policy-helper-ai/backup.sh") | crontab -
```

**For RDS (recommended for production):**
```bash
# AWS automatically handles backups. Enable automated backups:
# AWS Console → RDS → Databases → Modify → Backup retention: 7 days
```

### Step 15: Set Up CloudWatch Monitoring (Optional)

```bash
# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i -E ./amazon-cloudwatch-agent.deb

# Configure for application logs
sudo tee /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json > /dev/null << 'EOF'
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/policy-helper-ai/error.log",
            "log_group_name": "/aws/ec2/policy-helper-ai",
            "log_stream_name": "{instance_id}-error"
          },
          {
            "file_path": "/var/log/policy-helper-ai/access.log",
            "log_group_name": "/aws/ec2/policy-helper-ai",
            "log_stream_name": "{instance_id}-access"
          }
        ]
      }
    }
  }
}
EOF

# Start agent
sudo systemctl enable amazon-cloudwatch-agent
sudo systemctl start amazon-cloudwatch-agent
```

---

## Monitoring & Maintenance

### Daily Health Checks

```bash
# Check application status
sudo systemctl status policy-helper-ai
sudo systemctl status nginx

# Check logs
tail -20 /var/log/policy-helper-ai/error.log
tail -20 /var/log/policy-helper-ai/access.log

# Check system resources
free -h
df -h
ps aux | grep gunicorn

# Check database
du -h /var/www/policy-helper-ai/instance/users.db
```

### Weekly Tasks

```bash
# Check for updates
sudo apt update
sudo apt list --upgradable

# Review access logs for suspicious activity
grep "401\|403\|500" /var/log/policy-helper-ai/access.log

# Check SSL certificate expiry
sudo certbot certificates
```

### Monthly Tasks

```bash
# Update system packages
sudo apt upgrade -y

# Review and clean old logs
sudo find /var/log/policy-helper-ai -mtime +30 -delete

# Update application
cd /var/www/policy-helper-ai
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart policy-helper-ai
```

### Updating Application

```bash
cd /var/www/policy-helper-ai
source venv/bin/activate

# Pull latest code
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Restart application
sudo systemctl restart policy-helper-ai

# Verify
sudo systemctl status policy-helper-ai
```

---

## Troubleshooting

### Issue: Application not loading (500 error)

```bash
# Check logs
tail -50 /var/log/policy-helper-ai/error.log

# Check service status
sudo systemctl status policy-helper-ai

# Restart service
sudo systemctl restart policy-helper-ai

# Check Nginx
sudo nginx -t
sudo systemctl restart nginx
```

### Issue: Gunicorn socket not found

```bash
# Check if service is running
sudo systemctl status policy-helper-ai

# Restart service
sudo systemctl restart policy-helper-ai

# Check socket
ls -la /run/policy-helper-ai.sock

# Check logs
sudo journalctl -u policy-helper-ai -n 50
```

### Issue: High memory/CPU usage

```bash
# Check process resources
ps aux | grep gunicorn

# Monitor in real-time
top -b -n 1 | grep gunicorn

# Increase worker count (if available memory)
sudo nano /etc/systemd/system/policy-helper-ai.service
# Change: --workers 3 to --workers 5 or 7

sudo systemctl daemon-reload
sudo systemctl restart policy-helper-ai
```

### Issue: Database locked error

```bash
# Check processes accessing database
lsof /var/www/policy-helper-ai/instance/users.db

# Restart application
sudo systemctl restart policy-helper-ai

# If persistent, migrate to RDS
```

### Issue: Certificate renewal failing

```bash
# Check certificate status
sudo certbot certificates

# Manual renewal
sudo certbot renew --dry-run

# Force renewal
sudo certbot renew --force-renewal
```

---

## Cost Optimization

### AWS Free Tier

- **EC2**: 750 hours/month t2.micro = FREE
- **Storage**: 30GB EBS = FREE
- **Data Transfer**: Within region = FREE
- **Elastic IP**: FREE (if associated with instance)

**Estimated costs after free tier:**
- t2.micro: ~$9-10/month
- t3.medium: ~$35-40/month
- Additional storage: ~$0.10/GB/month
- Data transfer out: ~$0.09/GB

### Cost-Saving Tips

1. **Use Free Tier resources**
   - t2.micro for development/testing
   - 30GB EBS storage
   - Stop instance when not needed

2. **Optimize Gunicorn workers**
   - Start with 2 workers for t2.micro
   - Increase based on actual load
   - 1 worker = ~50MB RAM

3. **Use spot instances** (for non-critical)
   - Up to 70% cheaper than on-demand
   - Good for development/CI/CD

4. **Set up auto-scaling** (for production)
   - Scale up during peak hours
   - Scale down during off-hours

5. **Database optimization**
   - SQLite: FREE (file-based)
   - RDS micro: ~$15-20/month
   - Only pay for what you use

---

## Production Checklist

- [ ] Domain registered and DNS configured
- [ ] SSL certificate installed and auto-renewing
- [ ] Environment variables set (.env file)
- [ ] API keys obtained (GROQ, Hugging Face)
- [ ] Email server configured (optional)
- [ ] Backup strategy implemented
- [ ] CloudWatch monitoring enabled
- [ ] Security group properly configured
- [ ] SSH access hardened (only your IP)
- [ ] Application logs monitored
- [ ] Database maintenance plan in place
- [ ] Load testing completed (if needed)
- [ ] Monitoring alerts configured
- [ ] Disaster recovery plan documented

---

## Additional Resources

- **AWS Console**: https://console.aws.amazon.com
- **AWS Free Tier**: https://aws.amazon.com/free
- **EC2 Documentation**: https://docs.aws.amazon.com/ec2
- **Certbot Documentation**: https://certbot.eff.org
- **Nginx Documentation**: https://nginx.org/en/docs
- **Gunicorn Documentation**: https://docs.gunicorn.org

---

## Quick Reference Commands

```bash
# SSH Connection
ssh -i policy-helper-ai-key.pem ubuntu@YOUR_IP

# Check service status
sudo systemctl status policy-helper-ai

# View logs
tail -f /var/log/policy-helper-ai/error.log

# Restart application
sudo systemctl restart policy-helper-ai

# Restart web server
sudo systemctl restart nginx

# Update application
cd /var/www/policy-helper-ai && git pull origin main && sudo systemctl restart policy-helper-ai

# Check system resources
free -h && df -h && ps aux | grep gunicorn

# Check SSL certificate
sudo certbot certificates
```

---

**Last Updated:** April 2026
**Version:** 1.0
**Status:** Production Ready
