# 🚀 Production Deployment Checklist

## Before You Deploy

### 1. Configuration ✓

- [ ] `.env` file has `ENV=production`
- [ ] `FRONTEND_URL` is set to your HTTPS domain
- [ ] `SECRET_KEY` is strong (64 characters)
- [ ] `ALLOWED_HOSTS` includes your domain
- [ ] Database credentials are secure
- [ ] AWS credentials are configured

### 2. Infrastructure ✓

- [ ] EC2 instance launched (t3.medium+)
- [ ] Security groups configured (ports 22, 80, 443)
- [ ] Domain DNS points to EC2
- [ ] RDS/PostgreSQL database created
- [ ] S3 bucket created and accessible
- [ ] IAM roles configured properly

### 3. Code ✓

- [ ] All tests passing locally
- [ ] Database migrations are ready
- [ ] No debugging code left in
- [ ] Error handling is production-ready
- [ ] Logging is configured

### 4. Dependencies ✓

- [ ] `requirements.txt` is up to date
- [ ] All external services are accessible
- [ ] API keys are valid
- [ ] Cognito user pool exists

## Deployment Steps

### 1. Run Pre-Deployment Check

```bash
python scripts/check_production.py
```

All checks should pass!

### 2. Deploy to Server

Choose your method:

- [ ] EC2 deployment script
- [ ] Manual deployment
- [ ] Docker deployment

### 3. Verify Deployment

```bash
# Health check
curl https://yourdomain.com/health

# Detailed check
curl https://yourdomain.com/health/detailed
```

### 4. Setup SSL

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 5. Configure Monitoring

- [ ] Setup CloudWatch (if using AWS)
- [ ] Configure Sentry (optional)
- [ ] Setup log rotation
- [ ] Configure backup schedule

## Post-Deployment

### 1. Smoke Test

```bash
# Run smoke test
TOKEN=your-auth-token \
BASE_URL=https://yourdomain.com \
python scripts/smoke_test_live.py
```

### 2. Monitor for 24 Hours

- [ ] Check error logs every 2 hours
- [ ] Monitor CPU/memory usage
- [ ] Watch response times
- [ ] Verify database performance

### 3. Create Backup

```bash
# Database backup
pg_dump $DATABASE_URL > backup.sql

# Application backup
tar czf codexa-backup-$(date +%Y%m%d).tar.gz /opt/codexa
```

## Rollback Plan

If issues occur:

```bash
# 1. Stop service
sudo systemctl stop codexa-backend

# 2. Restore previous version
cd /opt/codexa
git checkout <previous-commit>
source .venv/bin/activate
pip install -r requirements.txt

# 3. Restore database (if needed)
psql $DATABASE_URL < backup.sql

# 4. Restart
sudo systemctl start codexa-backend
```

## Emergency Contacts

- DevOps: [contact]
- Database Admin: [contact]
- AWS Support: [link]

## Sign-off

- [ ] Deployment tested and verified
- [ ] Documentation updated
- [ ] Team notified
- [ ] Monitoring configured

Deployed by: ******\_\_\_******
Date: ******\_\_\_******
Verified by: ******\_\_\_******
