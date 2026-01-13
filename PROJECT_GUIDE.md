# Quizzy Project Guide

## Table of Contents
- [Architecture Overview](#architecture-overview)
- [Application Structure](#application-structure)
- [Development Workflow](#development-workflow)
- [Testing Standards](#testing-standards)
- [Code Quality](#code-quality)
- [Security Practices](#security-practices)
- [Deployment Process](#deployment-process)

## Architecture Overview

Quizzy follows a **service-oriented architecture** with clear separation of concerns:

```
User Request
    ↓
Django URL Router
    ↓
Views (Request Handling)
    ↓
Services (Business Logic)
    ↓
Models (Data Layer)
    ↓
PostgreSQL/Redis
```

### Key Design Principles

1. **Separation of Concerns**: Views handle HTTP, services handle business logic
2. **DRY (Don't Repeat Yourself)**: Shared logic in services
3. **Security First**: Input validation, output sanitization
4. **Performance**: Caching, query optimization, async tasks
5. **Scalability**: Designed for 10,000+ concurrent users

## Application Structure

### accounts
- **Purpose**: User authentication and profile management
- **Models**: CustomUser, UserProfile, College, LoginSession
- **Key Features**: JWT auth, email/phone verification
- **Dependencies**: None (base app)

### quizzes
- **Purpose**: Core quiz engine
- **Models**: Category, Quiz, Question, QuizAttempt, Answer
- **Key Features**: Timed quizzes, auto-grading
- **Dependencies**: accounts

### daily_quizzes
- **Purpose**: Daily challenges and key system
- **Models**: DailyQuiz, RewardedVideoAd, AdView, KeyLedger
- **Key Features**: Daily unlock, ad-based keys, fraud detection
- **Dependencies**: accounts, quizzes

### leaderboards
- **Purpose**: Ranking system
- **Models**: LeaderboardEntry, RankSnapshot
- **Key Features**: Real-time ranks, college rankings
- **Dependencies**: accounts, quizzes

### xp_system
- **Purpose**: Gamification and rewards
- **Models**: XPLog, XPConfig, UserStats, Badge
- **Key Features**: XP calculation, badge awards
- **Dependencies**: accounts, quizzes

### analytics
- **Purpose**: Reporting and analytics
- **Models**: Report, Analytics
- **Key Features**: PDF reports, charts, insights
- **Dependencies**: All apps

### admin_panel
- **Purpose**: Admin management interface
- **Models**: AdminSettings, FeatureFlag
- **Key Features**: Bulk upload, user management
- **Dependencies**: All apps

### dashboard
- **Purpose**: User dashboard
- **Models**: UserActivityLog, DailyActivityMetric
- **Key Features**: Activity tracking, statistics
- **Dependencies**: accounts, quizzes, xp_system

### core
- **Purpose**: Platform-wide utilities
- **Models**: PlatformSettings, FeatureFlag
- **Key Features**: Middleware, decorators, exceptions
- **Dependencies**: None

## Development Workflow

### 1. Feature Development

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes
# Run tests
pytest

# Format code
black .
isort .

# Commit
git commit -m "feat: your feature description"

# Push and create PR
```

### 2. Database Changes

```bash
# Create migration
python manage.py makemigrations app_name

# Review migration file
cat app_name/migrations/xxxx_migration.py

# Apply migration
python manage.py migrate

# Rollback if needed
python manage.py migrate app_name previous_migration_name
```

### 3. Adding New Models

1. Define model in `models.py`
2. Add comprehensive docstring
3. Add `Meta` class with indexes
4. Create migration
5. Register in `admin.py`
6. Create serializer in `serializers.py`
7. Write tests in `tests/test_app.py`

## Testing Standards

### Test Structure

```python
# tests/test_quizzes.py
import pytest
from django.test import TestCase
from accounts.models import CustomUser
from quizzes.models import Quiz

class QuizModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_quiz_creation(self):
        quiz = Quiz.objects.create(
            title='Test Quiz',
            duration=600
        )
        self.assertEqual(quiz.title, 'Test Quiz')
```

### Running Tests

```bash
# All tests
pytest

# Specific app
pytest tests/test_quizzes.py

# With coverage
pytest --cov=. --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Code Quality

### Style Guide

- **PEP 8**: Follow Python style guide
- **Line Length**: Max 100 characters
- **Imports**: Sorted and grouped
- **Docstrings**: Required for all public functions/classes

### Pre-commit Checks

```bash
# Format
black .

# Sort imports
isort .

# Lint
flake8

# Type checking (optional)
mypy .
```

## Security Practices

### Input Validation

```python
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError

def validate_email(email):
    validator = EmailValidator()
    try:
        validator(email)
    except ValidationError:
        raise ValueError('Invalid email')
```

### SQL Injection Prevention

```python
# ✅ SAFE - Using ORM
Quiz.objects.filter(title__contains=user_input)

# ❌ DANGEROUS - String concatenation
cursor.execute(f"SELECT * FROM quiz WHERE title = '{user_input}'")
```

### Password Handling

```python
# ✅ SAFE - Using Django's set_password
user.set_password(raw_password)
user.save()

# ❌ DANGEROUS - Storing raw password
user.password = raw_password  # NO!
```

## Deployment Process

### Development

```bash
python manage.py runserver
```

### Staging

```bash
# Set environment
export DJANGO_SETTINGS_MODULE=quizzy.settings
export DEBUG=False

# Run with Gunicorn
gunicorn quizzy.wsgi:application --config gunicorn_config.py
```

### Production (Docker)

```bash
# Build
docker-compose build

# Deploy
docker-compose up -d

# View logs
docker-compose logs -f

# Scale workers
docker-compose up -d --scale celery=3
```

### Heroku

```bash
# Login
heroku login

# Create app
heroku create your-app-name

# Add PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Add Redis
heroku addons:create heroku-redis:hobby-dev

# Set environment variables
heroku config:set SECRET_KEY=your-secret-key
heroku config:set DEBUG=False

# Deploy
git push heroku main

# Run migrations
heroku run python manage.py migrate

# Create superuser
heroku run python manage.py createsuperuser
```

## Appendix

### Useful Commands

```bash
# Django shell
python manage.py shell

# Database shell
python manage.py dbshell

# Show migrations
python manage.py showmigrations

# Create fixtures
python manage.py dumpdata app_name > fixtures/data.json

# Load fixtures
python manage.py loaddata fixtures/data.json
```

### Environment Variables

All sensitive configuration must be in `.env`:
- `SECRET_KEY` - Django secret key
- `DB_PASSWORD` - Database password
- `EMAIL_HOST_PASSWORD` - Email credentials
- `SENTRY_DSN` - Error tracking

See `.env.example` for complete list.
