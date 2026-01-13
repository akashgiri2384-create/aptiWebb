import csv
import io
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string
from django.db.models import Avg
from django.contrib.auth import get_user_model
from decouple import config
from quizzes.models import QuizAttempt
from .analytics import calculate_student_flags, categorize_topics, explain_flags, generate_recommendations

User = get_user_model()

def send_college_report(subscription):
    """
    Generates and sends the weekly/monthly report for a given subscription.
    Uses dedicated REPORT_EMAIL credentials if configured.
    Returns: (success: bool, message: str)
    """
    try:
        # Determine Date Range
        days = 30 if subscription.frequency == 'monthly' else 7
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # 1. Fetch Students
        students = User.objects.filter(college=subscription.college)
        if not students.exists():
            return False, f"No students found for {subscription.college.name}"

        # 2. Gather Data for CSV & Email Body
        student_data = [] # For CSV
        active_students_count = 0
        total_tests_taken = 0
        at_risk_count = 0
        total_accuracy_sum = 0
        accuracy_count = 0
        
        for student in students:
            # Get recent results
            recent_results = QuizAttempt.objects.filter(
                user=student,
                submitted_at__range=(start_date, end_date),
                status='graded'
            )
            
            quizzes_taken = recent_results.count()
            avg_acc = recent_results.aggregate(Avg('percentage_score'))['percentage_score__avg'] or 0
            
            flags = calculate_student_flags(student, days)
            topic_analysis = categorize_topics(student, days)
            risk_reason = explain_flags(flags, avg_acc, quizzes_taken)
            recommendations = generate_recommendations(student, days, flags, topic_analysis)
            
            if quizzes_taken > 0:
                active_students_count += 1
                total_tests_taken += quizzes_taken
                total_accuracy_sum += avg_acc
                accuracy_count += 1
                
            if 'At-Risk' in flags:
                at_risk_count += 1
            
            # Determine Improvements Needed (Weakest Category)
            improvements = "General Practice"
            if topic_analysis['weak']:
                 improvements = f"Focus: {', '.join(topic_analysis['weak'][:2])}"
            elif avg_acc > 0 and avg_acc < 50:
                improvements = "Concept Clarity"
            elif avg_acc >= 50 and avg_acc < 70:
                improvements = "Speed & Accuracy"
            elif avg_acc >= 70:
                improvements = "Advanced Topics"

            student_data.append({
                'roll_no': student.roll_number or "N/A",
                'name': student.full_name,
                'email': student.email,
                'year': student.year,
                'branch': student.branch,
                'tests': quizzes_taken,
                'accuracy': round(avg_acc, 1),
                'improvements': improvements, 
                'flags': ", ".join(flags),
                'strong_topics': ", ".join(topic_analysis['strong']),
                'weak_topics': ", ".join(topic_analysis['weak']),
                'risk_reason': risk_reason,
                'recommendation': " ".join(recommendations)
            })

        # Calculate Class Average
        class_avg = round(total_accuracy_sum / accuracy_count, 1) if accuracy_count > 0 else 0

        # 3. Generate CSVs (Split by Branch)
        attachments = []
        
        # Group by Branch
        branches = {}
        for row in student_data:
            branch_name = row['branch'] if row['branch'] else "Unknown Branch"
            if branch_name not in branches:
                branches[branch_name] = []
            branches[branch_name].append(row)
            
        # Create CSV for each branch
        for branch_name, students_in_branch in branches.items():
            csv_file = io.StringIO()
            writer = csv.writer(csv_file)
            # Enhanced Headers
            writer.writerow(['Roll No', 'Name', 'Email', 'Branch', 'Year', 'Tests Taken', 'Avg Accuracy', 
                             'Improvements Needed', 'Activity Flag', 'Strong Topics', 'Weak Topics', 'Context/Reason', 'Recommended Action'])
            
            for row in students_in_branch:
                writer.writerow([
                    row['roll_no'], 
                    row['name'], 
                    row['email'], 
                    row['branch'], 
                    row['year'], 
                    row['tests'], 
                    f"{row['accuracy']}%", 
                    row['improvements'], 
                    row['flags'],
                    row['strong_topics'],
                    row['weak_topics'],
                    row['risk_reason'],
                    row['recommendation']
                ])
            
            # Sanitize filename
            safe_branch = "".join(c for c in branch_name if c.isalnum() or c in (' ', '-', '_')).strip()
            filename = f"Report_{safe_branch}_{end_date.strftime('%Y%m%d')}.csv"
            attachments.append((filename, csv_file.getvalue(), 'text/csv'))
        
        # 4. Prepare Email Context
        # Sort by Tests Taken (Desc) then Accuracy (Desc)
        top_performers = sorted(
            [s for s in student_data if s['tests'] > 0], 
            key=lambda x: (x['tests'], x['accuracy']), 
            reverse=True
        )[:3]

        context = {
            'college_name': subscription.college.name,
            'start_date': start_date,
            'end_date': end_date,
            'stats': {
                'active_students': active_students_count,
                'avg_accuracy': class_avg,
                'total_tests': total_tests_taken,
                'at_risk_count': at_risk_count
            },
            'top_performers': top_performers
        }

        # 5. Render Email Body
        html_content = render_to_string('reports/email/college_report.html', context)
        text_content = f"Here is the report for {subscription.college.name}. Active Users: {active_students_count}. Avg Accuracy: {class_avg}%."

        # 6. Configure Dedicated Email Connection
        # Use Default Backend (Brevo)
        # Anymail handles connection pooling automatically
        
        # 7. Send Email
        email = EmailMultiAlternatives(
            subject=f"Weekly Branch Reports - {subscription.college.name}",
            body=text_content,
            from_email=settings.REPORT_FROM_EMAIL, # <--- Changed this
            to=[subscription.recipient_email],
            # connection=connection # Removed custom connection
        )
        email.attach_alternative(html_content, "text/html")
        
        # Attach all branch files
        for filename, content, mimetype in attachments:
            email.attach(filename, content, mimetype)
        
        email.send()
        
        # Update last sent
        subscription.last_sent_at = timezone.now()
        subscription.save()

        return True, f"Sent to {subscription.recipient_email} from {settings.REPORT_FROM_EMAIL}"
        
    except Exception as e:
        return False, str(e)
