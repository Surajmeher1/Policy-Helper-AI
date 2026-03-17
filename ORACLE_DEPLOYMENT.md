# Deployment Guide - Oracle Cloud Always Free

Your project is now configured for deployment on **Oracle Cloud Always Free Tier**. This gives you up to 24GB RAM, 4 ARM CPUs, and 100GB storage - completely free!

## Prerequisites
1. Oracle Cloud account (free, no credit card for Always Free tier)
2. SSH key pair for instance access

## Step 1: Create Oracle Cloud Account
1. Go to [oracle.com/cloud/free](https://www.oracle.com/cloud/free/)
2. Click **"Sign Up"**
3. Complete the registration (no credit card charged)

## Step 2: Create a Compute Instance

1. In Oracle Cloud Console, go to **Compute** → **Instances**
2. Click **"Create Instance"**
3. Configure:
   - **Name**: `policy-helper-ai`
   - **Image**: Ubuntu 22.04 (or 24.04)
   - **Instance Shape**: Choose **"Ampere"** (ARM CPU) - this is free tier eligible
   - **Networking**: Create new VCN or use existing
   - **Public IP**: Assign one
   - **SSH Key**: Add your public SSH key

4. Click **"Create"** and wait for instance to be running

## Step 3: Connect to Your Instance

```bash
# SSH into your instance
ssh ubuntu@<your-instance-ip>

# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install -y python3 python3-pip python3-venv git
```

## Step 4: Clone and Deploy Your Project

```bash
# Clone your repository
git clone https://github.com/Surajmeher1/Policy-Helper-AI.git
cd Policy-Helper-AI

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file with your secrets
nano .env
# Add all required variables (copy from .env.example)
# Press Ctrl+X, Y, Enter to save

# Test the app
python app.py
# Should see: "Running on http://0.0.0.0:5000"
```

## Step 5: Set Up Systemd Service (Auto-Start)

Create `/etc/systemd/system/policy-helper.service`:

```bash
sudo nano /etc/systemd/system/policy-helper.service
```

Add this content:

```ini
[Unit]
Description=Policy Helper AI
After=network.target

[Service]
Type=notify
User=ubuntu
WorkingDirectory=/home/ubuntu/Policy-Helper-AI
ExecStart=/home/ubuntu/Policy-Helper-AI/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Save and enable:

```bash
sudo systemctl daemon-reload
sudo systemctl enable policy-helper
sudo systemctl start policy-helper
sudo systemctl status policy-helper
```

## Step 6: Set Up Nginx as Reverse Proxy

```bash
# Install Nginx
sudo apt install -y nginx

# Create Nginx config
sudo nano /etc/nginx/sites-available/policy-helper
```

Add this content:

```nginx
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Enable it:

```bash
sudo ln -s /etc/nginx/sites-available/policy-helper /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Step 7: Configure Firewall

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## Step 8: Set Up HTTPS (Optional but Recommended)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get free SSL certificate (replace with your domain)
sudo certbot certonly --standalone -d your-domain.com

# Update Nginx to use HTTPS
sudo nano /etc/nginx/sites-available/policy-helper
```

Update to use SSL:

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

Restart Nginx:

```bash
sudo systemctl restart nginx
```

## Step 9: Configure Database (Optional)

For production, upgrade from SQLite to PostgreSQL:

```bash
# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql <<EOF
CREATE DATABASE policy_helper;
CREATE USER policy_user WITH PASSWORD 'your_secure_password';
ALTER ROLE policy_user SET client_encoding TO 'utf8';
ALTER ROLE policy_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE policy_user SET default_transaction_deferrable TO on;
ALTER ROLE policy_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE policy_helper TO policy_user;
\q
EOF
```

Update `app.py`:

```python
# Instead of SQLite:
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

# Use PostgreSQL:
import os
db_user = os.getenv('DB_USER', 'policy_user')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST', 'localhost')
db_name = os.getenv('DB_NAME', 'policy_helper')
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_password}@{db_host}/{db_name}'
```

Add to `.env`:

```
DB_USER=policy_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_NAME=policy_helper
```

Install driver:

```bash
pip install psycopg2-binary
```

## Monitor Your App

```bash
# View service logs
sudo journalctl -u policy-helper -n 50 -f

# View Nginx logs
tail -f /var/log/nginx/error.log
tail -f /var/log/nginx/access.log

# Check resource usage
free -h
df -h
top
```

## Cost and Resources

| Resource | Limit | Cost |
|----------|-------|------|
| Compute Instances | 4 ARM vCPUs | Free |
| RAM | 24GB total | Free |
| Storage | 100GB total | Free |
| Network | Unlimited ingress | Free |
| Database | PostgreSQL | Free |
| HTTP/HTTPS | Unlimited | Free |

**Total Cost: $0/month forever!**

## Backup and Recovery

```bash
# Automated backups
sudo apt install -y xfsdump

# Manual backup
tar -czf ~/backup-$(date +%Y%m%d).tar.gz ~/Policy-Helper-AI

# Restore
tar -xzf ~/backup-*.tar.gz
```

## Troubleshooting

**App not accessible?**
```bash
# Check service status
sudo systemctl status policy-helper

# Check if port 5000 is listening
sudo netstat -tlnp | grep 5000

# Check Nginx
sudo nginx -t
sudo systemctl restart nginx
```

**Memory issues?**
```bash
# Check RAM usage
free -h

# Reduce model size or use optimization
# Consider using smaller models than facebook/bart-large-cnn
```

**App crashes?**
```bash
# Check logs
sudo journalctl -u policy-helper -n 100 -f

# Restart service
sudo systemctl restart policy-helper
```

**Need more info?** Check [Oracle Cloud Always Free Docs](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetieroverview.htm)
