# users/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.utils.translation import gettext as _
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str  
from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from django.views.decorators.http import require_http_methods
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.db import transaction

from .forms import (
    UserRegistrationForm, 
    AuthenticatedUserLoginForm, 
    UserProfileForm, 
    ChangePasswordForm,
    EnhancedPasswordResetForm
)

from .tokens import account_activation_token
import logging
import uuid

User = get_user_model()
logger = logging.getLogger(__name__)

@sensitive_post_parameters()
@csrf_protect
@never_cache
def register_view(request):
    """Gelişmiş kullanıcı kayıt görünümü"""
    if request.user.is_authenticated:
        return redirect('core:home')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Kullanıcıyı kaydet
                    user = form.save(commit=False)
                    
                    # Email doğrulama sistemi aktif/pasif
                    send_verification_email = False  # Geliştirme sırasında False, üretimde True yapın
                    
                    if send_verification_email:
                        # Email doğrulama için aktif değil olarak işaretle
                        user.is_active = False
                        user.save()
                        
                        # Doğrulama emaili gönder
                        current_site = get_current_site(request)
                        mail_subject = _('LungVision AI - Hesabınızı Etkinleştirin')
                        message = render_to_string('users/email/account_activation_email.html', {
                            'user': user,
                            'domain': current_site.domain,
                            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                            'token': account_activation_token.make_token(user),
                        })
                        email = EmailMessage(
                            mail_subject, message, to=[user.email]
                        )
                        email.content_subtype = "html"
                        email.send()
                        
                        messages.success(request, _(
                            "Hesabınız oluşturuldu! Hesabınızı etkinleştirmek için e-posta adresinize "
                            "gönderilen aktivasyon bağlantısına tıklayın."
                        ))
                        
                        # Kayıt aktivite günlüğü
                        logger.info(f"Kullanıcı kaydı oluşturuldu: {user.email} (ID: {user.id}), doğrulama maili gönderildi.")
                        
                        return redirect('users:login')
                    else:
                        # Email doğrulama olmadan doğrudan aktifleştir
                        user.is_active = True
                        user.is_email_verified = True  # Email doğrulama yapılmadı ama işaretlendi
                        user.save()
                        
                        # Kullanıcıyı doğrudan giriş yaptır
                        login(request, user)
                        
                        # Başarı mesajı
                        messages.success(request, _("Hesabınız başarıyla oluşturuldu! Hoş geldiniz."))
                        
                        # Kayıt aktivite günlüğü
                        logger.info(f"Kullanıcı kaydı oluşturuldu ve giriş yapıldı: {user.email} (ID: {user.id})")
                        
                        return redirect('core:home')
                
            except Exception as e:
                logger.error(f"Kullanıcı kaydı hatası: {str(e)}")
                messages.error(request, _("Hesap oluşturulurken bir hata oluştu. Lütfen tekrar deneyin."))
    else:
        form = UserRegistrationForm()
    
    return render(request, 'users/register.html', {'form': form})

@require_http_methods(["GET"])
def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.is_email_verified = True
        user.save()
        
        # Kullanıcıyı giriş yaptır
        login(request, user)
        
        messages.success(request, _("Hesabınız başarıyla aktifleştirildi. Hoş geldiniz!"))
        logger.info(f"Kullanıcı hesabı aktifleştirildi: {user.email} (ID: {user.id})")
        
        return redirect('core:home')
    else:
        messages.error(request, _("Aktivasyon bağlantısı geçersiz veya süresi dolmuş."))
        return redirect('users:login')

