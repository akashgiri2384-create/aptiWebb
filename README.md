# Quizzy - Educational Quiz Platform

> **Production-ready Django platform for 10,000+ concurrent users**

Quizzy is a scalable educational quiz platform built with Django 4.2, featuring real-time leaderboards, XP systems, daily challenges, and comprehensive analytics. Designed for high performance and enterprise-grade security.

## 🚀 Features

- **User Authentication**: Email/phone + JWT authentication
- **Quiz Engine**: Timed quizzes with various question types
- **Daily Challenges**: Unlock with keys earned through ads
- **XP & Rewards**: Gamified learning with badges and achievements
- **Leaderboards**: Real-time rankings (overall, category, college-based)
- **Analytics**: Comprehensive user performance tracking
- **Admin Panel**: Bulk quiz upload via CSV, user management
- **Multi-tenant**: College-specific leaderboards and features

## 🛠️ Tech Stack

**Backend:**
- Django 4.2 LTS
- Django REST Framework 3.14
- PostgreSQL (primary database)
- Redis (caching & Celery broker)
- Celery + Beat (background tasks)

**Security:**
- JWT authentication (SimpleJWT)
- bcrypt password hashing
- CORS protection
- Rate limiting
- CSRF protection
- Security headers (HSTS, CSP)

**Deployment:**
- Docker + Docker Compose
- Gunicorn (WSGI server)
- WhiteNoise (static files)
- Heroku-ready (Procfile included)

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- pip & virtualenv

## ⚡ Quick Start

### 1. Clone and Setup

```bash
cd d:\aptiWeb
python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
copy .env.example .env
# Edit .env with your database credentials and secrets
```

### 3. Database Setup

```bash
# Create PostgreSQL database
createdb quizzy

# Run migrations
python manage.py makemigrations
python manage.py migrate
```

### 4. Create Superuser

```bash
python manage.py createsuperuser
```

### 5. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 6. Run Development Server

```bash
python manage.py runserver
```

Visit: **http://localhost:8000/admin**

### 7. Start Celery (Optional, in separate terminals)

```bash
# Terminal 2: Celery Worker
celery -A quizzy worker --loglevel=info

# Terminal 3: Celery Beat
celery -A quizzy beat --loglevel=info
```

## 🐳 Docker Deployment

```bash
# Build and run all services
docker-compose up --build

# Run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f web

# Stop all services
docker-compose down
```

Services:
- **web**: Django app (http://localhost:8000)
- **db**: PostgreSQL database
- **redis**: Redis cache/broker
- **celery**: Background task worker
- **celery-beat**: Scheduled task scheduler

## 📁 Project Structure

```
quizzy/
├── accounts/              # User authentication & profiles
├── quizzes/               # Quiz engine
├── daily_quizzes/         # Daily challenges & key system
├── leaderboards/          # Ranking system
├── xp_system/             # XP & rewards
├── analytics/             # Reports & analytics
├── admin_panel/           # Admin dashboard
├── dashboard/             # User dashboard
├── core/                  # Platform utilities
├── quizzy/                # Django settings
├── templates/             # HTML templates
├── static/                # CSS, JS, images
├── media/                 # User uploads
├── docs/                  # Documentation
├── tests/                 # Test suite
└── logs/                  # Application logs
```

## 🔧 Development

### Install Development Dependencies

```bash
pip install -r requirements-dev.txt
```

### Run Tests

```bash
pytest
```

### Code Quality

```bash
# Format code
black .

# Sort imports
isort .

# Lint
flake8
```

### Create Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

## 📚 key Documentation

- [Project Guide](PROJECT_GUIDE.md) - Complete development guide
- [API Documentation](docs/API.md) - API endpoints reference
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment
- [Architecture](docs/ARCHITECTURE.md) - System architecture
- [Database Schema](docs/DATABASE.md) - Database design
- [XP System](docs/XP_SYSTEM.md) - XP calculation rules

## 🔐 Security

- **Authentication**: JWT tokens (1-hour access, 7-day refresh)
- **Password Hashing**: bcrypt with 10+ rounds
- **Rate Limiting**: 100/hour anonymous, 1000/hour authenticated
- **HTTPS**: Enforced in production
- **Input Validation**: Comprehensive validation on all endpoints
- **SQL Injection**: Protected via Django ORM
- **XSS Protection**: Auto-escaping in templates
- **CSRF Protection**: Enabled on all forms

## 🎯 Performance

**Target Metrics:**
- Leaderboard Query: <100ms
- Dashboard Load: <500ms
- Quiz Submission: <200ms
- API Response: <300ms average

**Optimizations:**
- Redis caching (5-level strategy)
- Database connection pooling (50 connections)
- Query optimization (select_related, prefetch_related)
- Async background jobs (Celery)
- Static file compression (WhiteNoise)

## 📊 Monitoring

**Logs:**
- `logs/app.log` - General application logs
- `logs/errors.log` - Error logs
- `logs/performance.log` - Performance metrics

**Health Check:**
```bash
curl http://localhost:8000/health/
```

## 🤝 Contributing

This is a production codebase. All contributions must:
- Pass all tests
- Follow code quality standards (black, isort, flake8)
- Include comprehensive documentation
- Meet security requirements
- Maintain >80% test coverage

## 📄 License

Proprietary - All rights reserved

## 🆘 Troubleshooting

See [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for common issues and solutions.

## 📧 Support

For issues or questions, contact: support@quizzy.com

---

**Built with ❤️ for scalable educational technology** - Ready for 10,000+ concurrent users from day one!
