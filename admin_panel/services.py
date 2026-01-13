"""
Business logic services for admin_panel app.
"""

from django.db import transaction
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta
import csv
import io
import logging

from .models import AdminUser, FeatureToggle, AuditLog, QuizTemplate
from accounts.models import CustomUser
from quizzes.models import Quiz, Question, Category

logger = logging.getLogger('quizzy')


class AdminService:
    """Admin panel business logic"""
    
    @staticmethod
    @transaction.atomic
    def approve_user(admin_user, user_id, notes=None):
        """
        Approve a pending user.
        
        Args:
            admin_user: AdminUser instance
            user_id: UUID of user to approve
            notes: Optional approval notes
            
        Returns:
            tuple: (success, message)
        """
        try:
            user = CustomUser.objects.get(id=user_id)
            
            if user.is_active:
                return False, "User is already active"
            
            user.is_active = True
            user.save(update_fields=['is_active'])
            
            # Log action
            AuditLog.objects.create(
                admin_user=admin_user,
                action='approve_user',
                target_model='CustomUser',
                target_id=str(user.id),
                description=f"Approved user: {user.email}",
                metadata={'notes': notes}
            )
            
            logger.info(f"Admin {admin_user.user.email} approved user {user.email}")
            
            return True, f"User {user.email} approved successfully"
        
        except CustomUser.DoesNotExist:
            return False, "User not found"
        except Exception as e:
            logger.error(f"Error approving user: {str(e)}")
            return False, "Failed to approve user"
    
    @staticmethod
    @transaction.atomic
    def ban_user(admin_user, user_id, reason, duration_days=None):
        """
        Ban a user.
        
        Args:
            admin_user: AdminUser instance
            user_id: UUID of user
            reason: Ban reason
            duration_days: Optional duration (None = permanent)
            
        Returns:
            tuple: (success, message)
        """
        try:
            user = CustomUser.objects.get(id=user_id)
            
            if user.is_banned:
                return False, "User is already banned"
            
            user.is_banned = True
            user.ban_reason = reason
            
            if duration_days:
                user.ban_expires_at = timezone.now() + timedelta(days=duration_days)
            
            user.save()
            
            # Log action
            AuditLog.objects.create(
                admin_user=admin_user,
                action='ban_user',
                target_model='CustomUser',
                target_id=str(user.id),
                description=f"Banned user: {user.email}",
                metadata={'reason': reason, 'duration_days': duration_days}
            )
            
            logger.info(f"Admin {admin_user.user.email} banned user {user.email}")
            
            return True, f"User {user.email} banned successfully"
        
        except CustomUser.DoesNotExist:
            return False, "User not found"
        except Exception as e:
            logger.error(f"Error banning user: {str(e)}")
            return False, "Failed to ban user"
    
    @staticmethod
    @transaction.atomic
    def grant_xp(admin_user, user_id, amount, description):
        """
        Manually grant XP to a user.
        
        Args:
            admin_user: AdminUser instance
            user_id: UUID of user
            amount: XP amount
            description: Reason
            
        Returns:
            tuple: (success, message)
        """
        try:
            user = CustomUser.objects.get(id=user_id)
            
            # Award XP
            from xp_system.services import XPService
            success, xp_log, error = XPService.award_xp(
                user=user,
                amount=amount,
                description=f"Admin grant: {description}"
            )
            
            if not success:
                return False, error
            
            # Log action
            AuditLog.objects.create(
                admin_user=admin_user,
                action='grant_xp',
                target_model='CustomUser',
                target_id=str(user.id),
                description=f"Granted {amount} XP to {user.email}",
                metadata={'amount': amount, 'reason': description}
            )
            
            logger.info(f"Admin {admin_user.user.email} granted {amount} XP to {user.email}")
            
            return True, f"Granted {amount} XP to {user.email}"
        
        except CustomUser.DoesNotExist:
            return False, "User not found"
        except Exception as e:
            logger.error(f"Error granting XP: {str(e)}")
            return False, "Failed to grant XP"
    
    @staticmethod
    @transaction.atomic
    def import_quizzes_csv(admin_user, csv_file, category_id):
        """
        Import quizzes from CSV file.
        
        CSV Format:
        title,description,difficulty,duration_minutes,passing_percentage
        
        Args:
            admin_user: AdminUser instance
            csv_file: Uploaded CSV file
            category_id: UUID of category
            
        Returns:
            tuple: (success, imported_count, errors)
        """
        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            return False, 0, ["Category not found"]
        
        errors = []
        imported_count = 0
        
        try:
            # Read CSV
            csv_content = csv_file.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            
            for row_num, row in enumerate(csv_reader, start=2):
                try:
                    # Validate required fields
                    if not row.get('title'):
                        errors.append(f"Row {row_num}: Title is required")
                        continue
                    
                    # Create quiz
                    quiz = Quiz.objects.create(
                        title=row['title'].strip(),
                        description=row.get('description', '').strip(),
                        category=category,
                        difficulty=row.get('difficulty', 'medium').lower(),
                        duration_minutes=int(row.get('duration_minutes', 30)),
                        passing_percentage=int(row.get('passing_percentage', 60)),
                        is_published=False  # Keep unpublished until reviewed
                    )
                    
                    imported_count += 1
                
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
            
            # Log action
            AuditLog.objects.create(
                admin_user=admin_user,
                action='import_quizzes',
                target_model='Quiz',
                description=f"Imported {imported_count} quizzes from CSV",
                metadata={'category': category.name, 'errors_count': len(errors)}
            )
            
            logger.info(f"Admin {admin_user.user.email} imported {imported_count} quizzes")
            
            return True, imported_count, errors
        
        except Exception as e:
            logger.error(f"Error importing CSV: {str(e)}")
            return False, 0, [str(e)]
    
    @staticmethod
    def get_dashboard_stats():
        """
        Get admin dashboard statistics.
        
        Returns:
            dict: Dashboard stats
        """
        from quizzes.models import QuizAttempt
        from xp_system.models import UserStats
        
        # User stats
        total_users = CustomUser.objects.count()
        active_users = CustomUser.objects.filter(is_active=True).count()
        banned_users = CustomUser.objects.filter(is_banned=True).count()
        
        # Quiz stats
        total_quizzes = Quiz.objects.count()
        published_quizzes = Quiz.objects.filter(is_published=True).count()
        total_attempts = QuizAttempt.objects.count()
        
        # Recent activity (last 7 days)
        week_ago = timezone.now() - timedelta(days=7)
        new_users_week = CustomUser.objects.filter(created_at__gte=week_ago).count()
        attempts_week = QuizAttempt.objects.filter(started_at__gte=week_ago).count()
        
        # Top users by XP
        top_users = UserStats.objects.select_related('user').order_by('-total_xp')[:5]
        
        return {
            'users': {
                'total': total_users,
                'active': active_users,
                'banned': banned_users,
                'new_this_week': new_users_week,
            },
            'quizzes': {
                'total': total_quizzes,
                'published': published_quizzes,
                'attempts_total': total_attempts,
                'attempts_this_week': attempts_week,
            },
            'top_users': [
                {
                    'name': stats.user.full_name,
                    'email': stats.user.email,
                    'xp': stats.total_xp,
                    'level': stats.level,
                }
                for stats in top_users
            ]
        }
