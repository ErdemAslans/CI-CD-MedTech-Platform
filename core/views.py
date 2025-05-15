# core/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def home(request):
    """Ana sayfa görünümü"""
    return render(request, 'home.html')

def about(request):
    """Hakkında sayfası görünümü"""
    return render(request, 'about.html')

def contact(request):
    """İletişim sayfası görünümü"""
    return render(request, 'contact.html')

def terms(request):
    """Kullanım şartları sayfası görünümü"""
    return render(request, 'terms.html')

def privacy(request):
    """Gizlilik politikası sayfası görünümü"""
    return render(request, 'privacy.html')

@login_required
def profile(request):
    """Kullanıcı profili sayfası görünümü"""
    return render(request, 'users/profile.html', {
        'user': request.user
    })