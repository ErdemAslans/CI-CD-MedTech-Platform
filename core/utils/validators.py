"""
Validators modülü.

Bu modül, çeşitli veri doğrulama işlemleri için kullanılan yardımcı işlevleri içerir.
Form ve model alanları için, API istekleri için ve diğer doğrulama ihtiyaçları için doğrulayıcılar sağlar.
"""

import os
import re
import uuid
import imghdr
from django.core.validators import RegexValidator, ValidationError
from django.utils.translation import gettext_lazy as _

# Temel doğrulama işlevleri
def validate_uuid_format(value):
    """
    UUID formatını doğrular.
    
    Args:
        value: Doğrulanacak değer
        
    Raises:
        ValidationError: Değer geçerli bir UUID formatında değilse
    """
    try:
        uuid_obj = uuid.UUID(str(value))
        return str(uuid_obj) == str(value)
    except (ValueError, AttributeError, TypeError):
        raise ValidationError(_("'%(value)s' geçerli bir UUID formatı değil."), params={'value': value})

# Telefon numarası doğrulayıcısı
phone_regex = RegexValidator(
    regex=r'^\+?1?\d{9,15}$', 
    message=_("Telefon numarası '+999999999' formatında girilmelidir. En fazla 15 rakam.")
)

# Email doğrulayıcısı (daha katı bir doğrulama için)
def validate_email_domain(value):
    """
    Email adresinin alan adını doğrular.
    
    Args:
        value: Doğrulanacak email adresi
        
    Raises:
        ValidationError: Alan adı kabul edilemiyorsa
    """
    # Geçici veya tek kullanımlık email servislerini engelleme
    disposable_domains = [
        'tempmail.com', 'throwawaymail.com', 'mailinator.com', 
        'guerrillamail.com', 'guerrillamailblock.com'
    ]
    
    domain = value.split('@')[-1].lower()
    
    if domain in disposable_domains:
        raise ValidationError(
            _("Geçici email adresleri kabul edilmez. Lütfen kalıcı bir email adresi girin."),
            params={'value': value}
        )

# Görüntü dosyası doğrulayıcıları
def validate_image_size(file_obj, max_size_mb=20):
    """
    Görüntü dosyasının boyutunu doğrular.
    
    Args:
        file_obj: Doğrulanacak dosya nesnesi
        max_size_mb: İzin verilen maksimum dosya boyutu (MB cinsinden)
        
    Raises:
        ValidationError: Dosya boyutu izin verilen maksimumdan büyükse
    """
    if file_obj.size > max_size_mb * 1024 * 1024:
        raise ValidationError(
            _("Dosya boyutu %(max_size)s MB'den küçük olmalıdır. Yüklenen: %(size)s MB."),
            params={
                'max_size': max_size_mb,
                'size': round(file_obj.size / (1024 * 1024), 2)
            }
        )

def validate_image_format(file_obj):
    """
    Görüntü dosyasının formatını doğrular.
    
    Desteklenen formatlar: JPEG, PNG, BMP, TIFF
    
    Args:
        file_obj: Doğrulanacak dosya nesnesi
        
    Raises:
        ValidationError: Dosya desteklenen bir formatta değilse
    """
    # Dosyanın geçici bir konuma kaydedildiğinden emin olun
    if hasattr(file_obj, 'temporary_file_path'):
        file_path = file_obj.temporary_file_path()
    else:
        # Dosya henüz diske kaydedilmemiş
        file_path = None
    
    # İçerik türünü kontrol et
    if file_path:
        # Dosyayı disk üzerinde kontrol et
        img_type = imghdr.what(file_path)
    else:
        # Bellek içeriğini kontrol et
        img_type = imghdr.what(None, h=file_obj.read())
        file_obj.seek(0)  # Dosya göstergesini başa al
    
    valid_formats = ['jpeg', 'jpg', 'png', 'bmp', 'tiff']
    
    if img_type is None or img_type.lower() not in valid_formats:
        raise ValidationError(
            _("Geçersiz görüntü formatı. Desteklenen formatlar: %(formats)s."),
            params={'formats': ', '.join(valid_formats)}
        )

def validate_histopathology_image(file_obj, min_resolution=100, max_size_mb=20):
    """
    Histopatoloji görüntüsünü doğrular.
    
    Args:
        file_obj: Doğrulanacak dosya nesnesi
        min_resolution: Minimum çözünürlük (piksel cinsinden)
        max_size_mb: Maksimum dosya boyutu (MB cinsinden)
        
    Raises:
        ValidationError: Görüntü gereksinimleri karşılamıyorsa
    """
    # Dosya boyutunu kontrol et
    validate_image_size(file_obj, max_size_mb)
    
    # Dosya formatını kontrol et
    validate_image_format(file_obj)
    
    # Çözünürlüğü kontrol et
    import cv2
    import numpy as np
    
    # Dosyayı oku
    image_bytes = file_obj.read()
    file_obj.seek(0)  # Dosya göstergesini başa al
    
    # Bytes'ı numpy dizisine dönüştür
    img_array = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    
    if img is None:
        raise ValidationError(_("Görüntü dosyası okunamadı. Dosya bozuk olabilir."))
    
    # Çözünürlüğü kontrol et
    height, width = img.shape[:2]
    
    if height < min_resolution or width < min_resolution:
        raise ValidationError(
            _("Görüntü çözünürlüğü minimum %(min_res)sx%(min_res)s piksel olmalıdır. "
              "Yüklenen: %(width)sx%(height)s."),
            params={
                'min_res': min_resolution,
                'width': width,
                'height': height
            }
        )