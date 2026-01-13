"""
Core views for error pages and general pages.
"""

from django.shortcuts import render


def error_404(request, exception=None):
    """Custom 404 error page."""
    return render(request, 'errors/404.html', status=404)


def error_500(request):
    """Custom 500 error page."""
    return render(request, 'errors/500.html', status=500)


def home(request):
    """Homepage (redirect to dashboard if logged in)."""
    if request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect('dashboard:home')
    return render(request, 'core/home.html')


def terms(request):
    """Terms of service page."""
    return render(request, 'terms/terms.html')


def privacy(request):
    """Privacy policy page."""
    return render(request, 'terms/privacy.html')


def disclaimer(request):
    """Disclaimer page."""
    return render(request, 'terms/disclaimer.html')
