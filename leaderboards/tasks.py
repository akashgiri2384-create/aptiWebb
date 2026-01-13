"""
Celery tasks for leaderboards app.

PLACEHOLDER - Full implementation in PROMPT 6 specification.

Tasks:
1. update_quiz_leaderboards - Every 5 minutes
2. update_overall_leaderboard - Every 5 minutes  
3. update_college_leaderboard - Every hour
4. snapshot_leaderboards - Daily at midnight

Each task:
- Calls corresponding LeaderboardService method
- Invalidates relevant cache keys
- Logs completion/errors
"""

from celery import shared_task
from django.core.cache import cache
import logging

logger = logging.getLogger('quizzy')


@shared_task(bind=True)
def update_quiz_leaderboards(self):
    """Update all quiz leaderboards every 5 minutes"""
    try:
        from .services import LeaderboardService
        LeaderboardService.calculate_quiz_leaderboards()
        # Invalidate caches - full implementation in PROMPT
        return "Quiz leaderboards updated"
    except Exception as e:
        logger.error(f"Error updating quiz leaderboards: {str(e)}")
        raise


@shared_task(bind=True)
def update_overall_leaderboard(self):
    """Update overall student ranking every 5 minutes"""
    try:
        from .services import LeaderboardService
        LeaderboardService.calculate_overall_leaderboards()
        cache.delete("leaderboard:overall:all_time")
        cache.delete("leaderboard:overall:weekly")
        return "Overall leaderboards updated"
    except Exception as e:
        logger.error(f"Error updating overall leaderboard: {str(e)}")
        raise


@shared_task(bind=True)
def update_college_leaderboard(self):
    """Update college ranking hourly"""
    try:
        from .services import LeaderboardService
        LeaderboardService.calculate_college_leaderboards()
        cache.delete("leaderboard:college:all_time")
        return "College leaderboards updated"
    except Exception as e:
        logger.error(f"Error updating college leaderboard: {str(e)}")
        raise


@shared_task(bind=True)
def snapshot_leaderboards(self):
    """Create daily snapshots at midnight"""
    try:
        from .services import LeaderboardService
        LeaderboardService.snapshot_leaderboards()
        return "Leaderboard snapshots created"
    except Exception as e:
        logger.error(f"Error creating snapshots: {str(e)}")
        raise
