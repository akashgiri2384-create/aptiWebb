from django.urls import path
from . import views

urlpatterns = [
    path('download/', views.download_student_report, name='download_report'),
]
