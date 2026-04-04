# AWS Deployment - Quick Start Reference Guide

**Complete Deployment Time:** 30-45 minutes  
**Cost:** Free for first 12 months (AWS Free Tier)  
**Status:** Production Ready ✅

---

## 🚀 Quick Start (5 Minutes)

### If you're starting fresh:

```bash
# 1. Create AWS account
# Go to: https://aws.amazon.com → Create Account

# 2. Create SSH Key Pair
# AWS Console → EC2 → Key Pairs → Create → Download .pem file

# 3. Launch EC2 Instance
# AWS Console → EC2 → Launch Instance
# OS: Ubuntu 24.04 LTS
# Type: t2.micro (free) or t3.medium (recommended)
# Storage: 20GB
# Security Group: Allow port 22 (SSH), 80 (HTTP), 443 (HTTPS)

# 4. Connect via SSH (replace IP)
ssh -i policy-helper-ai-key.pem ubuntu@YOUR_INSTANCE_IP

# 5. Deploy Application (one command)
curl -fsSL https://raw.githubusercontent.com/Surajmeher1/Policy-Helper-AI/main/deploy-aws.sh | sudo bash
```

---

## 📋 Step-by-Step Quick Reference

### Phase 1: AWS Account Setup (5 minutes)

| Step | Action | Link |
|------|--------|------|
| 1.1 | Create AWS Account | https://aws.amazon.com/free |
| 1.2 | Verify email | Check inbox |
| 1.3 | Create SSH key pair | AWS Console → EC2 → Key Pairs |
| 1.4 | Download .pem file | Save securely (don't share) |

### Phase 2: EC2 Instance Launch (10 minutes)

```bash
# Configuration Summary:
Field                  | Value
-----------------------|--------------------
Name                   | policy-helper-ai
OS                     | Ubuntu Server 24.04 LTS
Instance Type          | t2.micro or t3.medium
Key Pair              | policy-helper-ai-key
Network               | Default VPC
Auto-assign Public IP | Yes
Security Group        | policy-helper-sg
Storage               | 20GB gp3

# Security Group Rules:
Type    | Protocol | Port | Source
--------|----------|------|----------
SSH     | TCP      | 22   | YOUR_IP_ONLY
HTTP    | TCP      | 80   | 0.0.0.0/0
HTTPS   | TCP      | 443  | 0.0.0.0/0
```

### Phase 3: SSH Connection (2 minutes)

**Windows PowerShell:**
```powershell
# Change key permissions
icacls policy-helper-ai-key.pem /inheritance:r /grant:r "%username%:F"

# Connect
ssh -i policy-helper-ai-key.pem ubuntu@YOUR_INSTANCE_IP
```

**Linux/Mac:**
```bash
chmod 400 policy-helper-ai-key.pem
ssh -i policy-helper-ai-key.pem ubuntu@YOUR_INSTANCE_IP
```

### Phase 4: Automated Deployment (15 minutes)

**Option A: One-Command Deploy (Recommended)**
```bash
sudo bash -c 'curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/Policy-Helper-AI/main/deploy-aws.sh | bash'
```

If you already have a partial install on the server, clean it first:
```bash
sudo rm -rf /var/www/policy-helper-ai
```

**Option B: Manual Deploy**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv git nginx certbot python3-certbot-nginx

# Clone repository
sudo mkdir -p /var/www/policy-helper-ai
cd /var/www/policy-helper-ai
sudo git clone https://github.com/YOUR_USERNAME/Policy-Helper-AI.git .
sudo chown ubuntu:ubuntu -R .

# Setup Python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure application
cp .env.example .env
nano .env  # Add your API keys here

# Initialize database
mkdir -p instance
flask db upgrade

# Create service
sudo nano /etc/systemd/system/policy-helper-ai.service
# Paste content from deploy-aws.sh (lines 120-145)

# Start services
sudo systemctl daemon-reload
sudo systemctl enable policy-helper-ai nginx
sudo systemctl start policy-helper-ai nginx
```

### Phase 5: Configuration (5 minutes)

```bash
# Edit .env with your API keys
nano /var/www/policy-helper-ai/.env
```

**Required Variables:**
```env
GROQ_API_KEY=your_key_from_console.groq.com
HF_TOKEN=your_token_from_huggingface.co
SECRET_KEY=your_generated_secret_key
FLASK_ENV=production
```

**Optional Variables:**
```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# For RDS Database:
DB_TYPE=mysql
DB_HOST=your-rds-endpoint.amazonaws.com
DB_USER=admin
DB_PASSWORD=secure_password
DB_NAME=policy_helper_ai
```

### Phase 6: Verification (3 minutes)

```bash
# Check services are running
sudo systemctl status policy-helper-ai nginx

# View application
# Visit: http://YOUR_INSTANCE_IP in browser
# Should see: Policy Helper AI landing page

# Check logs
tail -20 /var/log/policy-helper-ai/error.log
```

---

## 🔑 Essential Commands

### Service Management
```bash
# Service status
sudo systemctl status policy-helper-ai

# Restart after changes
sudo systemctl restart policy-helper-ai

# View logs
tail -100 /var/log/policy-helper-ai/error.log

# Start service
sudo systemctl start policy-helper-ai

# Stop service
sudo systemctl stop policy-helper-ai

# Enable auto-start on reboot
sudo systemctl enable policy-helper-ai
```

### Application Updates
```bash
# Update code
cd /var/www/policy-helper-ai
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Migrate database
flask db upgrade

# Restart
sudo systemctl restart policy-helper-ai
```

### Database Operations
```bash
# SQLite: Check database
sqlite3 /var/www/policy-helper-ai/instance/users.db ".tables"

# SQLite: Backup
cp /var/www/policy-helper-ai/instance/users.db /var/www/policy-helper-ai/instance/users.db.backup

# RDS: Test connection
mysql -h your-endpoint.rds.amazonaws.com -u admin -p policy_helper_ai -e "SELECT VERSION();"
```

### System Monitoring
```bash
# Check resources
free -h          # RAM
df -h            # Disk
top -b -n 1      # Processes

# Check listening ports
sudo netstat -tlpn | grep -E ":80|:443"

# Check running processes
ps aux | grep gunicorn | wc -l

# Check for recent errors
grep ERROR /var/log/policy-helper-ai/error.log | tail -10
```

---

## 🛠️ Common Tasks

### Add Custom Domain
```bash
# 1. Point domain DNS to your instance's Elastic IP or public IP
# 2. Install SSL certificate
sudo certbot --nginx -d your-domain.com

# 3. Verify redirect
curl -I https://your-domain.com
```

### Increase Server Size (Vertical Scaling)
```bash
# AWS Console → EC2 → Instances → Instance Settings → Instance Type
# Note: Requires instance stop/restart (downtime ~2-3 minutes)

# Update after resize
sudo apt update && sudo apt upgrade -y

# Increase Gunicorn workers if needed
sudo nano /etc/systemd/system/policy-helper-ai.service
# Change --workers from 3 to 5 or 7
sudo systemctl daemon-reload
sudo systemctl restart policy-helper-ai
```

### Enable RDS Database (Upgrade from SQLite)
```bash
# 1. Create RDS instance
#    AWS Console → RDS → Create Database
#    See AWS_RDS_SETUP_GUIDE.md for details

# 2. Update .env
nano /var/www/policy-helper-ai/.env
# Add:
# DB_TYPE=mysql
# DB_HOST=your-endpoint.rds.amazonaws.com
# DB_USER=admin
# DB_PASSWORD=secure-password
# DB_NAME=policy_helper_ai

# 3. Migrate database
cd /var/www/policy-helper-ai
source venv/bin/activate
flask db upgrade

# 4. Restart
sudo systemctl restart policy-helper-ai
```

### Set Up Automated Backups
```bash
# Create backup script
sudo nano /usr/local/bin/backup-db.sh

#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
cp /var/www/policy-helper-ai/instance/users.db \
   /backups/users.db.$DATE
find /backups -name "users.db.*" -mtime +7 -delete

chmod +x /usr/local/bin/backup-db.sh

# Schedule daily backup at 2 AM
(crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/backup-db.sh") | crontab -
```

### Enable HTTPS/SSL
```bash
# Prerequisites: Domain and ports 80, 443 open

# Install certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal (automatic via cronfor let's Encrypt)
sudo systemctl enable certbot.timer

# Check certificate details
sudo certbot certificates
```

---

## 💰 Cost Breakdown

### Year 1 (Free Tier Eligible)
- **EC2**: $0 (750 hours free)
- **Storage**: $0 (30GB free)
- **Database**: $0 (SQLite file-based)
- **Total**: **$0** ✅

### Year 2+ (If using t2.micro + SQLite)
- **EC2 t2.micro**: ~$9-11/month
- **EBS Storage**: ~$2-3/month
- **Bandwidth**: ~$0.5-1/month
- **Total**: ~**$12-15/month** 💰

### Year 2+ (If upgrading to production)
- **EC2 t3.medium**: ~$35-40/month
- **RDS MySQL**: ~$15-20/month
- **Storage**: ~$5-10/month
- **Backups**: ~$2-5/month
- **Total**: ~**$60-75/month** 💰

---

## ⚠️ Important Notes

### Security
- [ ] **Never commit .env to GitHub** - Use .env.example instead
- [ ] **SSH key is password** - Don't share or commit to version control
- [ ] **Restrict SSH to your IP** - Change security group rule from 0.0.0.0/0
- [ ] **Use strong passwords** - Especially for RDS and admin accounts
- [ ] **Enable automatic backups** - For disaster recovery

### Maintenance
- [ ] **Monitor logs regularly** - Check error.log for issues
- [ ] **Update packages monthly** - `sudo apt upgrade -y`
- [ ] **Backup database daily** - SQLite: `cp instance/users.db`, RDS: automatic
- [ ] **Review costs weekly** - AWS Console → Billing Dashboard
- [ ] **Test disaster recovery** - Monthly restoration from backup

### Production Checklist
- [ ] SSL certificate installed and auto-renewing
- [ ] All API keys entered in .env
- [ ] Database backups working
- [ ] CloudWatch monitoring enabled
- [ ] Security group properly configured
- [ ] SSH key backed up securely
- [ ] DNS/domain configured (if applicable)

---

## 📚 Documentation Index

| Document | Purpose | Read Time |
|----------|---------|-----------|
| **AWS_DEPLOYMENT_COMPLETE_GUIDE.md** | Full A-Z deployment guide | 45 min |
| **AWS_RDS_SETUP_GUIDE.md** | Production database setup | 30 min |
| **AWS_TROUBLESHOOTING_GUIDE.md** | Debugging and verification | 30 min |
| **AWS_DEPLOYMENT_SUMMARY.md** | Implementation overview | 15 min |
| **AWS_DEPLOYMENT_QUICK_START.md** | This file - quick reference | 5 min |

---

## 🆘 Quick Troubleshooting

### Application not accessible (http://IP shows 502/503)
```bash
# Check service is running
sudo systemctl status policy-helper-ai

# If not running, restart
sudo systemctl restart policy-helper-ai

# Check logs for errors
tail -50 /var/log/policy-helper-ai/error.log

# If database error: Run flask db upgrade
cd /var/www/policy-helper-ai
source venv/bin/activate
flask db upgrade
sudo systemctl restart policy-helper-ai
```

### API key errors (chat/model features not working)
```bash
# Check .env has keys
echo $GROQ_API_KEY
echo $HF_TOKEN

# If empty, edit .env
nano /var/www/policy-helper-ai/.env

# Add actual keys from:
# GROQ_API_KEY: https://console.groq.com
# HF_TOKEN: https://huggingface.co/settings/tokens

# Restart application
sudo systemctl restart policy-helper-ai
```

### Out of memory / Server slow
```bash
# Check resource usage
free -h
df -h

# Check process memory
ps aux | grep gunicorn | head -5

# If using too much memory:
# 1. Reduce Gunicorn workers: --workers 2 (instead of 3)
# 2. Upgrade instance on AWS Console
# 3. Use smaller ML models
```

### Can't clone repository
```bash
# If private repository, use personal access token:
git clone https://YOUR_TOKEN@github.com/YOUR_USERNAME/Policy-Helper-AI.git

# Or use SSH (requires SSH key setup first)
git clone git@github.com:YOUR_USERNAME/Policy-Helper-AI.git
```

---

## ✅ Success Indicators

Your deployment is successful when:

1. ✅ SSH connection works: `ssh -i key.pem ubuntu@IP`
2. ✅ Application accessible: `http://YOUR_IP` shows landing page
3. ✅ Register works: Can create new account
4. ✅ Chat works: API responses appear in console (if keys set)
5. ✅ No errors: `tail /var/log/policy-helper-ai/error.log` shows nothing
6. ✅ Services running: `sudo systemctl status policy-helper-ai nginx` shows "active"
7. ✅ Database works: Can register users without SQL errors

---

## 📞 Getting Help

### Check Logs First
```bash
# Application errors
tail -100 /var/log/policy-helper-ai/error.log

# System errors
sudo journalctl -u policy-helper-ai -n 50

# Nginx errors
sudo tail -20 /var/log/nginx/error.log
```

### Review Documentation
- **Deployment Guide**: AWS_DEPLOYMENT_COMPLETE_GUIDE.md
- **Troubleshooting**: AWS_TROUBLESHOOTING_GUIDE.md
- **DB Setup**: AWS_RDS_SETUP_GUIDE.md

### AWS Support
- **Free Tier Support**: Email support, no phone
- **Billing Issues**: AWS Billing Support
- **Technical Issues**: AWS Support (premium)

---

## ⏱️ Estimated Timeline

| Phase | Duration | Task |
|-------|----------|------|
| Account Setup | 5 min | Create AWS account, SSH key |
| EC2 Launch | 10 min | Launch instance, wait for startup |
| SSH Connect | 2 min | Connect to instance |
| Deploy | 15 min | Run deployment script |
| Config | 5 min | Set .env variables |
| Test | 3 min | Verify application loads |
| **Total** | **40 min** | Ready to use! |

Add 15-30 minutes if setting up custom domain/SSL.

---

## 🎯 Next Steps After Deployment

1. **Document your IP/domain** - Save it somewhere safe
2. **Test all features** - Register, login, use chat
3. **Set up backups** - Daily SQLite or enable RDS
4. **Monitor logs** - Check daily for errors
5. **Plan upgrades** - SQLite → RDS when needed
6. **Update DNS** (optional) - Point domain to your instance
7. **Enable SSL** (recommended) - Use Certbot

---

**Status**: Production Ready 🚀  
**Last Updated**: April 2026  
**Questions**: See documentation files or AWS support

Good luck with your deployment! 🎉
