"""
Business logic services for leaderboards app.

Services:
- LeaderboardService: Calculate and manage rankings
"""

from django.db.models import Sum, Count, Avg, F, Q, Max
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta
import logging

from .models import LeaderboardEntry, RankSnapshot
from accounts.models import CustomUser

logger = logging.getLogger('quizzy')


class LeaderboardService:
    """Leaderboard calculation and ranking service"""
    
    CACHE_TTL = 300  # 5 minutes
    
    @staticmethod
    def calculate_overall_leaderboard(scope='all_time', period=None, limit=100):
        """
        Calculate overall leaderboard based on XP.
        """
        cache_key = f'leaderboard:overall:{scope}:{period}'
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        from xp_system.models import UserStats
        
        # Optimize query - populate profile to avoid N+1
        users = UserStats.objects.select_related('user', 'user__college', 'user__profile').all()
        
        # Order by total XP
        users = users.order_by('-total_xp')[:limit]
        
        leaderboard = []
        for rank, user_stats in enumerate(users, start=1):
            user = user_stats.user
            
            # Safe profile access
            try:
                profile = user.profile
                quizzes_completed = profile.total_quizzes_attempted
                accuracy = round(profile.accuracy_percentage, 2)
            except:
                quizzes_completed = 0
                accuracy = 0.0

            leaderboard.append({
                'rank': rank,
                'user': {
                    'id': str(user.id),
                    'name': user.full_name,
                    'college': user.college.name if user.college else None,
                    'avatar': getattr(profile, 'avatar', None),
                },
                'xp': user_stats.total_xp,
                'level': user_stats.level,
                'quizzes_completed': quizzes_completed,
                'accuracy': accuracy,
            })
        
        cache.set(cache_key, leaderboard, LeaderboardService.CACHE_TTL)
        return leaderboard
    
    @staticmethod
    def calculate_quiz_leaderboard(quiz_id, limit=50):
        """
        Calculate leaderboard for a specific quiz.
        """
        from quizzes.models import QuizAttempt
        
        cache_key = f'leaderboard:quiz:{quiz_id}'
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        # Get best attempts per user
        all_attempts = QuizAttempt.objects.filter(
            quiz_id=quiz_id,
            status='graded'
        ).select_related('user', 'user__college').order_by(
            '-percentage_score',
            'duration_seconds'
        )
        
        # Manual deduplication for SQLite compatibility
        top_attempts = []
        seen_users = set()
        
        for attempt in all_attempts:
            if attempt.user_id in seen_users:
                continue
                
            seen_users.add(attempt.user_id)
            top_attempts.append(attempt)
            
            if len(top_attempts) >= limit:
                break
        
        leaderboard = []
        for rank, attempt in enumerate(top_attempts, start=1):
            leaderboard.append({
                'rank': rank,
                'user': {
                    'id': str(attempt.user.id),
                    'name': attempt.user.full_name,
                    'college': attempt.user.college.name if attempt.user.college else None,
                },
                'score': attempt.percentage_score,
                'time': attempt.duration_seconds,
                'xp_earned': attempt.xp_earned,
                'attempted_at': attempt.submitted_at.isoformat() if attempt.submitted_at else None,
            })
        
        cache.set(cache_key, leaderboard, LeaderboardService.CACHE_TTL)
        return leaderboard
    
    @staticmethod
    def calculate_college_leaderboard(limit=50):
        """
        Calculate college-wise leaderboard.
        """
        from accounts.models import College
        
        cache_key = 'leaderboard:colleges'
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        # Aggregate XP by college
        # Correctly use 'students' and 'xp_stats' related names
        colleges = College.objects.filter(is_active=True).annotate(
            total_xp=Sum('students__xp_stats__total_xp'),
            total_users=Count('students', distinct=True),
            avg_xp=Avg('students__xp_stats__total_xp')
        ).filter(
            total_users__gt=0,
            total_xp__isnull=False
        ).order_by('-total_xp')[:limit]
        
        leaderboard = []
        for rank, college in enumerate(colleges, start=1):
            leaderboard.append({
                'rank': rank,
                'college': {
                    'id': str(college.id),
                    'name': college.name,
                    'city': college.city,
                    'state': college.state,
                },
                'total_xp': college.total_xp or 0,
                'total_users': college.total_users,
                'average_xp': round(college.avg_xp or 0, 2),
            })
        
        cache.set(cache_key, leaderboard, LeaderboardService.CACHE_TTL)
        return leaderboard
    
    @staticmethod
    def get_user_position(user, scope='all_time'):
        """
        Get user's position in leaderboard.
        """
        try:
            # Correct related name
            user_stats = user.xp_stats
        except:
            return {
                'rank': None,
                'total_users': 0,
                'percentile': 0,
                'nearby_users': []
            }
        
        # Count users with more XP
        from xp_system.models import UserStats
        
        users_above = UserStats.objects.filter(
            total_xp__gt=user_stats.total_xp
        ).count()
        
        rank = users_above + 1
        total_users = UserStats.objects.count()
        percentile = ((total_users - rank) / total_users * 100) if total_users > 0 else 0
        
        # Get nearby users (3 above, 3 below)
        nearby_above = UserStats.objects.filter(
            total_xp__gt=user_stats.total_xp
        ).select_related('user').order_by('total_xp')[:3]
        
        nearby_below = UserStats.objects.filter(
            total_xp__lt=user_stats.total_xp
        ).select_related('user').order_by('-total_xp')[:3]
        
        nearby_users = []
        
        # Add users above
        for stats in reversed(list(nearby_above)):
            nearby_users.append({
                'name': stats.user.full_name,
                'xp': stats.total_xp,
                'level': stats.level,
            })
        
        # Add current user
        nearby_users.append({
            'name': user.full_name,
            'xp': user_stats.total_xp,
            'level': user_stats.level,
            'is_current_user': True,
        })
        
        # Add users below
        for stats in nearby_below:
            nearby_users.append({
                'name': stats.user.full_name,
                'xp': stats.total_xp,
                'level': stats.level,
            })
        
        return {
            'rank': rank,
            'total_users': total_users,
            'percentile': round(percentile, 2),
            'nearby_users': nearby_users,
        }
    
    @staticmethod
    def invalidate_leaderboard_cache():
        """Invalidate all leaderboard caches"""
        cache_keys = [
            'leaderboard:overall:all_time:None',
            'leaderboard:colleges',
        ]
        
        for key in cache_keys:
            cache.delete(key)
