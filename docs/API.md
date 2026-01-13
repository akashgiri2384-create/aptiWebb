# Quizzy API Documentation

## Base URL
```
Development: http://localhost:8000/api
Production: https://your-domain.com/api
```

## Authentication

All authenticated endpoints require a JWT token in the Authorization header:

```
Authorization: Bearer <access_token>
```

### Obtain Token

**POST** `/accounts/login/`

Request:
```json
{
    "email": "user@example.com",
    "password": "password123"
}
```

Response:
```json
{
    "success": true,
    "data": {
        "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "user": {
            "id": "uuid",
            "email": "user@example.com",
            "first_name": "John",
            "last_name": "Doe"
        }
    }
}
```

### Refresh Token

**POST** `/accounts/token/refresh/`

Request:
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

Response:
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

## Accounts Endpoints

### Register User

**POST** `/accounts/register/`

**Authentication**: Not required

Request:
```json
{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe"
}
```

Response:
```json
{
    "success": true,
    "data": {
        "user": {
            "id": "uuid",
            "email": "user@example.com"
        },
        "message": "Verification email sent"
    }
}
```

### Get Profile

**GET** `/accounts/profile/`

**Authentication**: Required

Response:
```json
{
    "success": true,
    "data": {
        "user": {
            "id": "uuid",
            "email": "user@example.com",
            "total_xp": 1250,
            "current_streak": 5
        },
        "profile": {
            "college": "MIT",
            "total_quizzes_attempted": 45,
            "average_score": 85.5
        }
    }
}
```

## Quiz Endpoints

### List Quizzes

**GET** `/quizzes/`

**Authentication**: Required

Query Parameters:
- `category` (optional): Filter by category ID
- `difficulty` (optional): easy, medium, hard
- `page` (optional): Page number (default: 1)

Response:
```json
{
    "success": true,
    "data": {
        "count": 100,
        "next": "/api/quizzes/?page=2",
        "previous": null,
        "results": [
            {
                "id": "uuid",
                "title": "Python Basics",
                "category": "Programming",
                "difficulty": "medium",
                "duration": 600,
                "total_questions": 10
            }
        ]
    }
}
```

### Start Quiz Attempt

**POST** `/quizzes/{quiz_id}/start/`

**Authentication**: Required

Response:
```json
{
    "success": true,
    "data": {
        "attempt_id": "uuid",
        "quiz": {
            "id": "uuid",
            "title": "Python Basics",
            "total_questions": 10,
            "duration": 600
        },
        "started_at": "2024-12-27T15:30:00Z",
        "expires_at": "2024-12-27T15:40:00Z"
    }
}
```

### Get Quiz Questions

**GET** `/quizzes/attempts/{attempt_id}/questions/`

**Authentication**: Required

Response:
```json
{
    "success": true,
    "data": {
        "questions": [
            {
                "id": "uuid",
                "text": "What is Python?",
                "question_type": "multiple_choice",
                "options": [
                    {"id": "a", "text": "A snake"},
                    {"id": "b", "text": "A programming language"},
                    {"id": "c", "text": "A framework"}
                ]
            }
        ]
    }
}
```

### Submit Quiz

**POST** `/quizzes/attempts/{attempt_id}/submit/`

**Authentication**: Required

Request:
```json
{
    "answers": [
        {
            "question_id": "uuid",
            "selected_option": "b"
        }
    ]
}
```

Response:
```json
{
    "success": true,
    "data": {
        "score": 85.5,
        "is_passed": true,
        "xp_earned": 50,
        "total_correct": 8,
        "total_questions": 10,
        "detailed_results": [
            {
                "question_id": "uuid",
                "is_correct": true,
                "user_answer": "b",
                "correct_answer": "b"
            }
        ]
    }
}
```

## Leaderboard Endpoints

### Get Overall Leaderboard

**GET** `/leaderboards/overall/`

**Authentication**: Optional

Query Parameters:
- `limit` (optional): Number of entries (default: 20, max: 100)

Response:
```json
{
    "success": true,
    "data": {
        "leaderboard": [
            {
                "rank": 1,
                "user": {
                    "id": "uuid",
                    "name": "John Doe",
                    "avatar_url": "/media/avatars/..."
                },
                "total_xp": 15000,
                "total_quizzes": 150,
                "average_score": 92.5
            }
        ],
        "current_user_rank": 45,
        "last_updated": "2024-12-27T15:30:00Z"
    }
}
```

### Get College Leaderboard

**GET** `/leaderboards/college/{college_id}/`

**Authentication**: Optional

Response: Similar to overall leaderboard

## Daily Quiz Endpoints

### List Daily Quizzes

**GET** `/daily-quizzes/`

**Authentication**: Required

Response:
```json
{
    "success": true,
    "data": {
        "daily_quizzes": [
            {
                "id": "uuid",
                "date": "2024-12-27",
                "quiz": {
                    "title": "Daily Challenge #1",
                    "difficulty": "medium"
                },
                "is_unlocked": true,
                "is_completed": false
            }
        ],
        "user_keys": 5,
        "keys_required": 10
    }
}
```

### Watch Ad for Keys

**POST** `/daily-quizzes/watch-ad/`

**Authentication**: Required

Request:
```json
{
    "ad_id": "uuid",
    "watch_duration": 35
}
```

Response:
```json
{
    "success": true,
    "data": {
        "keys_earned": 1,
        "total_keys": 6,
        "daily_ad_count": 15,
        "daily_ad_limit": 20
    }
}
```

## XP System Endpoints

### Get User XP Stats

**GET** `/xp/stats/`

**Authentication**: Required

Response:
```json
{
    "success": true,
    "data": {
        "total_xp": 1250,
        "current_streak": 5,
        "longest_streak": 12,
        "badges": [
            {
                "id": "uuid",
                "name": "Quiz Master",
                "description": "Completed 50 quizzes",
                "icon_url": "/media/badges/..."
            }
        ],
        "recent_xp_logs": [
            {
                "amount": 50,
                "reason": "Completed Python Basics quiz",
                "timestamp": "2024-12-27T15:30:00Z"
            }
        ]
    }
}
```

## Error Responses

All endpoints return errors in this format:

```json
{
    "success": false,
    "message": "Error description",
    "errors": {
        "field_name": ["Error detail"]
    }
}
```

### HTTP Status Codes

- `200 OK`: Success
- `201 Created`: Resource created
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Permission denied
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Rate Limiting

- **Anonymous users**: 100 requests/hour
- **Authenticated users**: 1000 requests/hour

Rate limit headers:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1609459200
```

## Pagination

List endpoints return paginated results:

```json
{
    "count": 100,
    "next": "/api/endpoint/?page=2",
    "previous": null,
    "results": [...]
}
```

## Filtering & Searching

Most list endpoints support:
- `search`: Full-text search
- `ordering`: Sort by field (use `-` for descending)
- Field-specific filters

Example:
```
GET /api/quizzes/?search=python&ordering=-created_at&difficulty=medium
```

---

**Note**: This is PROMPT 1 skeleton. Full API implementation in PROMPT 2+.
