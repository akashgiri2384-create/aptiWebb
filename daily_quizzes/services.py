"""
Business logic services for daily_quizzes app.
"""

from django.db import transaction
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta, date
import logging

from .models import DailyQuiz, DailyQuizUnlock, KeyLedger, AdView, RewardedVideoAd

logger = logging.getLogger('quizzy')


class DailyQuizService:
    """Daily quiz and key management"""
    
    @staticmethod
    def get_today_quizzes():
        """
        Get today's daily quizzes.
        
        Returns:
            QuerySet: Active DailyQuiz instances
        """
        # Use local date (e.g., IST) instead of UTC date
        today = timezone.localtime(timezone.now()).date()
        return DailyQuiz.objects.filter(date=today, is_active=True).select_related('quiz')
    
    @staticmethod
    def check_unlock_status(user, daily_quiz):
        """
        Check if user has unlocked specific daily quiz.
        
        Args:
            user: CustomUser instance
            daily_quiz: DailyQuiz instance
            
        Returns:
            tuple: (is_unlocked, unlock_record)
        """
        try:
            unlock = DailyQuizUnlock.objects.get(
                user=user,
                daily_quiz=daily_quiz
            )
            return unlock.is_unlocked, unlock
        except DailyQuizUnlock.DoesNotExist:
            return False, None
    
    @staticmethod
    @transaction.atomic
    def unlock_with_keys(user, daily_quiz_id, keys_to_spend=None):
        """
        Unlock daily quiz using keys.
        
        Args:
            user: CustomUser instance
            daily_quiz_id: UUID of DailyQuiz
            keys_to_spend: Optional (uses quiz requirement if None)
            
        Returns:
            tuple: (success, message)
        """
        try:
            daily_quiz = DailyQuiz.objects.get(id=daily_quiz_id)
        except DailyQuiz.DoesNotExist:
            return False, "Daily quiz not found"

        # Check if already unlocked
        is_unlocked, unlock_record = DailyQuizService.check_unlock_status(user, daily_quiz)
        
        if is_unlocked:
            return False, "Quiz already unlocked"
        
        # Check required keys
        required = keys_to_spend if keys_to_spend else daily_quiz.keys_required
        
        # Check available local keys (Shards)
        keys_have = unlock_record.keys_earned if unlock_record else 0
        
        if keys_have < required:
            # Optional: Fallback to global keys?
            # For now, strictly enforce local keys as per user request
            return False, f"Insufficient keys. You have {keys_have}/{required} for this quiz."
        
        # Unlock logic
        # We don't "spend" local keys, we just verify they are enough to unlock.
        # Or do we reset them? Usually 'unlock' consumes them conceptually, but record stays.
        
        if unlock_record:
            unlock_record.is_unlocked = True
            unlock_record.unlocked_at = timezone.now()
            unlock_record.unlock_method = 'keys'
            # keys_earned remains as record of work done
            unlock_record.save()
        else:
             # If no record but keys_required is 0 (or less, for safety), create it now
            if required <= 0:
                DailyQuizUnlock.objects.create(
                    user=user,
                    daily_quiz=daily_quiz,
                    keys_required=0,
                    keys_earned=0,
                    is_unlocked=True,
                    unlocked_at=timezone.now()
                )
            else:
                # Debugging info included to help identify "impossible" states
                return False, f"Error: No key progress found (req={required})"
        
        logger.info(f"User {user.email} unlocked daily quiz {daily_quiz.id} with {keys_have} local keys")
        
        return True, "Quiz unlocked successfully"
    
    @staticmethod
    @transaction.atomic
    def watch_ad_for_key(user, daily_quiz_id=None):
        """
        Process ad view and award key.
        
        Args:
            user: CustomUser instance
            daily_quiz_id: UUID of daily quiz (optional)
            
        Returns:
            tuple: (success, message, keys_earned)
        """
        from django.conf import settings
        
        # Rate Limit: Check if user watched an ad in the last 30 seconds
        cutoff = timezone.now() - timedelta(seconds=30)
        if AdView.objects.filter(user=user, created_at__gte=cutoff).exists():
            return False, "Please wait a moment before claiming another reward.", 0

        # Create ad view record
        # Note: 'ad' is optional now
        ad_view = AdView.objects.create(
            user=user,
            status='completed',
            daily_quiz_id=daily_quiz_id # Link to quiz if possible
        )
        
        keys_count = settings.QUIZZY_SETTINGS.get('KEYS_PER_AD', 1)
        
        # Scenario A: Specific Daily Quiz (Local Progress)
        if daily_quiz_id:
            try:
                dq = DailyQuiz.objects.get(id=daily_quiz_id)
                unlock, created = DailyQuizUnlock.objects.get_or_create(
                    user=user,
                    daily_quiz=dq,
                    defaults={'keys_required': dq.keys_required}
                )
                
                unlock.keys_earned += keys_count
                
                # Auto-unlock if enough keys?
                # User asked: "after collecting make sure i am able to attend"
                # If we auto-unlock, the "Unlock Now" button is skipped.
                # Let's keep manual unlock for satisfaction, OR auto-unlock if seamless.
                # Let's NOT auto-unlock yet, just accumulate.
                
                unlock.save()
                
                # Log to ledger for audit
                KeyLedger.objects.create(
                    user=user,
                    transaction_type='earned_ad',
                    amount=keys_count,
                    balance_after=0, # Not tracking global balance here effectively
                    description=f"Earned shard for quiz {dq.date}",
                    ad_view=ad_view,
                    unlock=unlock
                )
                
                logger.info(f"User {user.email} earned local key for quiz {daily_quiz_id}")
                return True, f"Collected a Key! ({unlock.keys_earned}/{unlock.keys_required})", keys_count
                
            except DailyQuiz.DoesNotExist:
                pass # Fallback to global
        
        # Scenario B: Global Key (Fallback)
        KeyService.earn_keys(
            user=user,
            amount=keys_count,
            description="Watched rewarded video ad",
            ad_view=ad_view
        )
        
        logger.info(f"User {user.email} earned {keys_count} global keys from ad")
        
        return True, f"Earned {keys_count} key(s)!", keys_count


