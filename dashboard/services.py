"""
Business logic services for dashboard app.

Services:
- DashboardService: Statistics calculation and activity logging
- MetricsService: Daily metrics aggregation
"""

from django.db.models import Count, Sum, Avg, Q, F
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta, date
import logging

from .models import UserActivityLog, DailyActivityMetric

logger = logging.getLogger('quizzy')


class DashboardService:
    """Core dashboard calculations and statistics."""
    
    CACHE_TTL = 600  # 10 minutes
    
    @staticmethod
    def get_user_stats(user, use_cache=True):
        """
        Get comprehensive user statistics.
        
        Args:
            user: CustomUser instance
            use_cache: Whether to use cached results
            
        Returns:
            dict: User statistics
        """
        cache_key = f'dashboard_stats_{user.id}'
        
        if use_cache:
            cached =cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for dashboard stats: {user.email}")
                return cached
        
        try:
            profile = user.profile
        except:
            # If profile doesn't exist, create it
            from accounts.models import UserProfile
            profile = UserProfile.objects.create(user=user)
        
        # Calculate current keys
        current_keys = DashboardService.get_current_keys(user)
        
        # Calculate weekly XP
        week_ago = timezone.now() - timedelta(days=7)
        weekly_xp = DashboardService._get_weekly_xp(user, week_ago)
        
        # Get days active
        days_active = DashboardService.get_days_active(user)
        
        # Get weekly rank
        weekly_rank = DashboardService.get_weekly_rank(user)
        
        # Calculate current rank dynamically (failsafe)
        current_rank = profile.current_rank
        if not current_rank:
            try:
                from xp_system.models import UserStats
                user_xp = profile.total_xp
                # Rank = count of users with more XP + 1
                rank = UserStats.objects.filter(total_xp__gt=user_xp).count() + 1
                current_rank = rank
                
                # Update profile
                profile.current_rank = rank
                profile.save(update_fields=['current_rank'])
            except Exception as e:
                logger.warning(f"Failed to calculate rank for {user.email}: {e}")
                current_rank = 'N/A'

        stats = {
            'total_xp': profile.total_xp,
            'full_name': user.full_name,
            'weekly_xp_change': f"+{weekly_xp}" if weekly_xp > 0 else str(weekly_xp),
            'quizzes_attempted': profile.total_quizzes_attempted,
            'days_active': days_active,
            'accuracy_percentage': round(profile.accuracy_percentage, 2),
            'available_keys': current_keys,
            'current_rank': current_rank,
            'weekly_rank': weekly_rank,
            'practice_streak': profile.practice_streak,
            'avatar': profile.avatar if profile.avatar else None,
        }
        
        if use_cache:
            cache.set(cache_key, stats, DashboardService.CACHE_TTL)
        
        # Check for recent major rank up (not cached to ensure freshness)
        try:
            from .models import UserActivityLog
            # 15 minute window
            recent_time = timezone.now() - timedelta(minutes=15)
            rank_activity = UserActivityLog.objects.filter(
                user=user,
                activity_type='rank_change',
                created_at__gte=recent_time
            ).order_by('-created_at').first()
            
            if rank_activity:
                # If major rank up detected
                if rank_activity.metadata.get('major_rank_up'):
                    stats['recent_rank_up'] = rank_activity.metadata
                else:
                    logger.debug(f"Profile: Minor rank up ignored for {user.email}")
        except Exception as e:
            logger.error(f"Error checking profile rank up: {e}")

        logger.info(f"Dashboard stats calculated for: {user.email}")
        return stats
    
    @staticmethod
    def _get_weekly_xp(user, week_ago):
        """Calculate XP earned in last 7 days."""
        try:
            from xp_system.models import XPLog
            weekly_xp = XPLog.objects.filter(
                user=user,
                created_at__gte=week_ago
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            return weekly_xp
        except:
            # XP system not yet implemented
            return 0
    
    @staticmethod
    def get_current_keys(user):
        """
        Calculate current available keys.
        
        Args:
            user: CustomUser instance
            
        Returns:
            int: Number of available keys
        """
        try:
            from daily_quizzes.models import KeyLedger
            
            earned = KeyLedger.objects.filter(
                user=user,
                transaction_type='earned'
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            
            used = KeyLedger.objects.filter(
                user=user,
                transaction_type='used'
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            
            return earned - used
        except:
            # Daily quizzes not yet implemented
            return 0
    
    @staticmethod
    def get_days_active(user):
        """
        Count unique days user has been active.
        
        Args:
            user: CustomUser instance
            
        Returns:
            int: Number of active days
        """
        return DailyActivityMetric.objects.filter(user=user).count()
    
    @staticmethod
    def get_weekly_rank(user):
        """
        Get user's rank in weekly leaderboard.
        
        Args:
            user: CustomUser instance
            
        Returns:
            int or str: Rank number or 'N/A'
        """
        try:
            from leaderboards.models import LeaderboardEntry
            
            entry = LeaderboardEntry.objects.filter(
                user=user,
                scope='overall',
                period=timezone.now().date() - timedelta(days=timezone.now().weekday())
            ).first()
            
            return entry.rank if entry else 'N/A'
        except:
            # Leaderboards not yet implemented
            return 'N/A'
    
    @staticmethod
    def get_recent_activities(user, limit=10):
        """
        Get recent user activities.
        
        Args:
            user: CustomUser instance
            limit: Maximum number of activities to return
            
        Returns:
            list: Activity dictionaries
        """
        activities = UserActivityLog.objects.filter(user=user)[:limit]
        
        return [
            {
                'id': str(activity.id),
                'type': activity.activity_type,
                'description': activity.description,
                'xp_change': activity.xp_change,
                'key_change': activity.key_change,
                'timestamp': activity.created_at.isoformat(),
                'relative_time': DashboardService._get_relative_time(activity.created_at),
            }
            for activity in activities
        ]
    
    @staticmethod
    def _get_relative_time(timestamp):
        """Convert timestamp to relative time string."""
        now = timezone.now()
        diff = now - timestamp
        
        if diff.total_seconds() < 60:
            return 'Just now'
        elif diff.total_seconds() < 3600:
            minutes = int(diff.total_seconds() / 60)
            return f'{minutes} minute{"s" if minutes > 1 else ""} ago'
        elif diff.total_seconds() < 86400:
            hours = int(diff.total_seconds() / 3600)
            return f'{hours} hour{"s" if hours > 1 else ""} ago'
        elif diff.days < 7:
            return f'{diff.days} day{"s" if diff.days > 1 else ""} ago'
        else:
            return timestamp.strftime('%b %d, %Y')
    
    @staticmethod
    def get_weekly_stats(user):
        """
        Get aggregated weekly statistics.
        
        Args:
            user: CustomUser instance
            
        Returns:
            dict: Weekly statistics
        """
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        daily_metrics = DailyActivityMetric.objects.filter(
            user=user,
            date__gte=week_ago,
            date__lte=today
        )
        
        aggregates = daily_metrics.aggregate(
            total_quizzes=Sum('quizzes_attempted'),
            total_xp=Sum('xp_earned'),
            total_keys=Sum('keys_earned'),
            avg_accuracy=Avg('accuracy_percentage'),
            total_time=Sum('total_time_minutes'),
        )
        
        return {
            'quizzes_completed': aggregates['total_quizzes'] or 0,
            'total_xp_earned': aggregates['total_xp'] or 0,
            'total_keys_earned': aggregates['total_keys'] or 0,
            'average_accuracy': round(aggregates['avg_accuracy'] or 0.0, 2),
            'days_active': daily_metrics.count(),
            'total_time_minutes': aggregates['total_time'] or 0,
        }
    
    @staticmethod
    def get_accuracy_trend(user, days=30):
        """
        Get daily accuracy trend for chart.
        
        Args:
            user: CustomUser instance
            days: Number of days to include
            
        Returns:
            list: Daily accuracy data points
        """
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        metrics = DailyActivityMetric.objects.filter(
            user=user,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
        
        return [
            {
                'date': metric.date.isoformat(),
                'accuracy': round(metric.accuracy_percentage, 2),
                'quizzes': metric.quizzes_attempted,
            }
            for metric in metrics
        ]
    
    @staticmethod
    def log_activity(user, activity_type, description, **kwargs):
        """
        Log user activity.
        
        Args:
            user: CustomUser instance
            activity_type: Type of activity from ACTIVITY_TYPES
            description: Human-readable description
            **kwargs: Additional optional fields
            
        Returns:
            UserActivityLog instance
        """
        activity = UserActivityLog.objects.create(
            user=user,
            activity_type=activity_type,
            description=description,
            quiz_id=kwargs.get('quiz_id'),
            xp_change=kwargs.get('xp_change', 0),
            key_change=kwargs.get('key_change', 0),
            rank_change=kwargs.get('rank_change'),
            badge_id=kwargs.get('badge_id'),
            metadata=kwargs.get('metadata', {}),
        )
        
        # Invalidate cache
        cache_key = f'dashboard_stats_{user.id}'
        cache.delete(cache_key)
        
        logger.info(f"Activity logged: {user.email} - {activity_type}")
        return activity
    
    @staticmethod
    def invalidate_cache(user):
        """Invalidate dashboard cache for user."""
        cache_key = f'dashboard_stats_{user.id}'
        cache.delete(cache_key)


class MetricsService:
    """Daily metrics aggregation service."""
    
    @staticmethod
    def update_daily_metric(user, date=None, **updates):
        """
        Update or create daily metric.
        
        Args:
            user: CustomUser instance
            date: Date for metric (default: today)
            **updates: Fields to update
            
        Returns:
            DailyActivityMetric instance
        """
        if date is None:
            date = timezone.now().date()
        
        metric, created = DailyActivityMetric.objects.update_or_create(
            user=user,
            date=date,
            defaults=updates
        )
        
        if created:
            logger.info(f"Daily metric created: {user.email} - {date}")
        else:
            logger.info(f"Daily metric updated: {user.email} - {date}")
        
        # Invalidate dashboard cache
        DashboardService.invalidate_cache(user)
        
        return metric
    
    @staticmethod
    def increment_metric(user, field, amount=1, date=None):
        """
        Increment a metric field.
        
        Args:
            user: CustomUser instance
            field: Field name to increment
            amount: Amount to increment by
            date: Date for metric (default: today)
        """
        if date is None:
            date = timezone.now().date()
        
        metric, created = DailyActivityMetric.objects.get_or_create(
            user=user,
            date=date,
            defaults={field: amount}
        )
        
        if not created:
            current_value = getattr(metric, field, 0)
            setattr(metric, field, current_value + amount)
            metric.save()
        
        return metric
    
    @staticmethod
    def aggregate_today_metrics(user):
        """
        Aggregate today's metrics from activity logs.
        
        This is typically called by a Celery task at end of day.
        
        Args:
            user: CustomUser instance
            
        Returns:
            DailyActivityMetric instance
        """
        today = timezone.now().date()
        
        # Get today's activities
        activities = UserActivityLog.objects.filter(
            user=user,
            created_at__date=today
        )
        
        # Calculate metrics
        quiz_count = activities.filter(
            activity_type='quiz_complete'
        ).count()
        
        xp_earned = activities.filter(
            activity_type='xp_earned'
        ).aggregate(Sum('xp_change'))['xp_change__sum'] or 0
        
        keys_earned = activities.filter(
            activity_type='key_earned'
        ).aggregate(Sum('key_change'))['key_change__sum'] or 0
        
        keys_used = activities.filter(
            activity_type='key_used'
        ).aggregate(Sum('key_change'))['key_change__sum'] or 0
        
        badges_earned = activities.filter(
            activity_type='badge_unlocked'
        ).count()
        
        # Update metric
        metric = MetricsService.update_daily_metric(
            user=user,
            date=today,
            quizzes_attempted=quiz_count,
            xp_earned=abs(xp_earned),
            keys_earned=abs(keys_earned),
            keys_used=abs(keys_used),
            badges_earned=badges_earned,
        )
        
        logger.info(f"Aggregated today's metrics for: {user.email}")
        return metric
