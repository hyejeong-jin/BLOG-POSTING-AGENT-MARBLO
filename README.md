# Marblo - AI-Powered Blog Post Generation Service

**?? MVP ë²„ì „ ì¶œì‹œ! 10ë¶??ˆì— AI ë¸”ë¡œê·??¬ìŠ¤???ì„± ?œì‘?˜ê¸°**

**ë¹ ë¥¸ ?œì‘**: [MVP ê°€?´ë“œ](./MARBLO_MVP_QUICKSTART.md) ì°¸ê³ 

Marblo??ë¸”ë¡œê±°ë“¤??ì½˜í…ì¸??œì‘ ?œê°„???¨ì¶•?˜ëŠ” AI ê¸°ë°˜ ë¸”ë¡œê·??¬ìŠ¤???ë™ ?ì„± ?œë¹„?¤ì…?ˆë‹¤.

## ?¯ MVP ?µì‹¬ ê¸°ëŠ¥

- ??**ë¸”ë¡œê·??¤í????™ìŠµ**: ?¤ì´ë²?ë¸”ë¡œê·?URL ?…ë ¥ ??AIê°€ ê¸€?°ê¸° ?¤í????™ìŠµ
- ??**?¬ì§„ ?…ë¡œ??*: ?¬ìŠ¤?¸ì— ?¬ìš©???¬ì§„ ? íƒ
- ??**?ë™ ?¬ìŠ¤???ì„±**: ?¤í???+ ?¬ì§„?¼ë¡œ ?„ì „???¬ìŠ¤???ë™ ?ì„±
- ??**ë³µì‚¬ & ë¶™ì—¬?£ê¸°**: ?ì„±???¬ìŠ¤?¸ë? ë¸”ë¡œê·¸ì— ì§ì ‘ ?ìš©

## ?? 3ì´??œì‘?˜ê¸°

### Docker Compose (ê¶Œì¥)
```bash
cd BLOG-POSTING-AGENT
docker-compose up -d
# http://localhost:8000/app ?‘ì†
```

### ?ëŠ” ë¡œì»¬ ?¤í–‰
```bash
python -m venv venv
.\venv\Scripts\activate
pip install -e ".[dev]"
# .env ?Œì¼?ì„œ CLAUDE_API_KEY ?¤ì •
alembic upgrade head
uvicorn app.main:app --reload
```

## ?“± ?¬ìš© ?œë‚˜ë¦¬ì˜¤

```
1. ?Œì›ê°€??ë¡œê·¸??
    ??
2. ë¸”ë¡œê·?URL ?…ë ¥ ???¤í????™ìŠµ (30ì´?
    ??
3. ?¬ì§„ ?…ë¡œ??+ ì£¼ì œ ?…ë ¥
    ??
4. "?¬ìŠ¤???ì„±" ?´ë¦­ (20-30ì´?
    ??
5. ?ì„±???¬ìŠ¤??ë³µì‚¬ ??ë¸”ë¡œê·¸ì— ë¶™ì—¬?£ê¸°
```

## ?“Š API ?”ë“œ?¬ì¸??(MVP)

### 1. ë¸”ë¡œê·??™ìŠµ
```bash
POST /api/v1/marblo/learn-blog
Content-Type: application/json
Authorization: Bearer {token}

{
  "blog_url": "https://blog.naver.com/username",
  "posts_to_analyze": 5
}
```

### 2. ?¬ìŠ¤???ì„±
```bash
POST /api/v1/marblo/generate-post
Content-Type: application/json
Authorization: Bearer {token}

{
  "photo_ids": ["uuid1", "uuid2"],
  "topic": "?€ì¶œì— ?€???Œì•„ë³´ì",
  "additional_context": "ì¶”ê? ?•ë³´"
}
```

### 3. ?¬ìŠ¤??ì¡°íšŒ
```bash
GET /api/v1/marblo/posts/list
Authorization: Bearer {token}
```

## ?—ï¸??„ì²´ ê¸°ëŠ¥

- **AI-Powered Writing Style Learning**: ê¸°ì¡´ ë¸”ë¡œê·??¬ìŠ¤??ë¶„ì„?¼ë¡œ ê¸€?°ê¸° ?¤í????™ìŠµ
- **Automated Photo Analysis**: ?¬ì§„?ì„œ ?„ì¹˜, ê°€ê²? ?¤ëª… ??ë©”í??°ì´???ë™ ì¶”ì¶œ
- **Intelligent Post Generation**: ?¬ì§„ + ë©”í??°ì´??+ ?¤í??¼ë¡œ ë¸”ë¡œê·??¬ìŠ¤???ë™ ?ì„±
- **Multi-Platform Export**: ?¤ì´ë²?ë¸”ë¡œê·? ?°ìŠ¤? ë¦¬ ?±ìœ¼ë¡?ì§ì ‘ ë°œí–‰ (?ˆì •)
- **Generation History**: ?ì„±??ëª¨ë“  ?¬ìŠ¤???€??ë°??¸ì§‘ ê¸°ë¡
- **Multi-User Support**: ê°€ì¡?êµ¬ì„±??ì´ˆë?ë¡??¨ê»˜ ?‘ì„± (?ˆì •)
- **Production-Ready**: AWS ê¸°ë°˜ ?„ë¡œ?•ì…˜ ?¸í”„??

## Tech Stack

- **Backend**: Python 3.11+, FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Caching**: Redis
- **Cloud Infrastructure**: AWS (S3, Bedrock/Claude API, CloudWatch)
- **Authentication**: JWT with bcrypt
- **Logging**: Structlog with CloudWatch integration
- **Web Server**: Uvicorn

