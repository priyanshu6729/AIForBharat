# Quick Deployment Guide

## Option 1: Deploy to AWS EC2 (Recommended)

### Prerequisites

1. **Launch EC2 Instance**

   - Ubuntu 22.04 LTS
   - t3.medium or larger
   - 20GB+ storage
   - Security group: Allow ports 22, 80, 443, 8000

2. **Configure AWS**
   ```bash
   aws configure
   # Enter your credentials
   ```

### Deploy

```bash
# 1. Make scripts executable
chmod +x scripts/*.sh

# 2. Update .env.production with your domain and settings
nano .env.production

# 3. Deploy to EC2
EC2_HOST=your-ec2-ip.amazonaws.com \
EC2_USER=ubuntu \
EC2_KEY=~/.ssh/your-key.pem \
./scripts/deploy_to_ec2.sh

# 4. SSH into EC2 and complete setup
ssh -i ~/.ssh/your-key.pem ubuntu@your-ec2-ip.amazonaws.com

# On EC2:
cd /opt/codexa
sudo ./scripts/deploy_production.sh

# 5. Setup SSL
sudo certbot --nginx -d yourdomain.com
```

## Option 2: Manual Deployment

### On Your Server

```bash
# 1. Clone repository
git clone https://github.com/your-org/codexa.git
cd codexa/codexa-backend

# 2. Copy .env.production to .env
cp .env.production .env
nano .env  # Update with your values

# 3. Run deployment script
sudo APP_DIR=$(pwd) ./scripts/deploy_production.sh

# 4. Check service
sudo systemctl status codexa-backend
curl http://localhost:8000/health
```

## Option 3: Docker Deployment

```bash
# 1. Build Docker image
docker build -t codexa-backend .

# 2. Run container
docker run -d \
  --name codexa-backend \
  -p 8000:8000 \
  --env-file .env.production \
  codexa-backend

# 3. Check logs
docker logs -f codexa-backend
```

## Post-Deployment

### 1. Verify Deployment

```bash
# Health check
curl http://your-domain.com/health

# Detailed check
curl http://your-domain.com/health/detailed
```

### 2. Monitor Logs

```bash
# Application logs
sudo journalctl -u codexa-backend -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
```

### 3. Setup Monitoring (Optional)

```bash
# Install monitoring tools
sudo apt-get install -y prometheus-node-exporter

# Configure Sentry (if using)
# Update SENTRY_DSN in .env
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
sudo journalctl -u codexa-backend -n 100 --no-pager

# Check configuration
cd /opt/codexa
source .venv/bin/activate
python -c "from app.core.config import settings; print(settings.dict())"

# Test database
psql $DATABASE_URL -c "SELECT 1"
```

### 502 Bad Gateway

```bash
# Check if service is running
sudo systemctl status codexa-backend

# Check nginx configuration
sudo nginx -t

# Restart services
sudo systemctl restart codexa-backend nginx
```

### SSL Issues

```bash
# Renew certificate
sudo certbot renew --dry-run

# Check certificate
sudo certbot certificates
```

## Rollback

```bash
# Stop service
sudo systemctl stop codexa-backend

# Restore from backup
cd /opt/codexa
git checkout previous-commit-hash

# Restart
sudo systemctl start codexa-backend
```

## Support

- Documentation: `/docs/DEPLOYMENT.md`
- Issues: GitHub Issues
- Logs: `/var/log/codexa/`
