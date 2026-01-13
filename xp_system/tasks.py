from celery import shared_task
from django.core.management import call_command
import logging

logger = logging.getLogger('quizzy')

@shared_task
def reset_monthly_ranks():
    """
    Celery task to reset monthly ranks.
    """
    logger.info("Starting monthly rank reset task...")
    try:
        call_command('reset_monthly_ranks')
        logger.info("Monthly rank reset task completed successfully.")
        return "Reset successful"
    except Exception as e:
        logger.error(f"Monthly rank reset task failed: {e}")
        return f"Reset failed: {e}"
