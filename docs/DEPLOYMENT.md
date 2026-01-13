# Quizzy Deployment Guide

## Table of Contents
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Heroku Deployment](#heroku-deployment)
- [Production Checklist](#production-checklist)

## Local Development

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### Setup Steps

1. **Clone Repository**
   ```bash
   cd d:\aptiWeb
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development only
   ```

4. **Environment Configuration**
   ```bash
   copy .env.example .env  # Windows
   cp .env.example .env    # Linux/Mac
   ```
   
   Edit `.env` with your settings:
   ```env
   DEBUG=True
   SECRET_KEY=your-generated-secret-key
   DB_NAME=quizzy
   DB_USER=postgres
   DB_PASSWORD=your_password
   DB_HOST=localhost
   DB_PORT=5432
   REDIS_URL=redis://localhost:6379/0
   ```

5. **Database Setup**
   ```bash
   createdb quizzy
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. **Collect Static Files**
   ```bash
   python manage.py collectstatic --noinput
   ```

7. **Start Server**
   ```bash
   python manage.py runserver
   ```

8. **Start Celery** (Optional, separate terminals)
   ```bash
   # Terminal 2
   celery -A quizzy worker --loglevel=info
   
   # Terminal 3
   celery -A quizzy beat --loglevel=info
   ```

## Docker Deployment

### Prerequisites
- Docker 20+
- Docker Compose 2+

### Deployment

1. **Build Images**
   ```bash
   docker-compose build
   ```

2. **Start Services**
   ```bash
   docker-compose up -d
   ```

3. **Run Migrations**
   ```bash
   docker-compose exec web python manage.py migrate
   docker-compose exec web python manage.py createsuperuser
   ```

4. **View Logs**
   ```bash
   docker-compose logs -f web
   ```

5. **Stop Services**
   ```bash
   docker-compose down
   ```

### Docker Services
- **web** (port 8000): Django application
- **db** (port 5432): PostgreSQL database
- **redis** (port 6379): Redis cache/broker
- **celery**: Background task worker
- **celery-beat**: Scheduled task scheduler

## Heroku Deployment

### Prerequisites
- Heroku CLI installed
- Heroku account

### Deployment Steps

1. **Login to Heroku**
   ```bash
   heroku login
   ```

2. **Create Application**
   ```bash
   heroku create your-app-name
   ```

3. **Add Add-ons**
   ```bash
   # PostgreSQL
   heroku addons:create heroku-postgresql:hobby-dev
   
   # Redis
   heroku addons:create heroku-redis:hobby-dev
   ```

4. **Set Environment Variables**
   ```bash
   heroku config:set SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
   heroku config:set DEBUG=False
   heroku config:set ALLOWED_HOSTS=your-app-name.herokuapp.com
   ```

5. **Deploy**
   ```bash
   git push heroku main
   ```

6. **Run Migrations**
   ```bash
   heroku run python manage.py migrate
   heroku run python manage.py createsuperuser
   heroku run python manage.py collectstatic --noinput
   ```

7. **View Application**
   ```bash
   heroku open
   ```

8. **View Logs**
   ```bash
   heroku logs --tail
   ```

### Heroku Configuration Files
- `Procfile`: Defines web, worker, and beat processes
- `runtime.txt`: Specifies Python version
- `requirements.txt`: Python dependencies

## Production Checklist

### Security
- [ ] `DEBUG=False` in production
- [ ] Strong `SECRET_KEY` (50+ characters)
- [ ] `ALLOWED_HOSTS` configured correctly
- [ ] HTTPS enforced (`SECURE_SSL_REDIRECT=True`)
- [ ] Secure cookies enabled
- [ ] HSTS headers configured
- [ ] Database credentials secure
- [ ] Redis password protected
- [ ] CORS origins whitelisted

### Performance
- [ ] Static files collected
- [ ] WhiteNoise compression enabled
- [ ] Database connection pooling configured
- [ ] Redis caching working
- [ ] Celery workers running
- [ ] Gunicorn workers optimized (CPU * 2 + 1)

### Monitoring
- [ ] Error tracking (Sentry) configured
- [ ] Application logs accessible
- [ ] Performance monitoring active
- [ ] Health check endpoint working
- [ ] Database backups automated
- [ ] Redis persistence configured

### Database
- [ ] Migrations applied
- [ ] Indexes created
- [ ] Initial data loaded
- [ ] Backup strategy in place
- [ ] Connection pooling enabled

### Email
- [ ] SMTP credentials configured
- [ ] Email templates tested
- [ ] From address verified
- [ ] Rate limits configured

### Celery
- [ ] Broker URL configured
- [ ] Result backend configured
- [ ] Beat schedule active
- [ ] Workers scaled appropriately
- [ ] Task monitoring enabled

## Environment Variables Reference

### Required
- `SECRET_KEY`: Django secret key
- `DB_NAME`: Database name
- `DB_USER`: Database username
- `DB_PASSWORD`: Database password
- `DB_HOST`: Database host
- `DB_PORT`: Database port

### Optional
- `DEBUG`: Debug mode (default: False)
- `ALLOWED_HOSTS`: Comma-separated hosts
- `REDIS_URL`: Redis connection string
- `EMAIL_HOST_USER`: SMTP username
- `EMAIL_HOST_PASSWORD`: SMTP password
- `SENTRY_DSN`: Sentry error tracking DSN

## Troubleshooting

### Static Files Not Loading
```bash
python manage.py collectstatic --noinput
# Verify STATIC_ROOT and STATICFILES_STORAGE
```

### Database Connection Error
```bash
# Check credentials
# Verify PostgreSQL is running
# Test connection: psql -U postgres -h localhost
```

### Celery Tasks Not Running
```bash
# Check broker connection
# Verify Redis is running
# Test: redis-cli ping
```

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

For more issues, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
