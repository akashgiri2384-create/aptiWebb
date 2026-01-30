"""
Business logic services for XP system.

Services:
- XPService: XP awarding, level calculation, streak tracking
- BadgeService: Badge unlocking and management
"""

from django.db import transaction
from django.db.models import Sum, Count, Avg, F, Q
from django.utils import timezone
from datetime import timedelta, date
import logging
import math

from .models import XPLog, XPConfig, UserStats, Badge, UserBadge

logger = logging.getLogger('quizzy')


class XPService:
    """XP calculation and awarding service"""
    
    @staticmethod
    @transaction.atomic
    def award_xp(user, amount, description, quiz_attempt_id=None, metadata=None):
        """
        Award XP to user and log transaction.
        
        Args:
            user: CustomUser instance
            amount: XP amount to award
            description: Human-readable description
            quiz_attempt_id: Optional UUID of quiz attempt
            metadata: Optional dict of additional data
            
        Returns:
            tuple: (success, xp_log, error_message)
        """
        if amount <= 0:
            return False, None, "XP amount must be positive"
        
        try:
            # Get or create user stats
            user_stats, _ = UserStats.objects.get_or_create(user=user)
            
            # Calculate new totals
            old_xp = user_stats.total_xp
            new_xp = old_xp + amount
            
            # Update Season XP
            user_stats.season_xp = F('season_xp') + amount
            
            # Calculate level (using formula: level = floor(sqrt(xp / 100)))
            old_level = user_stats.level
            new_level = XPService.calculate_level(new_xp)
            
            # Create XP log
            xp_log = XPLog.objects.create(
                user=user,
                amount=amount,
                description=description,
                transaction_type='quiz' if quiz_attempt_id else 'other',
                balance_after=new_xp,
                quiz_attempt_id=quiz_attempt_id,
                metadata=metadata or {}
            )
            
            # Update user stats
            user_stats.total_xp = new_xp
            user_stats.level = new_level
            user_stats.save()
            # Refresh to get updated season_xp value from DB
            user_stats.refresh_from_db()
            
            # Update user profile
            try:
                user.profile.total_xp = new_xp
                user.profile.save(update_fields=['total_xp'])
            except:
                pass
            
            # Check for level up
            if new_level > old_level:
                logger.info(f"User {user.email} leveled up: {old_level} -> {new_level}")
                XPService.handle_level_up(user, old_level, new_level)
            
            # Check badge unlocks (Achievements)
            BadgeService.check_and_award_badges(user)
            
            # Check Rank Up (New System)
            BadgeService.check_rank_up(user, user_stats)
            
            logger.info(f"Awarded {amount} XP to {user.email}: {description}")
            
            return True, xp_log, None
        
        except Exception as e:
            logger.error(f"Error awarding XP to {user.email}: {str(e)}")
            return False, None, "Failed to award XP"
    
    @staticmethod
    def calculate_level(total_xp):
        """
        Calculate level based on total XP.
        
        Formula: level = floor(sqrt(xp / 100))
        
        Args:
            total_xp: Total XP amount
            
        Returns:
            int: Calculated level
        """
        if total_xp < 0:
            return 1
        
        level = int(math.floor(math.sqrt(total_xp / 100)))
        return max(1, level)  # Minimum level 1
    
    @staticmethod
    def xp_required_for_level(level):
        """
        Calculate total XP required to reach a level.
        
        Args:
            level: Target level
            
        Returns:
            int: Total XP required
        """
        return (level ** 2) * 100
    
    @staticmethod
    def xp_to_next_level(user):
        """
        Calculate XP required to reach next level.
        
        Args:
            user: CustomUser instance
            
        Returns:
            dict: Current level, progress info
        """
        try:
            stats = user.stats
        except:
            stats, _ = UserStats.objects.get_or_create(user=user)
        
        current_level = stats.level
        current_xp = stats.total_xp
        
        next_level = current_level + 1
        xp_for_next = XPService.xp_required_for_level(next_level)
        xp_for_current = XPService.xp_required_for_level(current_level)
        
        xp_needed = xp_for_next - current_xp
        xp_progress = current_xp - xp_for_current
        xp_level_range = xp_for_next - xp_for_current
        
        progress_percentage = (xp_progress / xp_level_range * 100) if xp_level_range > 0 else 0
        
        return {
            'current_level': current_level,
            'next_level': next_level,
            'current_xp': current_xp,
            'xp_for_next_level': xp_for_next,
            'xp_needed': xp_needed,
            'progress_percentage': round(progress_percentage, 2)
        }
    
    @staticmethod
    def handle_level_up(user, old_level, new_level):
        """
        Handle level up event - award bonus XP, badges, etc.
        
        Args:
            user: CustomUser instance
            old_level: Previous level
            new_level: New level
        """
        # Award level up bonus (10 XP per level)
        levels_gained = new_level - old_level
        bonus_xp = levels_gained * 10
        
        # Note: We don't award XP here to avoid recursion
        # Just log the event
        logger.info(f"Level up bonus would be {bonus_xp} XP for {user.email}")
        
        # Could trigger notification, dashboard event, etc.
        try:
            from dashboard.services import DashboardService
            DashboardService.log_activity(
                user,
                'level_up',
                f'Reached level {new_level}!',
                xp_change=0,
                metadata={'old_level': old_level, 'new_level': new_level}
            )
        except:
            pass
    
    @staticmethod
    def update_streak(user):
        """
        Update user's practice streak with new rules:
        1. Only DAILY QUIZZES count.
        2. Must complete 3 Daily Quizzes to increment/maintain.
        3. Admin Safeguard: If < 3 quizzes existed yesterday, streak continues.
        """
        try:
            stats, _ = UserStats.objects.get_or_create(user=user)
        except:
            return 0, False, None
        
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        # 1. Count Completed DAILY Quizzes for Today
        # We rely on DailyQuizUnlock tracking or QuizAttempt linked to DailyQuiz
        from daily_quizzes.models import DailyQuiz
        from quizzes.models import QuizAttempt
        
        # Find attempts for today's daily quizzes
        today_daily_quizzes = DailyQuiz.objects.filter(date=today, is_active=True)
        total_available = today_daily_quizzes.count()
        today_dq_quiz_ids = today_daily_quizzes.values_list('quiz_id', flat=True)
        
        # Rule: If NO daily quizzes exist for today, streak is safely paused (not broken, not incremented).
        if total_available == 0:
            return stats.current_streak, False, None

        completed_today_count = QuizAttempt.objects.filter(
            user=user,
            quiz_id__in=today_dq_quiz_ids, 
            status='graded', 
            submitted_at__date=today
        ).count()
        
        # Rule: Must complete ALL available daily quizzes
        if completed_today_count < total_available:
            # Haven't reached goal yet.
            # Streak matches yesterday's state (paused until completion)
            return stats.current_streak, False, None

        # Rule Met: All Quizzes Done Today.
        
        # Check integrity of previous streak
        last_active = stats.last_activity_date
        
        # If already updated today, ignore
        if last_active == today:
             return stats.current_streak, False, None
             
        # If first time ever
        if not last_active:
            stats.current_streak = 1
            stats.longest_streak = 1
            stats.last_activity_date = today
            stats.save()
            return 1, True, None

        # Calculate Gap
        delta = (today - last_active).days
        
        if delta == 1:
            # Perfect streak (Yesterday was active)
            stats.current_streak += 1
        else:
            # Missed days exists. Check if they are forgivable.
            streak_broken = False
            
            # Check every missed day
            check_date = last_active + timedelta(days=1)
            while check_date < today:
                # Check if there were quizzes on this day
                past_available = DailyQuiz.objects.filter(date=check_date, is_active=True).count()
                
                if past_available > 0:
                    # There were quizzes, and user missed them (since last_active < check_date)
                    streak_broken = True
                    break
                # If past_available == 0, we forgive this day (Admin didn't add quizzes)
                
                check_date += timedelta(days=1)
            
            if streak_broken:
                stats.current_streak = 1 # Reset
            else:
                stats.current_streak += 1 # Continued (Forgiven)

        # Update Longest
        if stats.current_streak > stats.longest_streak:
            stats.longest_streak = stats.current_streak
            
        stats.last_activity_date = today
        stats.save()
        
        # Check milestones
        milestone = XPService.check_streak_milestone(stats.current_streak)
        
        return stats.current_streak, True, milestone
    
    @staticmethod
    def check_streak_milestone(streak):
        """
        Check if streak hit milestone.
        
        Args:
            streak: Current streak count
            
        Returns:
            int or None: Milestone XP bonus
        """
        milestones = {
            3: 5,    # 3 days = 5 XP
            7: 15,   # 7 days = 15 XP
            14: 30,  # 14 days = 30 XP
            30: 100, # 30 days = 100 XP
            60: 250, # 60 days = 250 XP
            90: 500, # 90 days = 500 XP
        }
        
        return milestones.get(streak)
    
    @staticmethod
    def get_user_stats(user):
        """
        Get comprehensive user XP statistics.
        
        Args:
            user: CustomUser instance
            
        Returns:
            dict: User XP stats
        """
        try:
            stats = user.stats
        except:
            stats, _ = UserStats.objects.get_or_create(user=user)
        
        # Level progress
        level_info = XPService.xp_to_next_level(user)
        
        # XP earned in last 7 days
        week_ago = timezone.now() - timedelta(days=7)
        weekly_xp = XPLog.objects.filter(
            user=user,
            created_at__gte=week_ago
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Total XP logs
        total_transactions = XPLog.objects.filter(user=user).count()
        
        # Badges
        badges_earned = UserBadge.objects.filter(user=user).count()
        
        return {
            'total_xp': stats.total_xp,
            'level': stats.level,
            'level_progress': level_info,
            'streak': {
                'current': stats.current_streak,
                'longest': stats.longest_streak,
                'last_active': user.profile.last_practice_date.isoformat() if hasattr(user.profile, 'last_practice_date') and user.profile.last_practice_date else None,
            },
            'weekly_xp': weekly_xp,
            'total_transactions': total_transactions,
            'badges_earned': badges_earned,
        }


    @staticmethod
    def get_global_leaderboard(limit=10, user=None):
        """
        Get global leaderboard based on total XP.
        
        Args:
            limit: Number of users to return
            user: Current user (to check if they are in top N)
            
        Returns:
            list: Leaderboard entries
        """
        top_stats = UserStats.objects.select_related('user').order_by('-total_xp')[:limit]
        
        leaderboard = []
        for rank, stat in enumerate(top_stats, 1):
            leaderboard.append({
                'rank': rank,
                'user_id': str(stat.user.id),
                'name': stat.user.full_name,
                'xp': stat.total_xp,
                'level': stat.level,
                'is_current_user': (user and stat.user.id == user.id)
            })
            
        return leaderboard

    @staticmethod
    def get_college_leaderboard(college, limit=10, user=None):
        """
        Get college-specific leaderboard based on total XP.
        
        Args:
            college: College instance
            limit: Number of users to return
            user: Current user
            
        Returns:
            list: Leaderboard entries
        """
        if not college:
            return []
            
        top_stats = UserStats.objects.filter(
            user__college=college
        ).select_related('user').order_by('-total_xp')[:limit]
        
        leaderboard = []
        for rank, stat in enumerate(top_stats, 1):
            leaderboard.append({
                'rank': rank,
                'user_id': str(stat.user.id),
                'name': stat.user.full_name,
                'xp': stat.total_xp,
                'level': stat.level,
                'is_current_user': (user and stat.user.id == user.id)
            })
            
        return leaderboard


    @staticmethod
    def get_college_rankings(limit=10):
        """
        Get ranking of colleges based on total student XP.
        
        Args:
            limit: Number of colleges to return
            
        Returns:
            list: College leaderboard entries
        """
        from accounts.models import College
        from django.db.models import Sum
        
        # Aggregate XP per college
        colleges = College.objects.annotate(
            total_xp=Sum('students__xp_stats__total_xp')
        ).filter(total_xp__gt=0).order_by('-total_xp')[:limit]
        
        leaderboard = []
        for rank, college in enumerate(colleges, 1):
            leaderboard.append({
                'rank': rank,
                'id': str(college.id),
                'name': college.name,
                'xp': college.total_xp or 0,
                'student_count': college.students.count()
            })
            
        return leaderboard


class BadgeService:
    """Badge unlocking and management"""
    
    @staticmethod
    @transaction.atomic
    def check_and_award_badges(user):
        """
        Check all badge unlock conditions and award eligible badges.
        
        Args:
            user: CustomUser instance
            
        Returns:
            list: Newly awarded badges
        """
        newly_awarded = []
        
        # Get all badges (Explicitly exclude Ranks - they are handled by check_rank_up)
        badges = Badge.objects.filter(is_active=True).exclude(rarity='rank')
        
        # Get user's existing badges
        existing_badge_ids = set(
            UserBadge.objects.filter(user=user).values_list('badge_id', flat=True)
        )
        
        for badge in badges:
            # Skip if user already has this badge
            if badge.id in existing_badge_ids:
                continue
            
            # Check unlock condition
            if BadgeService.check_badge_condition(user, badge):
                # Award badge
                user_badge = UserBadge.objects.create(
                    user=user,
                    badge=badge
                )
                
                newly_awarded.append(badge)
                logger.info(f"Badge awarded to {user.email}: {badge.name}")
                
                # Log to dashboard
                try:
                    from dashboard.services import DashboardService
                    DashboardService.log_activity(
                        user,
                        'badge_unlocked',
                        f'Unlocked badge: {badge.name}',
                        badge_id=badge.id
                    )
                except:
                    pass
        
        return newly_awarded
    
    @staticmethod
    def check_badge_condition(user, badge):
        """
        Check if user meets badge unlock condition.
        
        Args:
            user: CustomUser instance
            badge: Badge instance
            
        Returns:
            bool: Whether condition is met
        """
        unlock_type = badge.unlock_type
        requirement = badge.unlock_requirement
        
        try:
            # Get user stats
            try:
                stats = user.xp_stats
                profile = user.profile
            except:
                return False
            
            # Quizzes Attempted
            if unlock_type == 'quizzes_attempted':
                count = requirement.get('count', 0)
                return profile.total_quizzes_attempted >= count
                
            # Quizzes Passed
            elif unlock_type == 'quizzes_passed':
                count = requirement.get('count', 0)
                return stats.quizzes_passed >= count
                
            # Accuracy (Single Quiz)
            elif unlock_type == 'accuracy_single':
                # This check is usually done right after a quiz
                # For generic check, we look for history
                from quizzes.models import QuizAttempt
                percentage = requirement.get('percentage', 100)
                return QuizAttempt.objects.filter(
                    user=user, 
                    percentage_score__gte=percentage
                ).exists()
            
            # Streak
            elif unlock_type == 'streak_days':
                days = requirement.get('days', 0)
                return stats.current_streak >= days
                
            # Time Range (Night Owl)
            elif unlock_type == 'time_range':
                # This requires context of "current action", 
                # but for general check, we might look at recent polls
                # For now, we return False during bulk check unless passed context
                # OR we check if ANY quiz was done in that range
                start = requirement.get('start', '00:00')
                end = requirement.get('end', '00:00')
                # Simplifying: check if last quiz was in range
                # Simplifying: check if last quiz was in range
                from quizzes.models import QuizAttempt
                last_quiz = QuizAttempt.objects.filter(user=user, status='graded').order_by('-submitted_at').first()
                if last_quiz and last_quiz.submitted_at:
                    t = last_quiz.submitted_at.time()
                    # Parse range (simple string comparison for "HH:MM")
                    s_h, s_m = map(int, start.split(':'))
                    e_h, e_m = map(int, end.split(':'))
                    
                    # Convert to comparable integers (minutes from midnight)
                    req_start = s_h * 60 + s_m
                    req_end = e_h * 60 + e_m
                    quiz_time = t.hour * 60 + t.minute
                    
                    if req_start > req_end: # Crosses midnight (e.g. 22:00 to 04:00)
                        return quiz_time >= req_start or quiz_time <= req_end
                    else:
                        return req_start <= quiz_time <= req_end
                
                return False

            # XP Thresholds
            elif unlock_type == 'total_xp':
                amount = requirement.get('amount', 0)
                return stats.total_xp >= amount
                
            else:
                return False
        
        except Exception as e:
            logger.error(f"Error checking badge condition for {user.email}: {str(e)}")
            return False
    
    @staticmethod
    def get_user_badges(user):
        """
        Get all badges earned by user.
        
        Args:
            user: CustomUser instance
            
        Returns:
            list: User badges with details
        """
        user_badges = UserBadge.objects.filter(user=user).select_related('badge')
        
        return [
            {
                'badge': {
                    'id': str(ub.badge.id),
                    'name': ub.badge.name,
                    'description': ub.badge.description,
                    'icon': ub.badge.emoji or '🏅', # Use emoji as icon fallback
                    'image_path': ub.badge.image_path,
                    'rarity': ub.badge.rarity,
                    'xp_bonus': ub.badge.xp_reward,
                    'xp_threshold': ub.badge.xp_threshold,
                },
                'earned_at': ub.unlocked_at.isoformat(),
            }
            for ub in user_badges
        ]
    
    @staticmethod
    def check_rank_up(user, user_stats):
        """
        Check for rank upgrades based on Season XP.
        Awards all skipped ranks and triggers notification for the highest one.
        
        Args:
            user: CustomUser instance
            user_stats: UserStats instance
        """
        # Get all eligible rank badges
        eligible_badges = Badge.objects.filter(
            rarity='rank',
            xp_threshold__lte=user_stats.season_xp,
            is_active=True
        ).order_by('rank_order')
        
        if not eligible_badges.exists():
            return
            
        # Get existing rank badges
        existing_badges_qs = UserBadge.objects.filter(
            user=user, 
            badge__rarity='rank'
        ).select_related('badge')
        
        existing_badge_ids = set(existing_badges_qs.values_list('badge_id', flat=True))
        
        # Determine previous highest rank (for "Major" upgrade check)
        previous_highest_rank = None
        if existing_badges_qs.exists():
            # Assuming 'rank_order' implies hierarchy
            previous_highest_rank = max(
                [ub.badge for ub in existing_badges_qs], 
                key=lambda b: b.rank_order
            )

        # Identify new badges
        new_badges = []
        for badge in eligible_badges:
            if badge.id not in existing_badge_ids:
                new_badges.append(badge)
        
        if not new_badges:
            return
            
        # Award new badges
        try:
            # Create UserBadge records
            UserBadge.objects.bulk_create([
                UserBadge(user=user, badge=badge) for badge in new_badges
            ])
            
            # Find highest rank among new ones for notification (default behavior)
            highest_new_rank = max(new_badges, key=lambda b: b.rank_order)
            
            logger.info(f"User {user.email} ranked up to {highest_new_rank.name} (Rank {highest_new_rank.rank_order})")
            
            # --- ABSOLUTE FINAL LOGIC (USER REQUESTED) ---
            # Direct Mapping: Badge Name -> Video File
            # Only keys present here will trigger animation.
            # This implicitly handles the "Only Rank I" rule because we only list "Bronze I", "Silver I", etc.
            
            BADGE_VIDEO_MAP = {
                'Bronze I': '1_bronze-1.mp4',
                'Silver I': '6_silver-1.mp4',
                'Emberlaure I': '11_Emberlaure-11.mp4',
                'Tome I': '16_Tome-1.mp4',
                'Eternal I': '21_eternal-1.mp4',
                'Arcane I': '26_Arcane-1.mp4',
                'Mystic I': '31_Mystic-1.mp4',
                'Verdant I': '36_Verdant-1.mp4',
                'Frostheart I': '41_Frostheart-1.mp4',
                'Crystal I': '46_Crystal-1.mp4', 
                'Infernos I': '51_Infernos-1.mp4',
                "Inferno's I": '51_Infernos-1.mp4', # Handle potential name variance
                'Stellar I': '56_Stellar-1.mp4',
                'Crown I': '61_Crown-1.mp4',
                'Lunar I': '66_Lunar-1.mp4',
                'Galactic I': '71_Galactic-1.mp4',
                'Grandmaster I': '76_Grandmaster-1.mp4',
                'Grandmaster V': '80_Grandmaster_5 -.mp4' # Special completion video
            }
            
            target_badge = None
            video_filename = None
            
            # Check if any new badge matches our map
            for badge in new_badges:
                if badge.name in BADGE_VIDEO_MAP:
                    # Found a Major Rank!
                    # If multiple (batch unlock), prefer the higher rank (though logic usually processes widely spaced ranks)
                    if target_badge is None or badge.rank_order > target_badge.rank_order:
                        target_badge = badge
                        video_filename = BADGE_VIDEO_MAP[badge.name]

            is_major_rank_up = False
            video_path_desktop = None
            video_path_mobile = None
            tier_name = ""
            
            if video_filename:
                is_major_rank_up = True
                video_path_desktop = f'/static/videos/desktop_laptop/{video_filename}'
                video_path_mobile = f'/static/videos/mobile/{video_filename}'
                
                # Extract simple name "Bronze" from "Bronze I"
                tier_name = target_badge.name.split(' ')[0].upper()
                if "INFERNO" in tier_name: tier_name = "INFERNOS"
                
                logger.info(f"ANIMATION TRIGGER: Badge={target_badge.name} -> {video_filename}")

            # Fallback for the very first badge if Logic misses (e.g. badge name typo in DB)
            # Check if User had 0 badges before, and now has badges.
            if previous_highest_rank is None and not is_major_rank_up and new_badges:
                 # Check if lowest rank badge is Bronze I
                 lowest_new = min(new_badges, key=lambda b: b.rank_order)
                 if lowest_new.rank_order == 1:
                     is_major_rank_up = True
                     video_path_desktop = '/static/videos/desktop_laptop/1_bronze-1.mp4'
                     video_path_mobile = '/static/videos/mobile/1_bronze-1.mp4'
                     tier_name = "BRONZE"
                     target_badge = lowest_new
                     logger.info("First Rank Fallback Triggered via Rank 1 check")

            # Log the Activity
            from dashboard.services import DashboardService
            
            # Use the triggering badge for ID if possible, else highest
            log_badge = target_badge if target_badge else max(new_badges, key=lambda b: b.rank_order)
            
            DashboardService.log_activity(
                user,
                'rank_change',
                f'Promoted to {log_badge.name}!',
                badge_id=log_badge.id,
                metadata={
                    'badge_id': str(log_badge.id),  # CRITICAL: Frontend needs this for unique cache keys
                    'rank_order': log_badge.rank_order,
                    'image_path': log_badge.image_path,
                    'name': log_badge.name,
                    'rank_up': True, # General flag
                    'major_rank_up': is_major_rank_up, # Animation Trigger
                    'video_path': video_path_desktop,     
                    'video_path_mobile': video_path_mobile,
                    'tier_name': tier_name or "RANK UP"
                }

            )
                
        except Exception as e:
            logger.error(f"Error awarding rank badges to {user.email}: {e}")
            import traceback
            logger.error(traceback.format_exc())
