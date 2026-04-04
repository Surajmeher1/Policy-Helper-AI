# AWS RDS Database Setup Guide

This guide explains how to set up AWS RDS (Relational Database Service) for Policy Helper AI for production deployments.

## Why RDS Over SQLite?

| Feature | SQLite | RDS MySQL | RDS PostgreSQL |
|---------|--------|-----------|-----------------|
| Performance | Good for users <100 | Excellent for users 1000+ | Excellent for users 1000+ |
| Scalability | Limited | Highly scalable | Highly scalable |
| Backup | Manual | Automatic (configurable) | Automatic (configurable) |
| Replication | No | Yes (Multi-AZ) | Yes (Multi-AZ) |
| Cost | $0 | $15-30/month | $15-30/month |
| Setup Complexity | None | Medium | Medium |
| Use Case | Development | Production | Production |

**Recommendation:** 
- **Development**: Use SQLite
- **Production (small)**: SQLite + Cloud backup
- **Production (large)**: RDS MySQL or PostgreSQL

---

## Step 1: Create RDS Instance in AWS Console

### 1.1 Navigate to RDS

1. Go to https://console.aws.amazon.com
2. Search for **"RDS"** → Click **"RDS Service"**
3. Left sidebar → Click **"Databases"**
4. Click **"Create database"**

### 1.2 Configure Database

**Database Creation Method:**
- Select **"Easy create"** (recommended for beginners)

**Engine Type:**
- Choose **"MySQL"** (most compatible) OR **"PostgreSQL"** (more advanced)
- Version: Latest (MySQL 8.0 or PostgreSQL 15+)

**DB Instance Identifier:**
```
policy-helper-ai-db
```

**Master Username:**
```
admin
```

**Master Password:**
- Generate strong password (minimum 8 characters)
- Save somewhere secure (AWS Secrets Manager recommended)

**DB Instance Class:**
- **Free Tier**: `db.t3.micro` (eligible for 12 months free)
- **Better Performance**: `db.t3.small` (~$25/month)

**Storage:**
- **Type**: `gp3` (General Purpose)
- **Allocated storage**: 20 GB (can auto-scale)
- **Enable storage autoscaling**: ✓ Yes

**Availability & Durability:**
- **Multi-AZ deployment**: 
  - Development: No (saves cost)
  - Production: Yes (high availability)

