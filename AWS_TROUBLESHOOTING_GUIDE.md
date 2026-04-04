# AWS Deployment - Troubleshooting & Verification Guide

## Pre-Deployment Checklist

### Environment Variable Preparation
- [ ] GROQ_API_KEY obtained from https://console.groq.com
- [ ] HF_TOKEN obtained from https://huggingface.co/settings/tokens
- [ ] HF_MODEL_NAME set to `facebook/bart-large-cnn`
- [ ] MAIL_SERVER configured (optional)
- [ ] MAIL_USERNAME and MAIL_PASSWORD obtained (optional)
- [ ] SECRET_KEY generated: `python3 -c "import secrets; print(secrets.token_hex(32))"`
- [ ] FLASK_ENV set to `production`

### AWS Account Setup
- [ ] AWS account created
- [ ] Free tier eligibility verified
- [ ] SSH key pair created and saved securely
- [ ] IAM user created with EC2 and RDS access (optional)
- [ ] Region selected (e.g., us-east-1 for lowest latency in US)

### Repository Preparation
- [ ] Repository is public OR personal access token created
- [ ] Latest code committed to main branch
- [ ] requirements.txt updated with all dependencies
- [ ] .env.example file created with placeholder values
- [ ] Dockerfile cleaned and tested locally

---

## Deployment Verification Steps

### Step 1: EC2 Instance Creation Verification

```bash
# SSH into instance
ssh -i policy-helper-ai-key.pem ubuntu@YOUR_INSTANCE_IP

# Should show: ubuntu@ip-xxx:~$

# If connection fails:
# 1. Check security group allows port 22 from your IP
# 2. Verify .pem file permissions: chmod 400 policy-helper-ai-key.pem
# 3. Verify instance is in "Running" state in AWS Console
```

### Step 2: System Dependencies Verification

```bash
# Run these commands on EC2:

# Check Python
python3 --version
# Should show: Python 3.x.x

# Check pip
pip3 --version
# Should show: pip x.x.x from /usr/lib/python3.x/dist-packages/pip

# Check virtual environment support
python3 -m venv --help
# Should show help text, no errors

# Check Nginx
nginx -v
# Should show: nginx/1.x.x

# Check Git
git --version
# Should show: git version 2.x.x

# Check system packages installed
dpkg -l | grep -E "python3|nginx|git" | wc -l
# Should show multiple installed packages
```

### Step 3: Application Files Verification

```bash
cd /var/www/policy-helper-ai

# Check repository cloned
ls -la
# Should show: app.py, requirements.txt, templates/, .git/, etc.

# Check virtual environment
ls -la venv/
# Should show: bin/, lib/, include/, pyvenv.cfg

# Check Python packages installed
source venv/bin/activate
pip list | head -20
# Should show: flask, torch, transformers, etc.
deactivate
```

### Step 4: Environment Variables Verification

```bash
cd /var/www/policy-helper-ai

# Check .env file exists
test -f .env && echo ".env file exists" || echo ".env file MISSING"

# Check .env file is readable only by owner
ls -la .env
# Should show: -rw------- (600 permissions)

# Check required variables are set
source .env
echo "GROQ_API_KEY length: ${#GROQ_API_KEY}"
echo "HF_TOKEN length: ${#HF_TOKEN}"
echo "SECRET_KEY length: ${#SECRET_KEY}"
# All should show > 0

# Check Flask environment
echo "FLASK_ENV: $FLASK_ENV"
# Should show: production
```

### Step 5: Database Verification

```bash
# Check SQLite database
ls -la /var/www/policy-helper-ai/instance/
# Should show: users.db (if not first run)

# Check database size
du -h /var/www/policy-helper-ai/instance/users.db
# Should show file size

# OR for RDS, test connection:
mysql -h your-rds-endpoint.rds.amazonaws.com \
      -u admin -p policy_helper_ai -e "SELECT VERSION();"
# Should show MySQL version without errors
```

### Step 6: Gunicorn Service Verification

```bash
# Check service file exists
sudo test -f /etc/systemd/system/policy-helper-ai.service && echo "Service file exists"

# Check service status
sudo systemctl status policy-helper-ai

# Expected output should include:
# - Active: active (running)
# - Main PID: XXXX
# - CGroup: process running

# Check service logs
sudo journalctl -u policy-helper-ai -n 20
# Should show service started successfully

# Check Gunicorn socket
ls -la /run/policy-helper-ai.sock
# Should show: srwxrwxr-x (socket file)

# Check Gunicorn process
ps aux | grep gunicorn
# Should show: 3 workers running
```

### Step 7: Nginx Verification

```bash
# Check Nginx configuration
sudo nginx -t
# Should show: nginx: configuration file test is successful

# Check Nginx service status
sudo systemctl status nginx
# Should show: Active: active (running)

# Check Nginx process
ps aux | grep nginx
# Should show: master process and worker processes

# Check Nginx is listening on port 80
sudo netstat -tlpn | grep :80
# Should show: LISTEN on 0.0.0.0:80

# Check Nginx configuration syntax
cat /etc/nginx/sites-available/policy-helper-ai
# Should show proxy pass configuration to socket
```

### Step 8: Network & Firewall Verification

```bash
# Check ports listening
sudo netstat -tlpn | grep -E ":80|:443"
# Should show:
# - 0.0.0.0:80 (HTTP)
# - 0.0.0.0:443 (HTTPS, if configured)

# Check security group rules (from your local machine)
curl -I http://YOUR_INSTANCE_IP
# Should return HTTP 200 (or 302 if redirect to HTTPS)

# Get instance public IP
ec2-metadata --public-ipv4
# Should show: xxx.xxx.xxx.xxx
```

### Step 9: Application Health Check

```bash
# Test application endpoint locally
curl -s http://localhost | head -20
# Should show HTML content, no error messages

# Check if redirects work
curl -L -I http://localhost/
# Should eventually show 200 OK

# Check API endpoints
curl -X GET http://localhost/api/health
# App may not have /health endpoint, but should be 404, not 500

# Check static files served
curl -I http://localhost/static/ 2>/dev/null | head -5
# Should show 403 (directory list disabled) or 200
```

### Step 10: Full Integration Test

```bash
# From your local machine, test full deployment:

# 1. Access landing page
curl -I http://YOUR_INSTANCE_IP
# Should return 200 OK

# 2. Test register endpoint
curl -X POST http://YOUR_INSTANCE_IP/register \
     -d "username=testuser&email=test@example.com&password=password123" 2>/dev/null | grep -q "register\|error" && echo "Register endpoint works"

# 3. Test chat endpoint
curl -X GET http://YOUR_INSTANCE_IP/chat
# Should return HTML or 404, not 500
```

---

## Common Issues & Solutions

### Issue 1: 502 Bad Gateway Error

**Cause:** Gunicorn not running or socket not accessible

**Solution:**
```bash
# Check service status
sudo systemctl status policy-helper-ai

# If not running, start it
sudo systemctl start policy-helper-ai

# Check logs
sudo journalctl -u policy-helper-ai -n 50

# Check socket exists
ls -la /run/policy-helper-ai.sock

# If socket doesn't exist, restart service
sudo systemctl restart policy-helper-ai

# Check Nginx can read socket
sudo ls -la /run/policy-helper-ai.sock

# Check permissions (should be readable by Nginx)
sudo chmod 666 /run/policy-helper-ai.sock
```

### Issue 2: 500 Internal Server Error

**Cause:** Application error, check logs

**Solution:**
```bash
# View application error log
tail -100 /var/log/policy-helper-ai/error.log

# Look for specific Python errors

# Common causes:
# - Missing API key: No GROQ_API_KEY found
# - Database error: database locked or not initialized
# - Module import error: Missing Python package

# If DATABASE error:
# 1. Check .env DATABASE variables
# 2. Run: flask db upgrade
# 3. Restart: sudo systemctl restart policy-helper-ai

# If API KEY error:
# 1. Edit .env with correct API keys
# 2. Restart: sudo systemctl restart policy-helper-ai

# If IMPORT error:
# 1. Check requirements.txt
# 2. Activate venv: source venv/bin/activate
# 3. Reinstall: pip install -r requirements.txt
# 4. Restart: sudo systemctl restart policy-helper-ai
```

### Issue 3: Timeout Errors

**Cause:** Requests taking too long, application processing slowly

**Solution:**
```bash
# Check system resources
free -h
# If RAM < 100MB available, increase instance size

df -h
# If disk < 1GB available, increase storage

# Check CPU usage
top -b -n 1 | head -15

# Increase Gunicorn timeout
sudo nano /etc/systemd/system/policy-helper-ai.service

# Change: --timeout 120
# To: --timeout 300 (or higher)

sudo systemctl daemon-reload
sudo systemctl restart policy-helper-ai

# Or increase Nginx proxy timeout
sudo nano /etc/nginx/sites-available/policy-helper-ai

# Add:
# proxy_read_timeout 300s;
# proxy_connect_timeout 300s;

sudo systemctl restart nginx
```

### Issue 4: API Key Errors

**Cause:** GROQ_API_KEY or HF_TOKEN not set or invalid

**Solution:**
```bash
# Check if variables are set
echo $GROQ_API_KEY
echo $HF_TOKEN

# If empty, edit .env
nano /var/www/policy-helper-ai/.env

# Ensure lines like:
# GROQ_API_KEY=your_actual_key_here
# HF_TOKEN=your_actual_token_here

# Verify keys are valid by testing API:
curl -H "Authorization: Bearer $GROQ_API_KEY" \
     https://api.groq.com/openai/v1/models

# Should return list of models, not 401 error

# Restart application
sudo systemctl restart policy-helper-ai
```

### Issue 5: Database Connection Errors

**If using SQLite:**
```bash
# Check database file exists and is readable
ls -la /var/www/policy-helper-ai/instance/users.db

# Check permissions
sudo chown ubuntu:ubuntu /var/www/policy-helper-ai/instance/users.db
sudo chmod 666 /var/www/policy-helper-ai/instance/users.db

# Recreate if corrupted
rm /var/www/policy-helper-ai/instance/users.db
cd /var/www/policy-helper-ai
source venv/bin/activate
flask db upgrade

# Restart
sudo systemctl restart policy-helper-ai
```

