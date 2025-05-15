import os
import uuid
import re
from datetime import datetime
import hashlib

def generate_uuid():
    """Benzersiz UUID oluşturur"""
    return str(uuid.uuid4())

def generate_filename(original_filename):
    """
    Yüklenen dosyalar için güvenli ve benzersiz bir dosya adı oluşturur
    Args:
        original_filename: Orijinal dosya adı
    Returns:
        str: Benzersiz dosya adı
    """
    # Dosya uzantısını al
    _, ext = os.path.splitext(original_filename)
    
    # Tarih ve UUID ile benzersiz isim oluştur
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    uuid_str = str(uuid.uuid4())[:8]
    
    # Güvenli dosya adı oluştur
    safe_filename = f"{timestamp}_{uuid_str}{ext.lower()}"
    
    return safe_filename

def get_file_path(instance, filename):
    """
    Django FileField için dosya yolunu belirler
    Args:
        instance: Model örneği
        filename: Orijinal dosya adı
    Returns:
        str: Dosya yolu
    """
    # Güvenli dosya adı oluştur
    safe_filename = generate_filename(filename)
    
    # İlgili model tipine göre klasör yapısı oluştur
    if hasattr(instance, '__class__') and hasattr(instance.__class__, '__name__'):
        folder = instance.__class__.__name__.lower()
    else:
        folder = 'misc'
    
    # Dosya yolunu oluştur
    return f"{folder}/{safe_filename}"

def sanitize_filename(filename):
    """
    Dosya adını güvenli hale getirir
    Args:
        filename: Orijinal dosya adı
    Returns:
        str: Güvenli dosya adı
    """
    # Uzantıyı ayır
    name, ext = os.path.splitext(filename)
    
    # Güvenli karakterler dışındakileri temizle
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[-\s]+', '-', name).strip('-_')
    
    # Boş isim kontrolü
    if not name:
        name = 'file'
    
    return f"{name}{ext}"

def get_file_hash(file_path):
    """
    Dosyanın SHA-256 hash değerini hesaplar
    Args:
        file_path: Dosya yolu
    Returns:
        str: Hash değeri
    """
    sha256_hash = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        # 4KB'lık parçalar halinde oku
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
            
    return sha256_hash.hexdigest()