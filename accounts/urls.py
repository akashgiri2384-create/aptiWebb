"""
URL routing for accounts app.
"""

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('register/', views.register, name='register'),
    path('verify-email/', views.verify_email, name='verify-email'), # Old post-reg (keep for safety or remove? Keep)
    path('initiate-verification/', views.initiate_verification, name='init-verify'),
    path('check-status/', views.check_verification_status, name='check-status'),
    path('confirm-email/', views.confirm_email, name='confirm-email'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    
    # OTP Password Reset
    path('send-otp/', views.SendOTPView.as_view(), name='send-otp'),
    path('verify-otp/', views.VerifyOTPView.as_view(), name='verify-otp'),
    path('reset-password/', views.ResetPasswordView.as_view(), name='reset-password'),

    # Link-Based Password Reset
    path('password-reset/request/', views.request_password_reset_link, name='request-password-reset-link'),
    path('reset-password/<str:token>/', views.password_reset_confirm, name='password-reset-confirm'),
    
    # Profile
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.update_profile, name='update-profile'),
    
    # Password
    path('change-password/', views.change_password, name='change-password'),
    
    # Colleges
    path('colleges/', views.colleges_list, name='colleges-list'),
    
    # Sessions
    path('sessions/', views.sessions, name='sessions'),
]