@sensitive_post_parameters()
@csrf_protect
@never_cache
def login_view(request):
    """Gelişmiş kullanıcı giriş görünümü"""
    if request.user.is_authenticated:
        return redirect('core:home')
   
    if request.method == 'POST':
        form = AuthenticatedUserLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
           
            # Kullanıcıyı giriş yaptır
            login(request, user)
           
            # Oturum süresi
            if not form.cleaned_data.get('remember_me', False):
                request.session.set_expiry(0)  # Tarayıcı kapandığında oturum sonlanır
           
            # Başarılı giriş günlüğü
            logger.info(f"Kullanıcı giriş yaptı: {user.email} (ID: {user.id}), IP: {get_client_ip(request)}")
           
            # Login sayacını sıfırla
            user.login_attempts = 0
            user.save(update_fields=['login_attempts'])
           
            # Başarılı giriş mesajı
            messages.success(request, _("Başarıyla giriş yaptınız."))
           
            # Yönlendirme - 'next' parametresini kontrol et
            next_url = request.GET.get('next') or request.POST.get('next') or 'core:home'
            
            # URL ile başlıyorsa doğrudan kullan, aksi halde reverse yap
            if next_url.startswith('/'):
                return redirect(next_url)
            else:
                return redirect(next_url)
        else:
            # Başarısız giriş günlüğü
            email = request.POST.get('username', '')
            logger.warning(f"Başarısız giriş denemesi: {email}, IP: {get_client_ip(request)}")
            
            # Kullanıcıya genel hata mesajı
            messages.error(request, _("Geçersiz e-posta veya şifre. Lütfen tekrar deneyin."))
    else:
        form = AuthenticatedUserLoginForm()
    
    return render(request, 'users/login.html', {'form': form})

@login_required
def logout_view(request):
    """Kullanıcı çıkış görünümü"""
    user_email = request.user.email
    user_id = request.user.id
    
    # Çıkış işlemi
    logout(request)
    
    # Çıkış günlüğü
    logger.info(f"Kullanıcı çıkış yaptı: {user_email} (ID: {user_id}), IP: {get_client_ip(request)}")
    
    # Çıkış mesajı
    messages.success(request, _("Başarıyla çıkış yaptınız. Tekrar görüşmek üzere!"))
    
    return redirect('core:home')

@login_required
@csrf_protect
def profile_view(request):
    """Kullanıcı profili görünümü"""
    user = request.user
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            
            # Profil güncelleme günlüğü
            logger.info(f"Kullanıcı profili güncellendi: {user.email} (ID: {user.id})")
            
            messages.success(request, _("Profiliniz başarıyla güncellendi!"))
            return redirect('users:profile')
    else:
        form = UserProfileForm(instance=user)
    
    # Kullanıcı etkinlik günlüğü (örnek)
    # Gerçek uygulamada bir model veya veritabanı tablosu kullanılacaktır
    activities = [
        {'action': _('Profile bakıldı'), 'timestamp': timezone.now()},
        {'action': _('Son giriş'), 'timestamp': user.last_login}
    ]
    
    return render(request, 'users/profile.html', {
        'form': form,
        'user': user,
        'activities': activities
    })

@login_required
@sensitive_post_parameters()
@csrf_protect
def change_password_view(request):
    """Şifre değiştirme görünümü"""
    user = request.user
    
    if request.method == 'POST':
        form = ChangePasswordForm(user, request.POST)
        if form.is_valid():
            # Şifreyi değiştir
            user = form.save()
            
            # Oturumu güncelle
            update_session_auth_hash(request, user)
            
            # Şifre değişim günlüğü
            logger.info(f"Kullanıcı şifre değiştirdi: {user.email} (ID: {user.id})")
            
            messages.success(request, _("Şifreniz başarıyla değiştirildi!"))
            return redirect('users:profile')
    else:
        form = ChangePasswordForm(user)
    
    return render(request, 'users/change_password.html', {'form': form})

@login_required
def user_settings_view(request):
    """Kullanıcı ayarları görünümü"""
    user = request.user
    
    # Burada kullanıcı ayarları formu ve mantığı eklenecek
    # Şimdilik basit bir görünüm olarak bırakılıyor
    
    return render(request, 'users/settings.html', {'user': user})

def get_client_ip(request):
    """Kullanıcının IP adresini al"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip