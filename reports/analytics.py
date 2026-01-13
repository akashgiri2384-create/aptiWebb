from datetime import timedelta
from django.utils import timezone
from django.db.models import Avg, Count
from accounts.models import UserProfile
from quizzes.models import QuizAttempt
from xp_system.models import UserStats

def calculate_student_flags(user, days=7):
    """
    Analyze student performance over the last `days` and return a list of flags.
    Flags: 'At-Risk', 'Star Performer', 'Consistent', 'Placement Ready', 'Getting Started'
    """
    flags = []
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)

    # Fetch recent results
    recent_results = QuizAttempt.objects.filter(
        user=user, 
        submitted_at__range=(start_date, end_date),
        status='graded'
    )
    
    quizzes_taken = recent_results.count()
    
    # Check Inactivity / New User
    if quizzes_taken == 0:
        # If logged in recently but no quiz
        if user.last_login and user.last_login > start_date:
            flags.append('Exploring') # Active but no quizzes
        elif user.date_joined > start_date:
            flags.append('Getting Started')
        else:
             # Only mark inactive if really no interaction
            flags.append('Needs Practice')
        return flags 

    # Calculate average accuracy
    avg_accuracy = recent_results.aggregate(Avg('percentage_score'))['percentage_score__avg'] or 0
    
    # 1. At-Risk Logic (Lowered threshold)
    if avg_accuracy < 35:
        flags.append('At-Risk')
    
    # 2. Star Performer Logic
    if avg_accuracy > 80 and quizzes_taken >= 3:
        flags.append('Star Performer')

    # 3. Consistency
    if quizzes_taken >= 5:
        flags.append('Consistent')

    # 4. Placement Ready (Longer term check - total stats)
    try:
        profile = user.profile
        if profile.total_quizzes_attempted > 20 and profile.accuracy_percentage > 75:
             flags.append('Placement Ready')
    except:
        pass

    # Default for active users without specific flags
    if not flags:
        flags.append('Active Learner')

    return flags

def calculate_trends(user, days=7):
    """
    Compare current period vs previous period to determine trends.
    Returns dict with 'accuracy_change' and 'trend_label'.
    """
    now = timezone.now()
    current_start = now - timedelta(days=days)
    previous_start = current_start - timedelta(days=days)

    # Current Period
    current_avg = QuizAttempt.objects.filter(
        user=user,
        submitted_at__range=(current_start, now),
        status='graded'
    ).aggregate(Avg('percentage_score'))['percentage_score__avg'] or 0

    # Previous Period
    previous_avg = QuizAttempt.objects.filter(
        user=user,
        submitted_at__range=(previous_start, current_start),
        status='graded'
    ).aggregate(Avg('percentage_score'))['percentage_score__avg'] or 0

    if previous_avg == 0:
        return {
            'accuracy_change': 0,
            'trend_label': 'New'
        }

    change = current_avg - previous_avg
    
    if change > 5:
        label = '📈 Improving'
    elif change < -5:
        label = '⚠️ Declining'
    else:
        label = '➡️ Stable'

    return {
        'accuracy_change': round(change, 1),
        'trend_label': label
    }

def categorize_topics(user, days=30):
    """
    Analyze performance by quiz category/topic.
    Returns: {
        'strong':List[str], 
        'average':List[str], 
        'weak':List[str], 
        'details': Dict[str, float]
    }
    """
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    attempts = QuizAttempt.objects.filter(
        user=user, 
        submitted_at__range=(start_date, end_date),
        status='graded'
    ).select_related('quiz', 'quiz__category')
    
    if not attempts.exists():
        return {'strong': [], 'average': [], 'weak': [], 'details': {}}
        
    # Aggregate by Category
    cat_stats = {}
    for attempt in attempts:
        # Use Category Name or 'General'
        cat_name = attempt.quiz.category.name if attempt.quiz.category else "General Aptitude"
        
        if cat_name not in cat_stats:
            cat_stats[cat_name] = {'total_score': 0, 'count': 0}
            
        cat_stats[cat_name]['total_score'] += attempt.percentage_score
        cat_stats[cat_name]['count'] += 1
        
    # Classify
    analysis = {'strong': [], 'average': [], 'weak': [], 'details': {}}
    
    for cat, data in cat_stats.items():
        avg = data['total_score'] / data['count']
        analysis['details'][cat] = round(avg, 1)
        
        if avg >= 75:
            analysis['strong'].append(cat)
        elif avg >= 40:
            analysis['average'].append(cat)
        else:
            analysis['weak'].append(cat)
            
    return analysis

def explain_flags(flags, avg_accuracy, quizzes_taken):
    """
    Provide human-readable reasons for specific flags.
    """
    reasons = []
    
    if 'At-Risk' in flags:
        reasons.append(f"Avg accuracy ({round(avg_accuracy)}%) is below the safety threshold of 35%.")
    
    if 'Needs Practice' in flags:
        reasons.append("No quizzes attempted in the reporting period.")
        
    if 'Star Performer' in flags:
        reasons.append("Maintained High accuracy (>80%) with consistent participation.")
        
    if 'Consistent' in flags:
        reasons.append(f"Showed good dedication with {quizzes_taken} attempts.")
        
    return " | ".join(reasons)

def generate_recommendations(user, days=30, flags=None, topic_analysis=None):
    """
    Generate actionable advice based on performance.
    """
    if flags is None:
        flags = []
    if topic_analysis is None:
        topic_analysis = categorize_topics(user, days)
        
    recs = []
    
    # 1. Topic-Based Recommendations
    if topic_analysis['weak']:
        top_weak = topic_analysis['weak'][:2]
        recs.append(f"Prioritize revising concepts in: {', '.join(top_weak)}.")
    
    # 2. Strength-Based
    if topic_analysis['strong'] and not topic_analysis['weak']:
        recs.append("Great command on core topics! Try 'Hard' difficulty quizzes to push your limits.")
        
    # 3. Activity-Based
    if 'Needs Practice' in flags:
        recs.append("Start with 1 'Daily Quiz' to build a habit.")
    elif 'Consistent' not in flags and 'Star Performer' not in flags:
        recs.append("Try to attempt at least 3 quizzes this week to build consistency.")
        
    # 4. General fallback
    if not recs:
        recs.append("Maintain your current pace and explore new categories.")
        
    return recs
