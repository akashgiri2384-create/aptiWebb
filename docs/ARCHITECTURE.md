# Quizzy Platform Architecture

## System Overview

Quizzy is a production-grade educational quiz platform built for 10,000+ concurrent users with enterprise-level security, performance, and scalability.

```
┌─────────────────────────────────────────────────────────────┐
│                      USER INTERFACE                          │
│  Web Browsers • Mobile Browsers • Progressive Web App (PWA) │
└─────────────────────────────────────────────────────────────┘
                            ↓ HTTPS
┌─────────────────────────────────────────────────────────────┐
│                     LOAD BALANCER                            │
│                   (Nginx / Heroku Router)                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  APPLICATION LAYER                           │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Gunicorn    │  │  Gunicorn    │  │  Gunicorn    │       │
│  │  Worker 1    │  │  Worker 2    │  │  Worker N    │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│         ↓                  ↓                  ↓              │
│  ┌─────────────────────────────────────────────────┐        │
│  │          Django 4.2 Application                  │        │
│  │  • Accounts • Quizzes • Daily Quizzes            │        │
│  │  • Leaderboards • XP System • Analytics          │        │
│  │  • Admin Panel • Dashboard • Core                │        │
│  └─────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
         ↓                          ↓                   ↓
┌────────────────┐       ┌────────────────┐    ┌───────────────┐
│   PostgreSQL   │       │     Redis      │    │    Celery     │
│   (Primary DB) │       │ (Cache/Broker) │    │   Workers     │
│                │       │                │    │               │
│ • Users        │       │ • Sessions     │    │ • XP Update   │
│ • Quizzes      │       │ • Leaderboard  │    │ • Leaderboard │
│ • Attempts     │       │ • User Stats   │    │ • Reports     │
│ • XP Logs      │       │ • Quiz Cache   │    │ • Email       │
└────────────────┘       └────────────────┘    └───────────────┘
```

## Application Architecture

### Layered Architecture

```
┌──────────────────────────────────────────────┐
│          Presentation Layer                   │
│  (Templates, Static Files, API Responses)     │
└──────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────┐
│            Controller Layer                   │
│  (Views, URL Routing, Authentication)         │
└──────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────┐
│          Business Logic Layer                 │
│  (Services, Validators, Permissions)          │
└──────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────┐
│            Data Access Layer                  │
│  (Models, ORM, Database Queries)              │
└──────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────┐
│            Database Layer                     │
│  (PostgreSQL, Redis)                          │
└──────────────────────────────────────────────┘
```

## Caching Strategy

### 5-Level Redis Cache

| Level | Data Type | TTL | Usage |
|-------|-----------|-----|-------|
| L1 | User Sessions | 10 min | Active user data |
| L2 | Leaderboard | 5 min | Live rankings |
| L3 | Quiz Questions | 1 hour | Question cache |
| L4 | Category Data | 24 hours | Metadata |
| L5 | College List | 24 hours | Static data |

### Cache Invalidation

- **Time-based**: TTL expires automatically
- **Event-based**: Manual invalidation on data change
- **Manual**: Admin cache purge

## Background Jobs (Celery)

### Job Priorities

**High Priority (Immediate)**
- XP calculation
- Key distribution
- Leaderboard updates

**Medium Priority (5 minutes)**
- Email notifications
- Daily report generation
- Ad fraud detection

**Low Priority (Hourly/Daily)**
- Weekly/monthly reports
- Data archival
- Log cleanup

### Beat Schedule

| Task | Schedule | Description |
|------|----------|-------------|
| reset_daily_quizzes | Daily 00:00 IST | Reset daily challenges |
| update_leaderboards | Every 5 min | Refresh rankings |
| generate_weekly_reports | Monday 20:00 IST | Create reports |
| cleanup_fraudulent_ads | Daily 02:00 IST | Remove fraud |

## Database Design

### Schema Overview

```
┌─────────────┐      ┌──────────────┐      ┌────────────┐
│ CustomUser  │──────│ UserProfile  │──────│  College   │
└─────────────┘      └──────────────┘      └────────────┘
      │                                           
      │ 1:N                                       
      ↓                                           
┌─────────────┐      ┌──────────────┐      ┌────────────┐
│QuizAttempt  │──────│    Quiz      │──────│  Category  │
└─────────────┘      └──────────────┘      └────────────┘
      │                     │                     
      │ 1:N                 │ 1:N                 
      ↓                     ↓                     
┌─────────────┐      ┌──────────────┐            
│   Answer    │      │   Question   │            
└─────────────┘      └──────────────┘            
```

### Indexing Strategy

