# 🚂 Railway Deployment Guide for Codexa Backend

## Prerequisites

- Railway account (https://railway.app)
- GitHub repository connected to Railway
- AWS credentials (for S3, Bedrock, Cognito)

## Step 1: Create Railway Project

1. Go to Railway dashboard
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your `codexa` repository
5. Railway will auto-detect the configuration from `railway.toml`

## Step 2: Add PostgreSQL Database

1. In your Railway project, click "New"
2. Select "Database" → "PostgreSQL"
3. Railway will automatically create a database and set `DATABASE_URL`
4. The `DATABASE_URL` is automatically injected into your backend service

## Step 3: Configure Environment Variables

Go to your backend service → Variables tab and add:

### Required Variables

```bash
ENV=production
FRONTEND_URL=https://your-frontend.railway.app
SECRET_KEY=<generate-with-openssl-rand-hex-32>
ALLOWED_HOSTS=your-backend.railway.app
```

### AWS Variables

```bash
AWS_ACCESS_KEY_ID=<your-aws-key>
AWS_SECRET_ACCESS_KEY=<your-aws-secret>
S3_BUCKET=codexa-2026
AWS_REGION=us-east-1
```

### Service Variables

```bash
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/657372247607/codexa-prototype
BEDROCK_MODEL_ID=amazon.nova-micro-v1:0
NOVA_MODEL_ID=amazon.nova-micro-v1:0
TITAN_EMBEDDING_MODEL_ID=amazon.titan-embed-text-v1
COGNITO_USER_POOL_ID=us-east-1_dNGB9UtRx
COGNITO_CLIENT_ID=1fu0qbokifrchf0jsa5qf9e6c6
COGNITO_REGION=us-east-1
LAMBDA_FUNCTION_NAME=codexa-analysis
LAMBDA_MODE=remote
```

### Optional Variables

```bash
RUN_MIGRATIONS=true  # Set to run DB migrations on startup
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=2000
LOG_LEVEL=INFO
SENTRY_DSN=<optional-sentry-dsn>
```

## Step 4: Generate SECRET_KEY

Run locally:

```bash
openssl rand -hex 32
```

Copy the output and set it as `SECRET_KEY` in Railway.

## Step 5: Deploy

1. Railway will automatically deploy on git push
2. Check deployment logs in Railway dashboard
3. Wait for deployment to complete

## Step 6: Verify Deployment

### Check Health Endpoint

```bash
curl https://your-backend.railway.app/health
```

Expected response:

```json
{
  "status": "healthy",
  "environment": "production",
  "database": "connected"
}
```

### Check Detailed Health

```bash
curl https://your-backend.railway.app/health/detailed
```

## Step 7: Run Database Migrations

If you haven't set `RUN_MIGRATIONS=true`:

1. Go to your service in Railway
2. Click on the "Deploy" tab
3. Use Railway CLI or set `RUN_MIGRATIONS=true` and redeploy

Or use Railway CLI:

```bash
railway run alembic upgrade head
```

## Step 8: Update Frontend

Update your frontend's `.env.production` with the Railway backend URL:

```bash
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

## Common Issues & Solutions

### Issue: PORT Error

**Solution**: Ensure `start.sh` properly handles `$PORT` variable (already fixed in our config)

### Issue: Database Connection Failed

**Solution**:

- Check if PostgreSQL service is running
- Verify `DATABASE_URL` is set automatically by Railway
- Check database logs in Railway

### Issue: AWS Credentials Invalid

**Solution**:

- Verify `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are set
- Check IAM permissions for S3, SQS, Bedrock, and Cognito

### Issue: CORS Errors

**Solution**:

- Ensure `FRONTEND_URL` matches your actual frontend URL
- Check `ALLOWED_HOSTS` includes your backend domain

## Monitoring

### View Logs

```bash
railway logs
```

### View Metrics

Go to Railway dashboard → Your service → Metrics tab

### Set Up Alerts

Configure alerts in Railway dashboard for:

- High error rate
- High memory usage
- Deployment failures

## Rollback

If deployment fails:

1. Go to Railway dashboard
2. Click on "Deployments"
3. Select a previous successful deployment
4. Click "Redeploy"

## Custom Domain (Optional)

1. Go to your service settings
2. Click "Networking"
3. Add custom domain
4. Update DNS records as instructed
5. Update `ALLOWED_HOSTS` and `FRONTEND_URL` accordingly

## Scaling

Railway automatically scales based on:

- CPU usage
- Memory usage
- Request volume

To configure scaling:

1. Go to service settings
2. Adjust resources in "Settings" tab

## Security Checklist

- [ ] `SECRET_KEY` is unique and strong (64+ characters)
- [ ] `ENV=production` is set
- [ ] API docs disabled (`/docs` and `/redoc` not accessible)
- [ ] HTTPS only (Railway provides SSL by default)
- [ ] AWS credentials are secure and have minimal permissions
- [ ] Rate limiting is enabled
- [ ] CORS is properly configured
- [ ] Database credentials are secure (managed by Railway)

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- GitHub Issues: https://github.com/yourusername/codexa/issues