class KeyService:
    """Key ledger management"""
    
    @staticmethod
    def get_available_keys(user):
        """
        Calculate available keys for user.
        
        Args:
            user: CustomUser instance
            
        Returns:
            int: Available keys
        """
        earned = KeyLedger.objects.filter(
            user=user,
            transaction_type='earned'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        spent = KeyLedger.objects.filter(
            user=user,
            transaction_type='used'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        return earned - spent
    
    @staticmethod
    @transaction.atomic
    def earn_keys(user, amount, description, ad_view=None):
        """
        Award keys to user.
        
        Args:
            user: CustomUser instance
            amount: Number of keys to award
            description: Description
            ad_view: Optional AdView instance
            
        Returns:
            KeyLedger instance
        """
        balance = KeyService.get_available_keys(user)
        new_balance = balance + amount
        
        key_log = KeyLedger.objects.create(
            user=user,
            transaction_type='earned',
            amount=amount,
            balance_after=new_balance,
            description=description,
            ad_view=ad_view
        )
        
        # Update user profile
        try:
            user.profile.total_keys = new_balance
            user.profile.save(update_fields=['total_keys'])
        except:
            pass
            
        # Invalidate dashboard cache
        try:
            from django.core.cache import cache
            cache.delete(f'dashboard_stats_{user.id}')
        except:
            pass
        
        return key_log
    
    @staticmethod
    @transaction.atomic
    def spend_keys(user, amount, description, daily_quiz=None):
        """
        Spend user's keys.
        
        Args:
            user: CustomUser instance
            amount: Number of keys to spend
            description: Description
            daily_quiz: Optional DailyQuiz instance
            
        Returns:
            KeyLedger instance
        """
        balance = KeyService.get_available_keys(user)
        
        if balance < amount:
            raise ValueError(f"Insufficient keys. Available: {balance}, Required: {amount}")
        
        new_balance = balance - amount
        
        key_log = KeyLedger.objects.create(
            user=user,
            transaction_type='used',
            amount=amount,
            balance_after=new_balance,
            description=description,
            daily_quiz_id=daily_quiz.id if daily_quiz else None
        )
        
        # Update user profile
        try:
            user.profile.total_keys = new_balance
            user.profile.save(update_fields=['total_keys'])
        except:
            pass
            
        # Invalidate dashboard cache
        try:
            from django.core.cache import cache
            cache.delete(f'dashboard_stats_{user.id}')
        except:
            pass
        
        return key_log
