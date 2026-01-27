""" Quizzy URL Configuration
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from core.frontend_views import (
    login_page, register_page, quiz_list_page, home_page,
    take_quiz_page, quiz_result_page, leaderboard_page, profile_page
)
from core.views_debug import debug_email_view
from core.views import cleanup_logs_view
from accounts import views as account_views

urlpatterns = [
    # Frontend pages
    path('', home_page, name='home'),
    path('login/', login_page, name='login'),
    path('register/', register_page, name='register'),
    # Password Reset Web View (Matched to Email Link)
    path('accounts/reset-password/<str:token>/', account_views.password_reset_confirm, name='password-reset-confirm-web'),
    
    path('quizzes/', quiz_list_page, name='quizzes'),
    path('quiz/<uuid:attempt_id>/', take_quiz_page, name='take-quiz'),
    path('quiz/<uuid:attempt_id>/result/', quiz_result_page, name='quiz-result'),
    path('leaderboard/', leaderboard_page, name='leaderboard'),
    path('profile/', profile_page, name='profile'),
    path('dashboard/', quiz_list_page, name='dashboard'),  # For now, same as quiz list
    path('test-apis/', lambda request: render(request, 'test_apis.html'), name='test-apis'),
    path('debug-email/', debug_email_view, name='debug-email'),
    path('system/cleanup/', cleanup_logs_view, name='cleanup_logs'),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/accounts/', include('accounts.urls')),
    path('api/quizzes/', include('quizzes.urls')),
    path('api/daily-quizzes/', include('daily_quizzes.urls')),
    path('api/leaderboards/', include('leaderboards.urls')),
    path('api/xp/', include('xp_system.urls')),
    path('api/analytics/', include('analytics.urls')),
    path('api/admin-panel/', include('admin_panel.urls')),
    path('api/dashboard/', include('dashboard.urls')),
    path('api/reports/', include('reports.urls')),
]

# Error handlers
handler404 = 'core.views.error_404'
handler500 = 'core.views.error_500'

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Customize admin site
admin.site.site_header = "Quizzy Administration"
admin.site.site_title = "Quizzy Admin"
admin.site.index_title = "Welcome to Quizzy Admin Portal"
