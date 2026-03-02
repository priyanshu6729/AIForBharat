# Codexa Backend 🚀

AI-powered code learning platform backend built with FastAPI, PostgreSQL, AWS Cognito, and AWS Bedrock.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ Features

- 🔐 **Authentication**: AWS Cognito integration with JWT tokens
- 🤖 **AI Guidance**: Multi-level code assistance using AWS Bedrock
- 📊 **Code Analysis**: AST parsing and complexity analysis
- 🎓 **Learning Paths**: Structured programming courses
- 💾 **PostgreSQL**: Relational database with pgvector for embeddings
- 🔒 **Security**: Rate limiting, CORS, input validation
- 📝 **API Documentation**: Auto-generated OpenAPI/Swagger docs

## 🏗️ Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Client    │─────▶│   FastAPI    │─────▶│  PostgreSQL │
│  (Frontend) │      │   Backend    │      │   Database  │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ├─────▶ AWS Cognito (Auth)
                            ├─────▶ AWS Bedrock (AI)
                            ├─────▶ AWS S3 (Storage)
                            └─────▶ AWS Lambda (Analysis)
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- AWS Account with configured credentials
- AWS Cognito User Pool
- Git

### Local Development

1. **Clone the repository**

```bash
git clone https://github.com/YOUR_USERNAME/codexa-backend.git
cd codexa-backend
```

2. **Create virtual environment**

```bash
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Setup environment variables**

```bash
cp .env.example .env
# Edit .env with your configuration
```

Required environment variables:

- `DATABASE_URL`: PostgreSQL connection string
- `COGNITO_USER_POOL_ID`: AWS Cognito User Pool ID
- `COGNITO_CLIENT_ID`: AWS Cognito App Client ID
- `AWS_REGION`: AWS region (default: us-east-1)
- `SECRET_KEY`: Generate with `openssl rand -hex 32`

5. **Initialize database**

```bash
# Create database
createdb codexa

# Run migrations
alembic upgrade head

# Optional: Seed sample data
python scripts/seed_db.py
```

6. **Run the application**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit http://localhost:8000/docs for interactive API documentation.

## 📦 Project Structure

```
codexa-backend/
├── app/
│   ├── main.py              # FastAPI application
│   ├── database.py          # Database connection
│   ├── deps.py              # Dependencies (auth, db)
│   ├── core/
│   │   ├── config.py        # Configuration management
│   │   └── logging.py       # Logging setup
│   ├── models/              # SQLAlchemy models
│   ├── routes/              # API routes
│   │   └── auth.py          # Authentication endpoints
│   ├── routers/             # Feature routers
│   │   ├── analyze.py       # Code analysis
│   │   ├── execute.py       # Code execution
│   │   ├── guidance.py      # AI guidance
│   │   ├── learn.py         # Learning paths
│   │   └── session.py       # User sessions
│   ├── schemas/             # Pydantic schemas
│   └── services/            # Business logic
│       ├── cognito_client.py
│       ├── bedrock_client.py
│       └── auth_service.py
├── alembic/                 # Database migrations
├── scripts/                 # Utility scripts
├── tests/                   # Test suite
├── .env.example             # Environment template
├── requirements.txt         # Python dependencies
└── README.md
```

## 🔌 API Endpoints

### Authentication

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/confirm` - Confirm email
- `GET /api/auth/me` - Get current user

### Code Operations

- `POST /api/analyze` - Analyze code structure
- `POST /api/execute` - Execute code safely
- `POST /api/visualize` - Generate code visualizations
- `POST /api/guidance` - Get AI-powered guidance

### Learning

- `GET /api/learn/paths` - List learning paths
- `GET /api/learn/paths/{id}` - Get learning path details
- `GET /api/progress` - Get user progress
- `POST /api/progress` - Update progress

### Sessions

- `GET /api/sessions` - List user sessions
- `POST /api/sessions` - Create new session
- `GET /api/sessions/{id}` - Get session details

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_auth.py -v
```

## 🐳 Docker Deployment

```bash
# Build image
docker build -t codexa-backend .

# Run container
docker run -d \
  --name codexa-backend \
  -p 8000:8000 \
  --env-file .env \
  codexa-backend
```

## ☁️ Production Deployment

### Railway (Recommended)

1. Install Railway CLI:

```bash
npm i -g @railway/cli
```

2. Login and deploy:

```bash
railway login
railway init
railway up
```

3. Set environment variables in Railway dashboard

### AWS EC2

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed AWS deployment guide.

### Vercel/Netlify (Serverless)

See [docs/SERVERLESS_DEPLOY.md](docs/SERVERLESS_DEPLOY.md)

## 🔐 Security

- ✅ JWT-based authentication
- ✅ Rate limiting (60 req/min, 1000 req/hour)
- ✅ CORS configuration
- ✅ Input validation with Pydantic
- ✅ SQL injection protection with SQLAlchemy
- ✅ Secrets management with environment variables
- ✅ HTTPS enforcement in production

## 📊 Monitoring

Integration with:

- Sentry for error tracking
- CloudWatch for AWS metrics
- Custom logging with structured JSON

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- FastAPI framework
- AWS Services (Cognito, Bedrock, S3)
- PostgreSQL with pgvector
- Tree-sitter for code parsing

## 📧 Contact

Your Name - [@yourhandle](https://twitter.com/yourhandle)

Project Link: [https://github.com/YOUR_USERNAME/codexa-backend](https://github.com/YOUR_USERNAME/codexa-backend)

---

Made with ❤️ by Priyanshu Raj