**Connectivity:**
- **VPC**: Default VPC
- **Public accessibility**: Yes (you'll configure security group)
- **VPC security group**: Create new → `policy-helper-ai-rds-sg`

**Database port:**
- MySQL: 3306
- PostgreSQL: 5432

**Database name:**
```
policy_helper_ai
```

**Backup:**
- **Backup retention period**: 7 days (recommended)
- **Backup window**: 03:00 UTC
- **Enable automated backups**: ✓ Yes

**Monitoring:**
- **Enable CloudWatch logs**: ✓ Yes
- **Log types**: Error, General, Slowquery

Click **"Create database"** and wait 5-15 minutes for creation.

### 1.3 Configure Security Group

After instance is created:

1. Go to **RDS Dashboard** → **Databases**
2. Click on your database instance
3. Scroll to **"Security group rules"**
4. Click the security group name
5. Add inbound rule:

```
Type:           MySQL/Aurora
Protocol:       TCP
Port:           3306 (MySQL) or 5432 (PostgreSQL)
Source:         Your EC2 instance security group
                (Select: policy-helper-sg)
```

Click **"Save"**

---

## Step 2: Connect to RDS from EC2

### 2.1 Install MySQL Client (on EC2)

```bash
# For MySQL
sudo apt install -y mysql-client

# For PostgreSQL
sudo apt install -y postgresql-client
```

### 2.2 Test Connection

**For MySQL:**
```bash
mysql -h your-rds-endpoint.rds.amazonaws.com \
      -u admin \
      -p policy_helper_ai

# Enter password when prompted

# If successful, you'll see: mysql>
# Exit with: exit
```

**For PostgreSQL:**
```bash
psql -h your-rds-endpoint.rds.amazonaws.com \
     -U admin \
     -d policy_helper_ai

# Enter password when prompted

# If successful, you'll see: policy_helper_ai=>
# Exit with: \q
```

---

## Step 3: Update Application Configuration

### 3.1 Update .env File

SSH into EC2 and edit `.env`:

```bash
nano /var/www/policy-helper-ai/.env
```

**For MySQL:**
```env
DB_TYPE=mysql
DB_HOST=your-rds-endpoint.rds.amazonaws.com
DB_PORT=3306
DB_USER=admin
DB_PASSWORD=your-secure-password
DB_NAME=policy_helper_ai
```

**For PostgreSQL:**
```env
DB_TYPE=postgresql
DB_HOST=your-rds-endpoint.rds.amazonaws.com
DB_PORT=5432
DB_USER=admin
DB_PASSWORD=your-secure-password
DB_NAME=policy_helper_ai
```

Save: **Ctrl+O**, **Enter**, **Ctrl+X**

### 3.2 Update requirements.txt 

```bash
cd /var/www/policy-helper-ai
```

Verify these packages are installed:

```bash
# For MySQL
pip install pymysql

# For PostgreSQL
pip install psycopg2-binary
```

Or ensure they're in requirements.txt:

```bash
grep -E "pymysql|psycopg2" requirements.txt
```

If not present, add them:

```bash
echo "pymysql" >> requirements.txt
echo "psycopg2-binary" >> requirements.txt
pip install -r requirements.txt
```

### 3.3 Initialize Database

```bash
cd /var/www/policy-helper-ai
source venv/bin/activate

# Set environment variables
export $(cat .env | xargs)

# Create database tables
flask db upgrade

# If first time, may need:
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 3.4 Restart Application

```bash
sudo systemctl restart policy-helper-ai
```

### 3.5 Verify Connection

```bash
# Check logs
tail -50 /var/log/policy-helper-ai/error.log

# If successful, no database errors should appear
# Test application: http://YOUR_IP/register
```

---

## Step 4: Backup & Restore Strategies

### 4.1 Automatic Backups (AWS)

AWS automatically creates backups based on settings:

1. **View backups**: RDS Dashboard → **Automated backups**
2. **Configure retention**: RDS Dashboard → Database → Modify → Backup retention period
3. **Point-in-time recovery**: Up to retention period

### 4.2 Manual Backup

Create manual snapshot:

```bash
# AWS CLI (on EC2 or local machine with AWS credentials)
aws rds create-db-snapshot \
    --db-instance-identifier policy-helper-ai-db \
    --db-snapshot-identifier policy-helper-ai-db-backup-$(date +%Y%m%d)
```

### 4.3 Export from RDS to S3

Backup entire database to S3:

```bash
# For MySQL, use mysqldump
mysqldump -h your-rds-endpoint.rds.amazonaws.com \
          -u admin -p policy_helper_ai > backup.sql

# Upload to S3
aws s3 cp backup.sql s3://your-bucket/policy-helper-ai-backups/
```

### 4.4 Restore from Backup

**From AWS Snapshot:**
1. RDS Dashboard → **Snapshots**
2. Select snapshot
3. Click **Actions** → **Restore from snapshot**
4. Configure new instance

**From SQL dump:**
```bash
mysql -h new-rds-endpoint.rds.amazonaws.com \
      -u admin -p policy_helper_ai < backup.sql
```

---

## Step 5: Monitoring & Performance

### 5.1 Enable Enhanced Monitoring

1. RDS Dashboard → **Databases**
2. Click instance → **Modify**
3. **Performance Insights**: Enable
4. **Enhanced monitoring**: Enable
5. **Monitoring interval**: 1 second
6. Click **Continue** → **Apply immediately**

### 5.2 CloudWatch Metrics

Available metrics:
- CPU Utilization
- Database Connections
- Disk Space Used
- Read/Write Operations
- Query Performance (Performance Insights)

Monitor from: AWS CloudWatch Dashboard

### 5.3 Check Query Performance

**MySQL:**
```bash
mysql -h your-rds-endpoint.rds.amazonaws.com -u admin -p policy_helper_ai

# View slow queries
SELECT * FROM mysql.slow_log LIMIT 10;

# View current process list
SHOW PROCESSLIST;
```

**PostgreSQL:**
```bash
psql -h your-rds-endpoint.rds.amazonaws.com -U admin policy_helper_ai

# View slow queries
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
SELECT query, calls, mean_time FROM pg_stat_statements 
ORDER BY mean_time DESC LIMIT 10;
```

---

## Step 6: Cost Optimization

### 6.1 Free Tier Eligibility

- **db.t3.micro**: FREE for 12 months (750 hours/month)
- **20 GB storage**: FREE (20 GB included)
- **Automated backups**: FREE (covered by free tier)
- **20 million I/O requests**: FREE

**Total cost after free tier**: ~$15-25/month for db.t3.micro

### 6.2 Cost-Saving Tips

1. **Use db.t3.micro for development**
   - Auto-scales with burstable performance
   - Cheapest option

2. **Enable auto-scaling**
   ```bash
   # AWS CLI
   aws rds create-db-instance-read-replica \
       --db-instance-identifier policy-helper-ai-replica \
       --source-db-instance-identifier policy-helper-ai-db
   ```

3. **Use reserved instances** (1-3 year discounts)
   - 30% discount for 1-year commitment
   - 50% discount for 3-year commitment

4. **Delete snapshots**
   - Snapshots cost: $0.095 per GB-month
   - Delete old snapshots regularly

5. **Monitor and stop if unused**
   ```bash
   aws rds stop-db-instance \
       --db-instance-identifier policy-helper-ai-db
   ```

---

## Troubleshooting

### Issue: Cannot connect to RDS

```bash
# Check security group
aws ec2 describe-security-groups --group-ids sg-xxxxx

# Test connection manually
mysql -h endpoint -u admin -p

# Check RDS status
aws rds describe-db-instances --db-instance-identifier policy-helper-ai-db
```

### Issue: Slow queries

1. Check Performance Insights: RDS Dashboard → Select DB → Performance Insights
2. Identify slow queries
3. Optimize application code or add database indexes

### Issue: Storage running out

1. RDS Dashboard → Select DB → **Modify**
2. Increase **Allocated storage**
3. Enable **Storage autoscaling**

### Issue: High CPU usage

1. Check what queries are running
2. Optimize application
3. Upgrade instance type
4. Add read replicas

---

## Production Checklist

- [ ] RDS instance created in correct region
- [ ] Automated backups enabled (7+ days retention)
- [ ] Security group configured (restrict to EC2 instance)
- [ ] Enhanced monitoring enabled
- [ ] Application .env file updated with RDS credentials
- [ ] Database tables created (flask db upgrade)
- [ ] Connection tested from EC2
- [ ] Application restarted
- [ ] CloudWatch alarms configured
- [ ] Backup strategy documented
- [ ] Disaster recovery plan in place

---

## Migration from SQLite to RDS

### Option 1: Using Flask-Migrate

```bash
# On EC2, in application directory
source venv/bin/activate
export $(cat .env | xargs)

# Create migration from current SQLite DB to RDS
flask db stamp head
flask db migrate -m "Migrate from SQLite to RDS"
flask db upgrade
```

### Option 2: Manual Migration

```bash
# Export from SQLite
sqlite3 instance/users.db << 'EOF'
.headers on
.mode csv
.output users_backup.csv
SELECT * FROM user;
SELECT * FROM activity;
.quit
EOF

# Import into RDS
mysql -h rds-endpoint -u admin -p policy_helper_ai < users_backup.sql
```

---

## AWS RDS Links & Resources

- **AWS RDS Documentation**: https://docs.aws.amazon.com/rds
- **RDS Pricing**: https://aws.amazon.com/rds/pricing
- **RDS Free Tier**: https://aws.amazon.com/free/database
- **RDS Performance Insights**: https://aws.amazon.com/rds/performance-insights
- **RDS Proxy** (connection pooling): https://aws.amazon.com/rds/proxy

---

**Last Updated:** April 2026
