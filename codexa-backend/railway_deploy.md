# Railway Deployment Guide

## 🚂 Quick Deploy to Railway

### Prerequisites

1. Railway account: https://railway.app
2. GitHub repository with your code
3. PostgreSQL database URL
4. AWS credentials

### Method 1: Deploy from GitHub (Recommended)

1. **Push code to GitHub**

```bash
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

2. **Create Railway Project**

   - Go to https://railway.app
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Select `codexa-backend` directory if monorepo

3. **Add PostgreSQL Database**

   - In your project, click "New"
   - Select "Database" → "PostgreSQL"
   - Railway will create and connect it automatically

4. **Configure Environment Variables**

   Click on your service → Variables tab:

   ```env
   ENV=production
   LOG_LEVEL=INFO

   # Database (Railway provides this automatically as DATABASE_URL)
   # No need to set if using Railway PostgreSQL

   # Frontend
   FRONTEND_URL=https://your-frontend-domain.com

   # AWS
   AWS_ACCESS_KEY_ID=your-aws-access-key
   AWS_SECRET_ACCESS_KEY=your-aws-secret-key
   AWS_REGION=us-east-1
   S3_BUCKET=codexa-2026
   S3_PREFIX=prototype

   # Bedrock
   BEDROCK_REGION=us-east-1
   BEDROCK_MODEL_ID=amazon.nova-micro-v1:0
   NOVA_MODEL_ID=amazon.nova-micro-v1:0
   TITAN_EMBEDDING_MODEL_ID=amazon.titan-embed-text-v1

   # Lambda
   LAMBDA_FUNCTION_NAME=codexa-analysis
   LAMBDA_MODE=local

   # Cognito
   COGNITO_USER_POOL_ID=us-east-1_dNGB9UtRx
   COGNITO_CLIENT_ID=1fu0qbokifrchf0jsa5qf9e6c6
   COGNITO_REGION=us-east-1

   # Security
   SECRET_KEY=your-generated-secret-key-here
   ALLOWED_HOSTS=your-domain.com,*.railway.app

   # Rate Limiting
   RATE_LIMIT_PER_MINUTE=60
   RATE_LIMIT_PER_HOUR=1000
   ```

5. **Deploy**

   - Railway automatically deploys on push
   - Monitor deployment in the Deployments tab
   - Check logs for any errors

6. **Run Migrations** (if needed)

   In the service settings:

   - Settings → Deploy → Start Command:
     ```bash
     sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
     ```

### Method 2: Deploy with Railway CLI

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize project (in codexa-backend directory)
cd codexa-backend
railway init

# Link to your project
railway link

# Add PostgreSQL
railway add --database postgres

# Set environment variables
railway variables set ENV=production
railway variables set SECRET_KEY=$(openssl rand -hex 32)
railway variables set FRONTEND_URL=https://yourdomain.com
# ... set other variables

# Deploy
railway up

# View logs
railway logs
```

### Verify Deployment

```bash
# Get your Railway URL
railway domain

# Test health endpoint
curl https://your-service.railway.app/health

# Check detailed health
curl https://your-service.railway.app/health/detailed
```

## 🔧 Configuration

### Custom Domain

1. Go to Settings → Networking
2. Click "Generate Domain" for Railway subdomain
3. Or add custom domain:
   - Enter your domain
   - Add CNAME record: `your-domain.com` → `railway-assigned.railway.app`

### Environment Variables

Required variables:

- `ENV=production`
- `DATABASE_URL` (auto-set if using Railway PostgreSQL)
- `SECRET_KEY` (generate with `openssl rand -hex 32`)
- `COGNITO_USER_POOL_ID`
- `COGNITO_CLIENT_ID`
- AWS credentials

Optional variables:

- `SENTRY_DSN` for error tracking
- `LOG_LEVEL` (default: INFO)

### Start Command

Railway should auto-detect, but you can set manually:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Or with migrations:

```bash
sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
```

## 🐛 Troubleshooting

### Port Error

If you see `'$PORT' is not a valid integer`:

1. Update Dockerfile CMD:
   ```dockerfile
   CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
   ```
2. Or use Procfile (Railway auto-detects):
   ```
   web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

### Database Connection

```bash
# Check DATABASE_URL is set
railway variables

# Test connection
railway run python -c "from app.database import engine; engine.connect()"
```

### Build Failures

```bash
# View build logs
railway logs --deployment

# Common issues:
# 1. Missing dependencies → Check requirements.txt
# 2. Build timeout → Increase in Settings → Deploy
# 3. Memory issues → Upgrade plan or optimize dependencies
```

### Health Check Failures

1. Verify `/health` endpoint works locally
2. Check health check path in railway.json
3. Increase timeout in Settings → Deploy

### Migration Errors

```bash
# Run migrations manually
railway run alembic upgrade head

# Or add to start command
railway settings --start-command "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port \$PORT"
```

## 📊 Monitoring

### View Logs

```bash
# Live logs
railway logs

# Deployment-specific logs
railway logs --deployment <deployment-id>
```

### Metrics

- View in Railway dashboard → Metrics
- CPU, Memory, Network usage
- Request/response times

### Alerts

Set up in Settings → Notifications:

- Deployment failures
- Health check failures
- Resource limits

## 💰 Cost Optimization

1. **Hobby Plan**: $5/month

   - 500 hours/month
   - $0.000463/GB-hour RAM
   - Good for development

2. **Production**:
   - Use sleep on inactivity
   - Optimize Docker image size
   - Use connection pooling for database

## 🔄 CI/CD

Railway auto-deploys on push to main branch.

### Disable Auto-Deploy

Settings → Deploy → Auto Deploy: OFF

### Manual Deploy

```bash
railway up
```

## 🚀 Next Steps

1. ✅ Set up custom domain
2. ✅ Configure environment variables
3. ✅ Run database migrations
4. ✅ Test all endpoints
5. ✅ Monitor logs for errors
6. ✅ Set up error tracking (Sentry)
7. ✅ Configure backup schedule

## 📚 Resources

- [Railway Docs](https://docs.railway.app)
- [Railway CLI](https://docs.railway.app/develop/cli)
- [Railway Templates](https://railway.app/templates)
