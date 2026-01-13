# Indira Quiz (IQ) Platform - Complete Developer Guide

## 1. Project Overview
**Indira Quiz (IQ)** is a premium, gamified aptitude testing platform designed for students. It features a robust quiz engine, an 80-tier rank system with monthly resets, detailed analytics, and a modern "Glassmorphism" UI.

### Key Features
*   **Authentication**: JWT-based (Access/Refresh), OTP Login, Email Verification.
*   **Quiz Engine**: Timed quizzes, multiple-choice questions, auto-grading, time-based bonuses.
*   **Gamification**:
    *   **XP System**: Geometric progression logic.
    *   **Badges**: 80 Rank Tiers + Achievement Badges.
    *   **Streaks**: Daily practice tracking.
    *   **Monthly Resets**: Automated resets of Season XP and Ranks.
*   **UI/UX**: Responsive Premium Dark Theme, Konva/CSS animations, specific mobile optimisations.

---

## 2. Tech Stack

### Backend
*   **Framework**: Django 4.2 LTS (Django REST Framework)
*   **Database**: SQLite (Dev) / PostgreSQL (Prod ready)
*   **Caching**: Redis (for Leaderboards, Session storage)
*   **Async Tasks**: Celery + Celery Beat (Redis Broker)
*   **Logging**: Custom logging configuration (`logs/app.log`)

### Frontend
*   **Templates**: Django Templates (server-side rendering)
*   **Styling**: Vanilla CSS (Variables, Flexbox/Grid) + `design-system.css`
*   **Scripting**: Vanilla JavaScript (ES6+)

---

## 3. Setup & Installation

### Prerequisites
*   Python 3.10+
*   Redis (Required for Celery)
*   PostgreSQL (Optional for Dev, Recommended for Prod)

### Initial Setup
1.  **Clone the repository**:
    ```bash
    git clone <repository_url>
    cd aptiWeb
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv myenv
    myenv\Scripts\activate  # Windows
    # source myenv/bin/activate  # Mac/Linux
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Environment Variables**:
    Create a `.env` file in the root directory:
    ```ini
    DEBUG=True
    SECRET_KEY=your-secret-key
    ALLOWED_HOSTS=localhost,127.0.0.1
    # Redis
    CELERY_BROKER_URL=redis://localhost:6379/0
    CELERY_RESULT_BACKEND=redis://localhost:6379/1
    ```

5.  **Database & Admin**:
    ```bash
    python manage.py migrate
    python manage.py createsuperuser
    ```

6.  **Seed Data**:
    ```bash
    python manage.py seed_ranks  # Essential for Badge System
    python manage.py setup_periodic_tasks # Essential for Automation
    ```

---

## 4. Running the Project

To run the full system, you need **three** separate terminal processes running simultaneously:

### Terminal 1: Django Web Server
Serves the website and API.
```bash
python manage.py runserver
```

### Terminal 2: Celery Worker
Processes background tasks (sending emails, awarding heavy XP).
```bash
# Windows (requires gevent or solo pool)
celery -A quizzy worker --pool=solo -l info

# Linux/Mac
celery -A quizzy worker -l info
```

### Terminal 3: Celery Beat
Schedules periodic tasks (Monthly Reset).
```bash
celery -A quizzy beat -l info
```

---

## 5. Key Workflows & Commands

### 🌟 Badge System Testing
You can cheat to test the "Rank Up" animation:
1.  Run `python manage.py shell`
2.  Execute:
    ```python
    from django.contrib.auth import get_user_model
    from xp_system.services import XPService
    user = get_user_model().objects.get(email='your_email@example.com')
    XPService.award_xp(user, 1500, "Testing", None)
    ```
3.  Refresh your Profile or Quiz Result page.

### 🔄 Monthly Reset (Automation)
The system is configured to automatically reset **Season XP** and **Rank Badges** on the **1st of every month at 00:00 UTC**.
*   **Command**: `reset_monthly_ranks`
*   **Task**: `xp_system.tasks.reset_monthly_ranks`
*   **Manual Trigger**: `python manage.py reset_monthly_ranks`

### 📊 Leaderboards
Leaderboards are cached in Redis for performance (TTL: 5 mins).
*   **Global**: `/api/leaderboard/global/`
*   **College**: `/api/leaderboard/college_rankings/`

---

## 6. Directory Structure
```
aptiWeb/
├── accounts/           # User models, Auth, Profile
├── core/              # Frontend views (Home, Privacy, Pages)
├── dashboard/         # User Dashboard, Activity Logging
├── quizzes/           # Quiz Engine (Models, Logic)
├── xp_system/         # XP, Badges, Ranks Services
├── templates/         # HTML Files
│   ├── accounts/      # Login, Profile
│   ├── quizzes/       # List, Take, Result
│   └── components/    # Navbar, Footer
├── static/
│   ├── css/          # design-system.css, rank-up.css
│   └── images/       # Badges, Logos
└── quizzy/           # Project Settings (settings.py, urls.py)
```

## 7. Troubleshooting

*   **Error: `ModuleNotFoundError: No module named 'django_celery_beat'`**
    *   Fix: Run `pip install django-celery-beat` and add it to `INSTALLED_APPS`.
*   **Error: Animation not showing**
    *   Fix: Ensure `python manage.py seed_ranks` was run. Check browser console for JS errors.
*   **Redis Connection Error**
    *   Fix: Ensure Redis server is running (`redis-cli ping` should return `PONG`).

---

**Built with ❤️ by the IQ Team**