## Project Structure

```
BLOG-POSTING-AGENT/
?œâ??€ app/                          # Main application package
??  ?œâ??€ __init__.py
??  ?œâ??€ config.py                 # Environment configuration
??  ?œâ??€ logging_config.py          # Logging setup
??  ?œâ??€ main.py                   # FastAPI app initialization
??  ?œâ??€ models/                   # Database models and schemas
??  ?œâ??€ routers/                  # API route handlers
??  ?œâ??€ services/                 # Business logic layer
??  ?œâ??€ utils/                    # Utility functions
??  ?”â??€ db.py                     # Database connection (to be created)
?œâ??€ tests/                        # Test suite
??  ?”â??€ conftest.py              # Test configuration (to be created)
?œâ??€ migrations/                   # Database migrations (Alembic)
?œâ??€ terraform/                    # Infrastructure as Code
?œâ??€ .env.example                  # Environment variables template
?œâ??€ .gitignore                    # Git ignore rules
?œâ??€ pyproject.toml               # Project dependencies
?œâ??€ README.md                     # This file
?”â??€ docker-compose.yml            # Local development setup (to be created)
```

## Installation

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 13+
- Redis 6+
- AWS Account (for S3, Bedrock, CloudWatch)

### Setup Development Environment

1. **Clone the repository**:
   ```bash
   git clone https://github.com/marblo/marblo.git
   cd marblo
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**:
   ```bash
   # Database migrations will be set up in subsequent tasks
   ```

6. **Run the application**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   The API will be available at `http://localhost:8000`
   - API Documentation: `http://localhost:8000/docs`
   - Alternative Docs: `http://localhost:8000/redoc`

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
# Environment
ENVIRONMENT=development
DEBUG=true

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/marblo

# Redis
REDIS_URL=redis://localhost:6379/0

# AWS Services
AWS_REGION=us-east-1
AWS_S3_BUCKET=marblo-photos
AWS_CLOUDWATCH_LOG_GROUP=/marblo/application

# AI Services
CLAUDE_API_KEY=your_key
OPENAI_API_KEY=your_key

# Security
SECRET_KEY=your_secret_key_change_in_production
```

See `.env.example` for complete list of configuration options.

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run tests matching pattern
pytest -k "test_login"
```

### Code Quality

```bash
# Format code
black app tests

# Sort imports
isort app tests

# Lint code
flake8 app tests
pylint app

# Type checking
mypy app
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## API Documentation

### Authentication

All protected endpoints require JWT token in Authorization header:

```
Authorization: Bearer <token>
```

### Health Check

```bash
curl http://localhost:8000/health
```

### API Endpoints

Full API documentation available at `/docs` endpoint when running the application.

Core endpoint categories:
- `/api/v1/auth` - Authentication and user management
- `/api/v1/style` - Writing style learning and profiles
- `/api/v1/photos` - Photo upload and metadata extraction
- `/api/v1/posts` - Blog post generation and management
- `/api/v1/history` - Generation history
- `/api/v1/export` - Post export and publishing

## Security

- JWT-based authentication with bcrypt password hashing
- Rate limiting to prevent abuse (5 login attempts/minute)
- SQL injection protection through SQLAlchemy ORM
- CORS configuration for cross-origin requests
- Security headers (X-Frame-Options, CSP, HSTS)
- Encrypted secrets management via AWS Secrets Manager
- All API requests logged for audit trail

### Password Requirements

- Minimum 12 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character

## Logging

Structured logging using structlog with two output modes:

**Development**: Console output with human-readable formatting

**Production**: JSON output to CloudWatch with:
- Timestamp
- Log level
- Logger name
- Message and context
- Exception information when applicable

Access logs at: `/aws/logs/marblo/application` (CloudWatch)

## Performance

- Database connection pooling (default 10 connections)
- Redis caching for style profiles and frequently accessed data
- GZip compression for responses > 1KB
- Rate limiting to prevent abuse
- Async/await for non-blocking I/O

Target metrics:
- API response time: < 2 seconds
- Photo analysis: < 30 seconds
- Post generation: < 60 seconds
- Support 100+ concurrent users

## Deployment

### Local Development

```bash
docker-compose up
```

### Production Deployment

Infrastructure as Code templates are in the `terraform/` directory:

```bash
cd terraform
terraform plan
terraform apply
```

This deploys to AWS:
- EC2 instances (auto-scaling)
- RDS PostgreSQL database
- S3 storage buckets
- CloudWatch logging and monitoring
- Application Load Balancer

## Monitoring & Alerting

CloudWatch dashboards track:
- Post generation success rate
- Photo analysis success rate
- Average generation time
- API response times
- System resource usage

Alerts configured for:
- Generation success rate < 80%
- API response time > 2 seconds
- Database CPU > 80%

## Contributing

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes and add tests
3. Run quality checks: `black`, `flake8`, `pytest`
4. Submit pull request

## License

MIT License - see LICENSE file

## Support

For issues, questions, or contributions, please visit:
- GitHub: https://github.com/marblo/marblo
- Documentation: https://docs.marblo.com
- Issues: https://github.com/marblo/marblo/issues

## Roadmap

- [ ] Database models and ORM setup
- [ ] User authentication and registration
- [ ] Photo upload and S3 integration
- [ ] AI-powered metadata extraction
- [ ] Writing style learning
- [ ] Blog post generation
- [ ] Multi-user and family member support
- [ ] Integration with Naver Blog
- [ ] Analytics and monitoring dashboard


