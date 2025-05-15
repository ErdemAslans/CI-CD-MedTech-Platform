# users/forms.py
from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.utils import timezone
from django.contrib.auth.hashers import check_password
import re

User = get_user_model()

class UserRegistrationForm(forms.ModelForm):
    """Gelişmiş kullanıcı kaydı formu"""
    
    password1 = forms.CharField(
        label=_('Şifre'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'autocomplete': 'new-password',
        }),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label=_('Şifre Tekrar'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'autocomplete': 'new-password',
        }),
        strip=False,
        help_text=_("Doğrulama için aynı şifreyi tekrar girin."),
    )
    
    terms_accepted = forms.BooleanField(
        label=_('Kullanım Şartları ve Gizlilik Politikasını kabul ediyorum'),
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'})
    )
    
    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'user_type', 
                 'organization', 'specialty', 'phone_number')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'ornek@mail.com'}),
            'username': forms.TextInput(attrs={'class': 'form-input'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'user_type': forms.Select(attrs={'class': 'form-input'}),
            'organization': forms.TextInput(attrs={'class': 'form-input'}),
            'specialty': forms.TextInput(attrs={'class': 'form-input'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+90...'}),
        }
        help_texts = {
            'email': _('Kayıt ve giriş için e-posta adresiniz kullanılacaktır.'),
            'username': _('Kullanıcı adınız profilinizde görünecektir.'),
            'user_type': _('Sizin için uygun olan kullanıcı tipini seçin.'),
        }
    
    def clean_password1(self):
        """Güçlü şifre validasyonu"""
        password1 = self.cleaned_data.get('password1')
        
        # Özel şifre gereklilikleri
        if len(password1) < 8:
            raise forms.ValidationError(_("Şifreniz en az 8 karakter olmalıdır."))
        
        if not re.search(r'[A-Z]', password1):
            raise forms.ValidationError(_("Şifreniz en az bir büyük harf içermelidir."))
            
        if not re.search(r'[a-z]', password1):
            raise forms.ValidationError(_("Şifreniz en az bir küçük harf içermelidir."))
            
        if not re.search(r'[0-9]', password1):
            raise forms.ValidationError(_("Şifreniz en az bir rakam içermelidir."))
            
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password1):
            raise forms.ValidationError(_("Şifreniz en az bir özel karakter içermelidir."))
        
        # Django'nun şifre validatörleri
        try:
            password_validation.validate_password(password1, self.instance)
        except forms.ValidationError as error:
            self.add_error('password1', error)
            
        return password1
        
    def clean_password2(self):
        """Şifre eşleşme kontrolü"""
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_("Şifreler eşleşmiyor."))
            
        return password2
        
    def clean_email(self):
        """Email varlık kontrolü ve formatı doğrulama"""
        email = self.cleaned_data.get('email')
        
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_("Bu e-posta adresi zaten kullanılıyor."))
            
        # Email formatı daha sıkı kontrol edilebilir
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise forms.ValidationError(_("Geçerli bir e-posta adresi girin."))
            
        return email
        
    def clean_username(self):
        """Kullanıcı adı varlık kontrolü"""
        username = self.cleaned_data.get('username')
        
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(_("Bu kullanıcı adı zaten kullanılıyor."))
            
        # Güvenlik için kullanıcı adını da kontrol et
        if len(username) < 4:
            raise forms.ValidationError(_("Kullanıcı adı en az 4 karakter olmalıdır."))
            
        if not re.match(r'^[a-zA-Z0-9_.]+$', username):
            raise forms.ValidationError(_("Kullanıcı adı sadece harf, rakam, alt çizgi ve nokta içerebilir."))
            
        return username
        
    def save(self, commit=True):
        """Kullanıcıyı kaydet"""
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        
        # İlave alanları ayarla
        user.is_active = True  # Hesap doğrulama sistemi eklenirse False yapılabilir
        user.is_email_verified = False  # Email doğrulama sonrası True olacak
        user.last_password_change = timezone.now()
        
        if commit:
            user.save()
        
        return user


class AuthenticatedUserLoginForm(AuthenticationForm):
    """Gelişmiş kullanıcı giriş formu"""
    
    username = forms.EmailField(
        label=_('E-posta Adresi'),
        widget=forms.EmailInput(attrs={
            'class': 'form-input', 
            'placeholder': 'ornek@mail.com',
            'autocomplete': 'email'
        })
    )
    
    password = forms.CharField(
        label=_('Şifre'),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-input', 
            'autocomplete': 'current-password'
        }),
    )
    
    remember_me = forms.BooleanField(
        label=_('Beni hatırla'),
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'})
    )
    
    error_messages = {
        'invalid_login': _(
            "Lütfen doğru bir e-posta ve şifre girdiğinizden emin olun. "
            "Her iki alan da büyük-küçük harfe duyarlıdır."
        ),
        'inactive': _("Bu hesap aktif değil."),
        'locked': _("Hesabınız kilitlenmiştir. Lütfen daha sonra tekrar deneyin veya şifre sıfırlama işlemi yapın."),
    }
    
    def clean(self):
        """Formun temizlenmesi ve ek doğrulamaların yapılması"""
        cleaned_data = super().clean()
        
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        
        if username and password:
            # Kullanıcıyı bul
            try:
                user = User.objects.get(email=username)
                
                # Hesap kilitli mi kontrol et
                if user.is_locked:
                    if user.locked_until and user.locked_until > timezone.now():
                        # Hesap hala kilitli
                        raise forms.ValidationError(
                            self.error_messages['locked'],
                            code='locked',
                        )
                    else:
                        # Kilit süresi dolmuş, hesabı aç
                        user.is_locked = False
                        user.login_attempts = 0
                        user.locked_until = None
                        user.save(update_fields=['is_locked', 'login_attempts', 'locked_until'])
                
                # Şifreyi kontrol et
                if not check_password(password, user.password):
                    # Başarısız giriş denemesi sayısını artır
                    user.login_attempts += 1
                    
                    # 5 başarısız denemeden sonra hesabı kilitle
                    if user.login_attempts >= 5:
                        from datetime import timedelta
                        user.is_locked = True
                        user.locked_until = timezone.now() + timedelta(minutes=30)  # 30 dakika kilitle
                        user.save(update_fields=['is_locked', 'login_attempts', 'locked_until'])
                        
                        raise forms.ValidationError(
                            self.error_messages['locked'],
                            code='locked',
                        )
                    else:
                        user.save(update_fields=['login_attempts'])
                
            except User.DoesNotExist:
                # Kullanıcı bulunamadı, normal hata mesajı göster
                pass
                
        return cleaned_data


