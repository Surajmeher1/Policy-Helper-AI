# AWS EC2 Deployment Guide - Policy Helper AI

This guide will help you deploy Policy Helper AI to AWS EC2 for under $10/month.

## Prerequisites
- AWS account (new accounts get 12 months free tier)
- SSH key pair
- Domain name (optional, or use Elastic IP)

---

## Step 1: Create AWS Account & Set Up Free Tier

1. Go to [aws.amazon.com](https://aws.amazon.com)
2. Click **"Create an AWS Account"**
3. Complete registration with email and credit card (not charged for free tier)
4. Choose **"Personal"** account type
5. Select the **Free Tier** plan

> **Free Tier Benefits** (12 months):
> - 750 hours/month of **t2.micro** or **t3.micro** EC2
> - 30GB of storage
> - Data transfer within region is free
> - Perfect for low-traffic apps

---

## Step 2: Create EC2 Instance

### 2.1 Launch Instance

1. Go to **AWS Console** → **EC2** → **Instances**
2. Click **"Launch Instance"**

### 2.2 Configure Instance

**Step 1: Name and Operating System**
- **Name**: `policy-helper-ai`
- **OS Image**: Ubuntu Server 24.04 LTS (free tier eligible)
  - AMI: `ami-0c02fb55956c7d316` (us-east-1)

**Step 2: Instance Type**
- **Instance Type**: `t3.medium` (recommended for ML model)
  - (or `t2.micro` for minimum cost, but slower)
  - **Note**: If staying in free tier, use `t2.micro`

**Step 3: Key Pair**
- **Create new key pair**
  - Name: `policy-helper-ai-key`
  - Type: RSA
  - Format: `.pem`
- **Download and save securely** (you won't be able to download again)

**Step 4: Network Settings**
- **VPC**: Default VPC
- **Subnet**: Default subnet in us-east-1a
- **Auto-assign public IP**: ✓ Enable
- **Firewall (Security Group)**: Create new
  - **Security Group Name**: `policy-helper-sg`
  - **Description**: `Security group for Policy Helper AI`

**Add Rules:**
```
Type          Protocol  Port Range  Source
SSH           TCP       22          0.0.0.0/0      (your IP only for security)
HTTP          TCP       80          0.0.0.0/0
HTTPS         TCP       443         0.0.0.0/0
```

**Step 5: Storage**
- **Volume Type**: gp3
- **Size**: 20GB (free tier includes 30GB)
- **Encrypted**: No (free tier)
- **Delete on Termination**: ✓ Yes

**Step 6: Advanced Details**
- Leave all defaults
- Click **"Launch Instance"**

### 2.3 Wait for Instance to Start
- Instance should show **"Running"** within 1-2 minutes
- Note the **Public IPv4 address** (you'll need this)

---

## Step 3: Connect to Your Instance

### 3.1 SSH Connection (Linux/Mac)

```bash
# Change permissions on key
chmod 400 policy-helper-ai-key.pem

# SSH into instance
ssh -i policy-helper-ai-key.pem ubuntu@<YOUR_PUBLIC_IP>
```

### 3.2 SSH Connection (Windows)
- Use **PuTTY** or **Windows Terminal** with OpenSSH
- Or use AWS Systems Manager Session Manager in console

---

## Step 4: Install Dependencies

```bash
# Update system packages
sudo apt update
sudo apt upgrade -y

# Install Python, pip, and system dependencies
sudo apt install -y python3 python3-pip python3-venv git build-essential

# Install Nginx (for reverse proxy)
sudo apt install -y nginx

# Install systemd service manager (already installed by default)
```

---

## Step 5: Clone and Set Up Your Application

```bash
# Create app directory
sudo mkdir -p /var/www/policy-helper-ai
sudo chown ubuntu:ubuntu /var/www/policy-helper-ai
cd /var/www/policy-helper-ai

# Clone repository
git clone https://github.com/YOUR_USERNAME/Policy-Helper-AI.git . 
# (or upload your project files via SCP/SFTP)

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create instance directory for database
mkdir -p instance
```

---

## Step 6: Configure Gunicorn

### 6.1 Create Gunicorn Service File

```bash
sudo nano /etc/systemd/system/policy-helper-ai.service
```

**Paste this content:**

```ini
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
    --access-logfile - \
    --error-logfile - \
    app:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 6.2 Enable and Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable policy-helper-ai
sudo systemctl start policy-helper-ai

# Verify it's running
sudo systemctl status policy-helper-ai
```

---

## Step 7: Configure Nginx

### 7.1 Create Nginx Config

```bash
sudo nano /etc/nginx/sites-available/policy-helper-ai
```

**Paste this content:**

```nginx
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
```

### 7.2 Enable Site and Test

```bash
# Enable the site
sudo ln -sf /etc/nginx/sites-available/policy-helper-ai \
    /etc/nginx/sites-enabled/policy-helper-ai

# Remove default site
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx config
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

---

## Step 8: Set Up Environment Variables

```bash
# Create .env file
nano /var/www/policy-helper-ai/.env
```

**Add your configuration (example):**

```env
FLASK_ENV=production
FLASK_APP=app
SECRET_KEY=your-secret-key-here-change-this
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

**Important**: Change `SECRET_KEY` to a random string:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## Step 9: Set Up HTTPS (SSL/TLS)

### Using Let's Encrypt (Free)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get certificate (replace with your domain)
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
sudo systemctl restart nginx
```

---

## Step 10: Set Up Static IP (Optional but Recommended)

To keep the same IP address:

1. Go to **AWS Console** → **EC2** → **Elastic IPs**
2. Click **"Allocate Elastic IP address"**
3. Select your instance
4. Associate the Elastic IP

**Cost**: Free if associated with running instance

---

## Step 11: Database Setup

### If Using SQLite (Current Setup)

```bash
# Ensure instance directory exists
mkdir -p /var/www/policy-helper-ai/instance

# Give proper permissions
sudo chown -R ubuntu:ubuntu /var/www/policy-helper-ai/instance
chmod 755 /var/www/policy-helper-ai/instance
```

### If Migrating to RDS PostgreSQL (Optional)

See "RDS Setup" section below.

---

## Step 12: Verify Deployment

```bash
# Check Gunicorn is running
sudo systemctl status policy-helper-ai

# Check Nginx is running
sudo systemctl status nginx

# View logs
sudo journalctl -u policy-helper-ai -f
sudo tail -f /var/log/nginx/error.log
```

**Visit your app**: Open browser to `http://<YOUR_PUBLIC_IP>` or `https://your-domain.com`

---

## Cost Breakdown (Monthly)

| Service | Free Tier | Cost |
|---------|-----------|------|
| **EC2 t2.micro** | 750 hrs/month | $0 |
| **t3.medium** (if needed) | Not free | ~$20 |
| **Data Transfer** | 100GB/month (region) | $0 in region |
| **Elastic IP** | Free if in-use | $0 |
| **RDS PostgreSQL** | 12 months free micro | $0 or ~$15 |
| **S3 Storage** | 5GB free | $0 (10GB) |
| **Total** | | **~$0-5/month** |

---

## Monitoring & Troubleshooting

### Check Application Status

```bash
# View gunicorn logs
sudo journalctl -u policy-helper-ai -n 50 -f

# View nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Check instance metrics in AWS Console
# EC2 → Instance → Monitoring
```

### Restart Application

```bash
sudo systemctl restart policy-helper-ai
sudo systemctl restart nginx
```

### Update Application

```bash
cd /var/www/policy-helper-ai
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart policy-helper-ai
```

---

## Auto-Scaling Setup (Optional)

For higher traffic, set up Load Balancer + Auto Scaling Group:

1. **Create AMI** from your configured instance
2. **Create Launch Template** with this AMI
3. **Create Auto Scaling Group** (2-4 instances)
4. **Create Application Load Balancer** (ALB)
5. **Configure Target Group** to ASG

See AWS documentation for Auto Scaling setup.

---

## RDS Setup (if migrating from SQLite)

If you want a managed database:

1. **AWS Console** → **RDS** → **Create database**
2. **Engine**: PostgreSQL 15
3. **Instance Class**: db.t3.micro (free tier eligible)
4. **Storage**: 20GB
5. **DB Name**: `policy_helper`
6. **Master Username**: `admin`
7. **Auto Backup**: 7 days

Update your app:
```python
# In app.py or config
SQLALCHEMY_DATABASE_URI = "postgresql://admin:password@endpoint:5432/policy_helper"
```

Then run migrations:
```bash
flask db upgrade
```

---

## Security Best Practices

✅ **Do This**:
- Keep security group rules minimal (only needed ports)
- Restrict SSH to your IP: `YOUR_IP/32` not `0.0.0.0/0`
- Use strong `SECRET_KEY`
- Keep system packages updated: `sudo apt update && sudo apt upgrade`
- Enable HTTPS/SSL (Let's Encrypt)
- rotate access logs

❌ **Avoid**:
- Default AWS credentials in code
- Port 22 open to world
- Weak passwords
- Committing `.env` files
- Running as root

---

## Support & Debugging

**Issues?**
1. Check `systemctl status policy-helper-ai`
2. View logs: `journalctl -u policy-helper-ai -f`
3. Test Nginx: `sudo nginx -t`
4. Verify port 8000: `sudo netstat -tlpn | grep :8000`

**Common Issues**:
- **502 Bad Gateway**: Gunicorn socket not responding → restart service
- **Connection refused**: Security group rules or firewall
- **Out of memory**: Increase instance type (t2.small = $10/month)

---

## Next Steps

1. ✅ Deploy application
2. ✅ Set up SSL certificate
3. ✅ Configure domain name
4. ✅ Set up monitoring (CloudWatch)
5. ✅ Configure auto-scaling
6. ✅ Set up backup strategy for SQLite DB

---

**Questions?** Check AWS documentation or review logs with `sudo journalctl -u policy-helper-ai -f`