**Single-column Indexes:**
- `users.email` (unique)
- `users.total_xp` (for leaderboard)
- `quiz_attempts.user_id`

**Composite Indexes:**
- `(user_id, quiz_id)` - Quiz attempts lookup
- `(user_id, created_at)` - User history
- `(category_id, difficulty)` - Quiz filtering

### Denormalization Strategy

Cached values in User model:
- `total_xp` - Sum of XP logs
- `current_streak` - Calculated daily
- `longest_streak` - Historical max

Cached values in UserProfile:
- `total_quizzes_attempted`
- `total_quizzes_passed`
- `average_score`

**Update Strategy**: On change, not on read

## Security Architecture

### Authentication Flow

```
1. User Login
   ↓
2. Validate Credentials (bcrypt)
   ↓
3. Generate JWT (access + refresh)
   ↓
4. Return Tokens
   ↓
5. Client stores tokens (httpOnly cookie/localStorage)
   ↓
6. Subsequent requests include token
   ↓
7. Middleware validates JWT
   ↓
8. Access granted
```

### Security Layers

1. **Transport Security**: HTTPS only
2. **Authentication**: JWT with rotation
3. **Authorization**: Permission-based access
4. **Input Validation**: All endpoints
5. **Output Sanitization**: XSS prevention
6. **Rate Limiting**: Per-user throttling
7. **CSRF Protection**: Token-based
8. **SQL Injection**: ORM protection

## Performance Optimizations

### Query Optimization

```python
# ❌ BAD: N+1 queries
quizzes = Quiz.objects.all()
for quiz in quizzes:
    print(quiz.category.name)  # DB hit per quiz!

# ✅ GOOD: Single query with JOIN
quizzes = Quiz.objects.select_related('category').all()
for quiz in quizzes:
    print(quiz.category.name)  # No additional DB hits
```

### Connection Pooling

- **Database**: 50 persistent connections
- **Redis**: 50 connections with retry
- **Connection lifetime**: 10 minutes

### Async Processing

All expensive operations moved to Celery:
- XP calculation
- Report generation
- Email sending
- Leaderboard updates

## Scalability Considerations

### Horizontal Scaling

**Application Layer:**
- Stateless Django workers
- Load balancer distribution
- Auto-scaling based on CPU/memory

**Database Layer:**
- Read replicas for SELECT queries
- Write master for INSERT/UPDATE
- Connection pooling

**Cache Layer:**
- Redis Cluster for high availability
- Sentinel for automatic failover

### Performance Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| Leaderboard Query | <100ms | Cached in Redis |
| Dashboard Load | <500ms | Denormalized stats |
| Quiz Submission | <200ms | Async XP update |
| API Response | <300ms | Average |

## Monitoring & Observability

### Logging

**Log Files:**
- `app.log` - General application logs
- `errors.log` - Error tracking
- `performance.log` - Slow query logs

**Log Rotation:**
- Max size: 10MB
- Backup count: 10 files
- Auto-cleanup after 30 days

### Metrics

**Application Metrics:**
- Request count
- Response time (p50, p95, p99)
- Error rate
- Cache hit rate

**System Metrics:**
- CPU usage
- Memory usage
- Disk I/O
- Network throughput

## Deployment Architecture

### Production Environment

```
┌──────────────────────────────────────────────────┐
│              Cloud Provider (Heroku/AWS)          │
├──────────────────────────────────────────────────┤
│  Load Balancer                                    │
├──────────────────────────────────────────────────┤
│  Web Dynos/Instances (Auto-scaled)                │
│  ├─ Gunicorn Workers                              │
│  └─ Django Application                            │
├──────────────────────────────────────────────────┤
│  Worker Dynos/Instances                           │
│  └─ Celery Workers + Beat                         │
├──────────────────────────────────────────────────┤
│  Database (PostgreSQL)                            │
│  ├─ Primary (writes)                              │
│  └─ Read Replicas (reads)                         │
├──────────────────────────────────────────────────┤
│  Cache (Redis)                                    │
│  └─ High-availability cluster                     │
├──────────────────────────────────────────────────┤
│  Static Files (CDN)                               │
│  └─ CloudFront / Fastly                           │
└──────────────────────────────────────────────────┘
```

## Technology Stack

**Backend:**
- Django 4.2 LTS
- Python 3.11
- PostgreSQL 15
- Redis 7
- Celery 5.3

**Infrastructure:**
- Docker & Docker Compose
- Gunicorn (WSGI)
- WhiteNoise (static files)
- Heroku / AWS

**Monitoring:**
- Sentry (error tracking)
- Custom logging
- Performance metrics

---

**Design for 10,000+ concurrent users from day one!**