class UserProfileForm(forms.ModelForm):
    """Kullanıcı profil düzenleme formu"""
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'organization', 'specialty', 'phone_number', 'profile_image')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'organization': forms.TextInput(attrs={'class': 'form-input'}),
            'specialty': forms.TextInput(attrs={'class': 'form-input'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-input'}),
            'profile_image': forms.ClearableFileInput(attrs={'class': 'form-input'}),
        }


class ChangePasswordForm(forms.Form):
    """Şifre değiştirme formu"""
    
    old_password = forms.CharField(
        label=_('Mevcut Şifre'),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'autocomplete': 'current-password'}),
    )
    
    new_password1 = forms.CharField(
        label=_('Yeni Şifre'),
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'autocomplete': 'new-password'}),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    
    new_password2 = forms.CharField(
        label=_('Yeni Şifre (Tekrar)'),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'autocomplete': 'new-password'}),
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_old_password(self):
        """Eski şifreyi doğrula"""
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise forms.ValidationError(_('Mevcut şifreniz yanlış. Lütfen tekrar deneyin.'))
        return old_password
    
    def clean_new_password1(self):
        """Yeni şifreyi doğrula"""
        password1 = self.cleaned_data.get('new_password1')
        
        # Özel şifre gereklilikleri
        if len(password1) < 8:
            raise forms.ValidationError(_("Şifreniz en az 8 karakter olmalıdır."))
        
        if not re.search(r'[A-Z]', password1):
            raise forms.ValidationError(_("Şifreniz en az bir büyük harf içermelidir."))
            
        if not re.search(r'[a-z]', password1):
            raise forms.ValidationError(_("Şifreniz en az bir küçük harf içermelidir."))
            
        if not re.search(r'[0-9]', password1):
            raise forms.ValidationError(_("Şifreniz en az bir rakam içermelidir."))
            
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password1):
            raise forms.ValidationError(_("Şifreniz en az bir özel karakter içermelidir."))
    
        # Django'nun şifre validatörleri
        password_validation.validate_password(password1, self.user)
        
        # Şifre, eski şifreyle aynı olmamalı
        if self.user.check_password(password1):
            raise forms.ValidationError(_('Yeni şifreniz eski şifrenizle aynı olamaz.'))
            
        return password1
    
    def clean_new_password2(self):
        """Şifre eşleşmesini kontrol et"""
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_("İki şifre eşleşmiyor."))
        return password2
    
    def save(self, commit=True):
        """Yeni şifreyi kaydet"""
        password = self.cleaned_data["new_password1"]
        self.user.set_password(password)
        self.user.last_password_change = timezone.now()
        if commit:
            self.user.save()
        return self.user


class EnhancedPasswordResetForm(PasswordResetForm):
    """Geliştirilmiş şifre sıfırlama formu"""
    
    email = forms.EmailField(
        label=_("E-posta Adresi"),
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-input', 
            'placeholder': 'ornek@mail.com',
            'autocomplete': 'email'
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data['email']
        # E-posta adresinin varlığını kontrol et
        if not User.objects.filter(email=email, is_active=True).exists():
            # Güvenlik nedeniyle aynı hata mesajını göster
            raise forms.ValidationError(_("Bu e-posta adresiyle kayıtlı bir hesap bulunamadı."))
        return email


class EnhancedSetPasswordForm(SetPasswordForm):
    """Geliştirilmiş şifre ayarlama formu"""
    
    new_password1 = forms.CharField(
        label=_("Yeni Şifre"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'autocomplete': 'new-password'
        }),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    
    new_password2 = forms.CharField(
        label=_("Yeni Şifre (Tekrar)"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'autocomplete': 'new-password'
        }),
    )
    
    def clean_new_password1(self):
        """Yeni şifreyi doğrula"""
        password1 = self.cleaned_data.get('new_password1')
        
        # Özel şifre gereklilikleri
        if len(password1) < 8:
            raise forms.ValidationError(_("Şifreniz en az 8 karakter olmalıdır."))
        
        if not re.search(r'[A-Z]', password1):
            raise forms.ValidationError(_("Şifreniz en az bir büyük harf içermelidir."))
            
        if not re.search(r'[a-z]', password1):
            raise forms.ValidationError(_("Şifreniz en az bir küçük harf içermelidir."))
            
        if not re.search(r'[0-9]', password1):
            raise forms.ValidationError(_("Şifreniz en az bir rakam içermelidir."))
            
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password1):
            raise forms.ValidationError(_("Şifreniz en az bir özel karakter içermelidir."))
    
        # Django'nun şifre validatörleri
        try:
            password_validation.validate_password(password1, self.user)
        except forms.ValidationError as error:
            self.add_error('new_password1', error)
            
        return password1