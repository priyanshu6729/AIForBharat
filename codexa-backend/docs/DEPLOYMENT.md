# Codexa Backend Deployment Guide

## Prerequisites

- Ubuntu 20.04+ or Amazon Linux 2
- Python 3.11+
- PostgreSQL 15+
- AWS Account with configured credentials
- Domain name (for production)

## Quick Start

### 1. Pre-Deployment Check

```bash
python scripts/check_production.py
```

Fix any issues reported before proceeding.

### 2. Generate Secrets

```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Update .env with the generated key
```

### 3. Update Configuration

Edit `.env` file:

- Set `ENV=production`
- Update `FRONTEND_URL` with your domain
- Update `ALLOWED_HOSTS` with your domain
- Set `SECRET_KEY` to generated value
- Verify `LAMBDA_MODE` (use `local` if Lambda not deployed)

### 4. Deploy

```bash
# Make script executable
chmod +x scripts/deploy_production.sh

# Deploy (run with sudo or as root)
sudo APP_DIR=/opt/codexa scripts/deploy_production.sh
```

### 5. Setup SSL

```bash
# Install certbot if not already installed
sudo apt-get install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

## Lambda Function Modes

### Local Mode (Development/Initial Production)

When Lambda function is not yet deployed:

```env
LAMBDA_MODE=local
```

The application will process AST analysis locally.

### Invoke Mode (Full Production)

After deploying Lambda function:

```env
LAMBDA_MODE=invoke
LAMBDA_FUNCTION_NAME=codexa-analysis
```

## Monitoring

### View Logs

```bash
# Application logs
sudo journalctl -u codexa-backend -f

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### Health Checks

```bash
# Basic health
curl http://localhost:8000/health

# Detailed health (includes DB, S3, Bedrock checks)
curl http://localhost:8000/health/detailed

# Kubernetes-style probes
curl http://localhost:8000/health/ready
curl http://localhost:8000/health/live
```

### Service Management

```bash
# Check status
sudo systemctl status codexa-backend

# Restart service
sudo systemctl restart codexa-backend

# Stop service
sudo systemctl stop codexa-backend

# View service logs
sudo journalctl -u codexa-backend -n 100
```

## Troubleshooting

### Application Won't Start

1. Check configuration:

```bash
cd /opt/codexa
source .venv/bin/activate
python -c "from app.core.config import settings; print(settings.env)"
```

2. Check database connection:

```bash
psql $DATABASE_URL -c "SELECT 1"
```

3. Check logs:

```bash
sudo journalctl -u codexa-backend -n 50 --no-pager
```

### Database Issues

```bash
# Run migrations
cd /opt/codexa
source .venv/bin/activate
alembic upgrade head
```

### AWS Permission Issues

Ensure IAM user/role has:

- S3: `s3:GetObject`, `s3:PutObject`, `s3:ListBucket`
- Lambda: `lambda:InvokeFunction`, `lambda:GetFunction`
- Bedrock: `bedrock:InvokeModel`
- SQS: `sqs:SendMessage`, `sqs:ReceiveMessage`

### SSL Certificate Issues

```bash
# Renew manually
sudo certbot renew

# Check certificate status
sudo certbot certificates
```

## Performance Tuning

### Gunicorn Workers

Edit `/etc/systemd/system/codexa-backend.service`:

```ini
# For 4 CPU cores, use 9 workers (2 * cores + 1)
ExecStart=/opt/codexa/.venv/bin/gunicorn app.main:app \
    --workers 9 \
    --worker-class uvicorn.workers.UvicornWorker
```

### Database Connection Pooling

In `.env`:

```env
DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/db?pool_size=20&max_overflow=10
```

## Security Checklist

- [ ] SECRET_KEY changed from default
- [ ] FRONTEND_URL uses HTTPS
- [ ] ALLOWED_HOSTS restricted to actual domains
- [ ] Database uses strong password
- [ ] AWS credentials use IAM roles (not access keys)
- [ ] SSL certificate installed and auto-renewing
- [ ] Rate limiting enabled
- [ ] API docs disabled in production (`/docs` returns 404)
- [ ] Firewall configured (only ports 80, 443, 22 open)
- [ ] Database not exposed to internet

## Backup Strategy

### Database Backups

```bash
# Daily backup script
#!/bin/bash
BACKUP_DIR="/var/backups/codexa"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

pg_dump $DATABASE_URL | gzip > $BACKUP_DIR/codexa_$DATE.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "codexa_*.sql.gz" -mtime +7 -delete
```

Add to crontab:

```bash
0 2 * * * /usr/local/bin/backup_codexa.sh
```

### S3 Versioning

Enable versioning on S3 bucket for automatic file backups.

## Scaling

### Horizontal Scaling

1. Use load balancer (ALB/nginx)
2. Multiple application servers
3. Shared PostgreSQL database (RDS)
4. Redis for session storage (optional)

### Vertical Scaling

- Increase EC2 instance size
- Add more Gunicorn workers
- Increase database connection pool

## Support

For issues, check:

1. Application logs
2. System logs (`dmesg`, `journalctl`)
3. AWS CloudWatch (if configured)
4. GitHub issues
