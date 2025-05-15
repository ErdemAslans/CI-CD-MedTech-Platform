# users/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import RegexValidator
import uuid

class UserManager(BaseUserManager):
    """Modern kullanıcı model yöneticisi"""
    
    def create_user(self, email, username=None, password=None, **extra_fields):
        """Normal kullanıcı oluştur"""
        if not email:
            raise ValueError(_('Email adresi gereklidir'))
        
        email = self.normalize_email(email)
        
        if username is None:
            username = email.split('@')[0]
        
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        
        return user
    
    def create_superuser(self, email, username=None, password=None, **extra_fields):
        """Süper kullanıcı oluştur"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('user_type', 'admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Süper kullanıcı için is_staff=True olmalıdır'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Süper kullanıcı için is_superuser=True olmalıdır'))
        
        return self.create_user(email, username, password, **extra_fields)


class User(AbstractUser):
    """Gelişmiş Kullanıcı modeli"""
    
    USER_TYPE_CHOICES = (
        ('doctor', _('Doktor')),
        ('pathologist', _('Patolog')),
        ('admin', _('Yönetici')),
        ('researcher', _('Araştırmacı')),
    )
    
    username_validator = UnicodeUsernameValidator()
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email adresi'), unique=True)
    username = models.CharField(
        _('kullanıcı adı'),
        max_length=150,
        unique=True,
        validators=[username_validator],
        error_messages={
            'unique': _("Bu kullanıcı adı zaten kullanılıyor."),
        },
    )
    user_type = models.CharField(_('kullanıcı tipi'), max_length=20, choices=USER_TYPE_CHOICES, default='doctor')
    organization = models.CharField(_('kurum'), max_length=255, blank=True, null=True)
    specialty = models.CharField(_('uzmanlık alanı'), max_length=255, blank=True, null=True)
    profile_image = models.ImageField(_('profil resmi'), upload_to='profiles/', blank=True, null=True)
    phone_number = models.CharField(
        _('telefon numarası'), 
        max_length=20, 
        blank=True, 
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message=_("Telefon numarası '+999999999' formatında olmalıdır.")
            )
        ]
    )
    
    # İki faktörlü kimlik doğrulama için alan
    two_factor_enabled = models.BooleanField(_('iki faktörlü doğrulama aktif'), default=False)
    
    # Güvenlik için son şifre değişim tarihi
    last_password_change = models.DateTimeField(_('son şifre değişim tarihi'), auto_now_add=True)
    
    # Hesap aktivasyon durumu
    is_email_verified = models.BooleanField(_('email doğrulandı'), default=False)
    
    # Şüpheli aktiviteler için hesap kilitleme
    login_attempts = models.PositiveIntegerField(_('giriş denemeleri'), default=0)
    is_locked = models.BooleanField(_('hesap kilitli'), default=False)
    locked_until = models.DateTimeField(_('kilit süresi'), null=True, blank=True)
    
    # Denetim alanları
    created_at = models.DateTimeField(_('oluşturulma tarihi'), auto_now_add=True)
    updated_at = models.DateTimeField(_('güncellenme tarihi'), auto_now=True)
    
    # Django'nun standart username yerine email ile login olma
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    objects = UserManager()
    
    def __str__(self):
        return f"{self.email} ({self.get_user_type_display()})"
    
    def get_full_name(self):
        """Kullanıcının tam adını döndürür."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username or self.email
    
    def get_short_name(self):
        """Kısa ad döndürür."""
        return self.first_name or self.username
    
    def has_perm(self, perm, obj=None):
        """Belirli bir izne sahip mi kontrol et."""
        # Kilitli hesaplar izinsizdir
        if self.is_locked:
            return False
        return super().has_perm(perm, obj)

    def has_module_perms(self, app_label):
        """Modül izinleri kontrolü."""
        # Kilitli hesaplar izinsizdir
        if self.is_locked:
            return False
        return super().has_module_perms(app_label)
        
    class Meta:
        verbose_name = _('kullanıcı')
        verbose_name_plural = _('kullanıcılar')
        ordering = ['-created_at']