**If using RDS:**
```bash
# Test connection
mysql -h your-rds-endpoint.rds.amazonaws.com \
      -u admin -p policy_helper_ai

# Check security group allows connection
aws ec2 describe-security-groups --group-ids sg-xxxxx

# Check RDS instance status
aws rds describe-db-instances --db-instance-identifier policy-helper-ai-db | grep DBInstanceStatus

# Should show: available

# Verify .env has correct credentials
nano /var/www/policy-helper-ai/.env

# Check: DB_HOST, DB_USER, DB_PASSWORD are correct

# Restart
sudo systemctl restart policy-helper-ai
```

### Issue 6: SSL/HTTPS Certificate Issues

**If Certbot fails:**
```bash
# Check DNS is correctly pointed
nslookup your-domain.com
# Should show your EC2 instance IP

# Check ports 80 and 443 are open
sudo netstat -tlpn | grep -E ":80|:443"

# Verify DNS propagation
curl http://your-domain.com
# Should reach your server

# Try manual renewal
sudo certbot renew --dry-run

# If fails, try webroot method
sudo certbot certonly --webroot \
    -w /var/www/policy-helper-ai \
    -d your-domain.com

# Check certificate details
sudo certbot certificates
```

### Issue 7: High Memory Usage

**Cause:** Gunicorn workers using too much memory

**Solution:**
```bash
# Check current worker count
ps aux | grep gunicorn | wc -l

# Monitor memory
top -b -n 1 | grep gunicorn

# Reduce workers if needed
sudo nano /etc/systemd/system/policy-helper-ai.service

# Change: --workers 3
# To: --workers 2 (for t2.micro)

sudo systemctl daemon-reload
sudo systemctl restart policy-helper-ai

# Increase instance size if persistent
# Upgrade from t2.micro to t3.small in AWS Console
```

### Issue 8: Application Not Starting After Update

**Cause:** Code error or new dependency issue

**Solution:**
```bash
# Check recent changes
cd /var/www/policy-helper-ai
git log --oneline -5

# If error in recent commit, revert
git revert HEAD

# Or pull from clean state
git stash
git pull origin main

# Reinstall dependencies (might have changed)
source venv/bin/activate
pip install -r requirements.txt

# Test locally
flask run --host=0.0.0.0 --port=5000

# If works, restart service
sudo systemctl restart policy-helper-ai

# Check logs
sudo journalctl -u policy-helper-ai -n 50
```

---

## Monitoring & Health Check Script

Create `/home/ubuntu/health-check.sh`:

```bash
#!/bin/bash

echo "Policy Helper AI - Health Check"
echo "================================"

# Service status
echo ""
echo "1. Service Status:"
sudo systemctl status policy-helper-ai --no-pager | grep Active

echo ""
echo "2. Nginx Status:"
sudo systemctl status nginx --no-pager | grep Active

echo ""
echo "3. Memory Usage:"
free -h | grep Mem

echo ""
echo "4. Disk Usage:"
df -h / | tail -1

echo ""
echo "5. Application Response:"
curl -s http://localhost | grep -o "<title>.*</title>" || echo "Unable to retrieve page title"

echo ""
echo "6. Recent Errors:"
grep ERROR /var/log/policy-helper-ai/error.log | tail -5 || echo "No errors"

echo ""
echo "7. Socket Status:"
ls -la /run/policy-helper-ai.sock 2>/dev/null || echo "Socket not found"

echo ""
echo "================================"
```

Make executable and run:
```bash
chmod +x /home/ubuntu/health-check.sh
./health-check.sh

# Or run with cron for automated checks
crontab -e
# Add: 0 * * * * /home/ubuntu/health-check.sh >> /home/ubuntu/health-check.log 2>&1
```

---

## Emergency Recovery Commands

```bash
# Restart everything
sudo systemctl restart policy-helper-ai nginx

# Force stop all services
sudo systemctl stop policy-helper-ai nginx

# Clear Gunicorn socket (if stuck)
sudo rm /run/policy-helper-ai.sock

# Restart and check logs
sudo systemctl start policy-helper-ai
sudo journalctl -u policy-helper-ai -f

# Restore database from backup
cd /var/www/policy-helper-ai
cp instance/users.db.backup instance/users.db
sudo systemctl restart policy-helper-ai

# Reset application
rm -rf /var/www/policy-helper-ai/instance/users.db
cd /var/www/policy-helper-ai
source venv/bin/activate
flask db upgrade
```

---

## Support & Resources

- **Application Logs**: `/var/log/policy-helper-ai/error.log`
- **System Logs**: `sudo journalctl -u policy-helper-ai -f`
- **Nginx Logs**: `/var/log/nginx/error.log`
- **AWS Support**: https://console.aws.amazon.com/support
- **Free Tier Support**: Email support (no phone)

---

**Last Updated:** April 2026
**Status:** Production Ready
