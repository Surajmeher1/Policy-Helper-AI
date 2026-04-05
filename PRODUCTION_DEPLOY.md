# Production Deployment Guide - Policy Helper AI

## Quick Start (Copy-Paste)

### 1. SSH into EC2 Instance
```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
sudo -i  # Switch to root
```

### 2. Clone and Deploy
```bash
cd /tmp
git clone https://github.com/Surajmeher1/Policy-Helper-AI.git
cd Policy-Helper-AI

# Copy deployment files to EC2
scp -i your-key.pem policy-helper-ai.service ubuntu@your-ec2-ip:/tmp/
scp -i your-key.pem policy-helper-ai.nginx ubuntu@your-ec2-ip:/tmp/
scp -i your-key.pem deploy.sh ubuntu@your-ec2-ip:/tmp/

# SSHed into instance:
sudo bash /tmp/deploy.sh
```

### 3. Configure Environment Variables
```bash
sudo nano /var/www/policy-helper-ai/.env
```

Add your actual values:
```
FLASK_ENV=production
SECRET_KEY=generate-a-random-string-here
GROQ_API_KEY=your-actual-groq-key
HF_TOKEN=your-actual-huggingface-token
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

### 4. Start Services
```bash
sudo systemctl start policy-helper-ai
sudo systemctl start nginx
```

---

## Service Management

### Start/Stop/Restart
```bash
sudo systemctl start policy-helper-ai
sudo systemctl stop policy-helper-ai
sudo systemctl restart policy-helper-ai
sudo systemctl status policy-helper-ai
```

### Enable on Boot
```bash
sudo systemctl enable policy-helper-ai
sudo systemctl enable nginx
```

---

## Logs & Debugging

### Gunicorn Logs
```bash
# Real-time logs
sudo journalctl -u policy-helper-ai -f

# Last 100 lines
sudo tail -100 /var/log/gunicorn/error.log
sudo tail -100 /var/log/gunicorn/access.log
```

### Nginx Logs
```bash
sudo tail -100 /var/log/nginx/policy-helper-ai-error.log
sudo tail -100 /var/log/nginx/policy-helper-ai-access.log
```

### Check if Services Running
```bash
ps aux | grep gunicorn
ps aux | grep nginx
```

### Test Nginx Config
```bash
sudo nginx -t
```

---

## Common Issues & Fixes

### App Won't Start
```bash
# Check logs
sudo journalctl -u policy-helper-ai -f

# Common causes:
# 1. Missing .env file - see "Configure Environment Variables" above
# 2. Missing dependencies - run: pip install -r requirements.txt
# 3. Permission issues - run: sudo chown -R www-data:www-data /var/www/policy-helper-ai
```

### Out of Memory
```bash
# Check swap
free -h

# Monitor memory
watch -n 1 free -h

# Check gunicorn processes
ps aux | grep gunicorn
```

### Port 80 Already in Use
```bash
sudo lsof -i :80
sudo kill -9 <PID>
```

### Nginx 502 Bad Gateway
```bash
# Check if gunicorn is running
sudo systemctl status policy-helper-ai

# Restart both
sudo systemctl restart policy-helper-ai
sudo systemctl restart nginx

# Check logs
sudo tail -50 /var/log/nginx/policy-helper-ai-error.log
```

---

## Performance Tuning

### Monitor System
```bash
# Real-time monitoring
top
htop  # Install: sudo apt-get install htop

# Check load
uptime
```

### Gunicorn Settings (in policy-helper-ai.service)
- `--workers=2` - Number of worker processes (set to CPU cores for CPU-bound work)
- `--threads=4` - Threads per worker (good for I/O-bound NLP tasks)
- `--worker-class=gthread` - Thread-based workers (memory efficient)
- `--timeout=120` - Timeout for requests (NLP can be slow)

### For Heavy NLP Processing
Increase timeout in service file if processing takes >120s:
```bash
sudo nano /etc/systemd/system/policy-helper-ai.service
# Change: --timeout=120 to --timeout=300
sudo systemctl daemon-reload
sudo systemctl restart policy-helper-ai
```

---

## Update Code

### Pull Latest Changes
```bash
cd /var/www/policy-helper-ai
sudo -u www-data git pull origin main
sudo systemctl restart policy-helper-ai
```

### Update Dependencies
```bash
cd /var/www/policy-helper-ai
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart policy-helper-ai
```

---

## System Health Check

```bash
#!/bin/bash
echo "=== System Health Check ==="
echo ""
echo "1. Services Status:"
sudo systemctl status policy-helper-ai --no-pager
sudo systemctl status nginx --no-pager

echo ""
echo "2. Memory Usage:"
free -h

echo ""
echo "3. Disk Usage:"
df -h

echo ""
echo "4. Swap Status:"
swapon --show

echo ""
echo "5. Network Check:"
sudo netstat -tlnp | grep -E ':(80|443|5000)'

echo ""
echo "6. Recent Errors:"
sudo tail -20 /var/log/gunicorn/error.log
```

---

## Security Checklist

- [ ] Set strong SECRET_KEY in .env
- [ ] Keep API keys secure (never commit to git)
- [ ] Enable UFW firewall
- [ ] Use HTTPS in production (add SSL certificate)
- [ ] Regular security updates: `sudo apt-get update && sudo apt-get upgrade`
- [ ] Monitor logs regularly
- [ ] Backup your database regularly

---

## SSL/HTTPS Setup (Optional but Recommended)

### Using Let's Encrypt with Certbot
```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

Update nginx config in `/etc/nginx/sites-available/policy-helper-ai` to redirect HTTP to HTTPS.

---

## Useful Commands

```bash
# Check app is responding
curl http://localhost/health

# Check specific port
sudo lsof -i :80
sudo lsof -i :5000

# Restart everything
sudo systemctl restart policy-helper-ai && sudo systemctl restart nginx

# Full logs with timestamps
sudo journalctl -u policy-helper-ai -n 50 --no-pager

# Monitor in real-time
watch -n 5 'sudo systemctl status policy-helper-ai'
```

---

## Rollback if Issues

```bash
# Revert code
cd /var/www/policy-helper-ai
git log --oneline  # Find commit hash
git checkout <commit-hash>

# Restart service
sudo systemctl restart policy-helper-ai
```

---

## Support & Debugging

For detailed debugging:
```bash
# Full system info
uname -a
python3 --version
nginx -v

# Test WSGI app
cd /var/www/policy-helper-ai
source venv/bin/activate
python3 -c "from app import app; print('App imports OK')"

# Run gunicorn manually (for testing)
cd /var/www/policy-helper-ai
source venv/bin/activate
gunicorn --bind 127.0.0.1:5000 --workers=2 --threads=4 --timeout=120 app:app
```

---

Done! Your Flask NLP+AI app is in production.
