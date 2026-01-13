import csv
import io
from datetime import timedelta
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.template.loader import get_template
from xhtml2pdf import pisa
from quizzes.models import QuizAttempt
from .analytics import calculate_trends, calculate_student_flags, categorize_topics, generate_recommendations

@login_required
@require_GET
def download_student_report(request):
    """
    Download Student Report as PDF or CSV.
    Query params: 
    - type: 'weekly' (default) or 'monthly'
    - format: 'pdf' (default) or 'csv'
    """
    report_type = request.GET.get('type', 'weekly')
    fmt = request.GET.get('format', 'pdf')
    
    days = 30 if report_type == 'monthly' else 7
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Fetch Data
    results = QuizAttempt.objects.filter(
        user=request.user,
        submitted_at__range=(start_date, end_date),
        status='graded'
    ).order_by('-submitted_at')
    
    # Calculate Stats
    total_quizzes = results.count()
    if total_quizzes > 0:
        avg_score = sum(r.percentage_score for r in results) / total_quizzes
    else:
        avg_score = 0
        
    trend_data = calculate_trends(request.user, days)
    flags = calculate_student_flags(request.user, days)
    
    # Enhanced Analytics
    topic_analysis = categorize_topics(request.user, days)
    recommendations = generate_recommendations(request.user, days, flags, topic_analysis)

    # Skill Analysis (Aggregate by Category - Keep existing for compatibility or rely on new topic_analysis)
    # Using existing logic for now but sorting safely
    skills = []
    category_stats = {}
    for r in results:
        cat = r.quiz.category.name if r.quiz.category else "General"
        if cat not in category_stats:
            category_stats[cat] = {'total': 0, 'count': 0}
        category_stats[cat]['total'] += r.percentage_score
        category_stats[cat]['count'] += 1
    
    for cat, stats in category_stats.items():
        skills.append({
            'name': cat,
            'score': round(stats['total'] / stats['count'], 1)
        })
    skills.sort(key=lambda x: x['score'], reverse=True)

    # Badges 
    from xp_system.models import UserBadge
    earned_badges = UserBadge.objects.filter(
        user=request.user,
        unlocked_at__range=(start_date, end_date)
    ).select_related('badge')

    context = {
        'user': request.user,
        'profile': request.user.profile,
        'report_type': report_type.title(),
        'start_date': start_date,
        'end_date': end_date,
        'results': results[:15], 
        'stats': {
            'total_quizzes': total_quizzes,
            'avg_score': round(avg_score, 1),
            'trend': trend_data,
            'flags': flags
        },
        'skills': skills[:5], 
        'badges': earned_badges,
        'topic_analysis': topic_analysis, # New
        'recommendations': recommendations # New
    }

    if fmt == 'csv':
        return generate_csv(results, report_type)
    else:
        return generate_pdf('reports/student_report_card.html', context)

def generate_csv(results, report_type):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="student_report_{report_type}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Quiz Title', 'Score', 'Accuracy %', 'XP Earned', 'Status'])

    for r in results:
        writer.writerow([
            r.submitted_at.strftime('%Y-%m-%d %H:%M'),
            r.quiz.title,
            r.correct_count, # raw score
            f"{r.percentage_score}%",
            r.xp_earned,
            'Passed' if r.is_passed else 'Failed'
        ])

    return response

def generate_pdf(template_src, context_dict):
    template = get_template(template_src)
    html  = template.render(context_dict)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="report_card.pdf"'
    
    pisa_status = pisa.CreatePDF(
       html, dest=response
    )
    
    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response
