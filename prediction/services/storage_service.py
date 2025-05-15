"""
Depolama servisi.

Bu modül, görüntü dosyalarının depolanması ve yönetilmesi için işlevler sağlar.
Hem yerel dosya sistemi hem de bulut depolama servisleri (AWS S3, GCS) desteklenir.
"""

import os
import shutil
import uuid
import datetime
import mimetypes
from typing import Optional, Dict, Any, Tuple, List, BinaryIO, Union
from pathlib import Path
import logging
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

logger = logging.getLogger('lungvision.storage')

class StorageService:
    """
    Dosya depolama işlemlerini yöneten servis sınıfı.
    
    Bu sınıf, LungVision'da kullanılan tüm dosya depolama işlemlerini soyutlar
    ve hem yerel hem de bulut depolama sistemleri için tutarlı bir API sağlar.
    """
    
    # Geçerli depolama stratejisi
    STORAGE_STRATEGY = getattr(settings, 'STORAGE_STRATEGY', 'local')
    
    # Depolama dizinleri
    SAMPLE_DIRECTORY = 'samples'
    GRADCAM_DIRECTORY = 'gradcam'
    REPORT_DIRECTORY = 'reports'
    
    @classmethod
    def get_storage_backend(cls):
        """
        Yapılandırılmış depolama stratejisine göre uygun depolama backend'ini döndürür.
        
        Returns:
            storage: Django depolama backend'i
        """
        return default_storage
    
    @classmethod
    def generate_unique_filename(cls, original_filename: str) -> str:
        """
        Benzersiz bir dosya adı oluşturur.
        
        Args:
            original_filename: Orijinal dosya adı
            
        Returns:
            Benzersiz dosya adı (timestamp ve UUID ile)
        """
        # Dosya uzantısını al
        _, ext = os.path.splitext(original_filename)
        
        # Zaman damgası ve UUID kullanarak benzersiz bir dosya adı oluştur
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        
        return f"{timestamp}_{unique_id}{ext.lower()}"
    
    @classmethod
    def _validate_directory(cls, directory: str) -> str:
        """
        Dizin yolunu doğrular ve gerekirse oluşturur.
        
        Args:
            directory: Dizin yolu
            
        Returns:
            Doğrulanmış dizin yolu
        """
        # Boş dizin kontrolü
        if not directory:
            raise ValueError("Geçersiz dizin yolu: Boş değer")
        
        # Yasaklı yolların kontrolü
        if any(p in directory for p in ['..', './', '/']):
            raise ValueError(f"Geçersiz dizin yolu: {directory}")
        
        # Dizinin var olduğundan emin ol (storage türüne göre)
        if cls.STORAGE_STRATEGY == 'local':
            storage_dir = os.path.join(settings.MEDIA_ROOT, directory)
            os.makedirs(storage_dir, exist_ok=True)
        
        return directory
    
    @classmethod
    def save_file(cls, file_obj: BinaryIO, directory: str, filename: Optional[str] = None) -> str:
        """
        Dosyayı belirtilen dizine kaydeder.
        
        Args:
            file_obj: Dosya nesnesi
            directory: Dizin yolu
            filename: Dosya adı (None ise otomatik oluşturulur)
            
        Returns:
            Kaydedilen dosyanın göreli yolu
        """
        # Dizini doğrula
        directory = cls._validate_directory(directory)
        
        # Dosya adını kontrol et
        if filename is None:
            if hasattr(file_obj, 'name'):
                original_filename = file_obj.name
            else:
                # Dosya adı yoksa varsayılan bir ad ve uzantı kullan
                mime_type, _ = mimetypes.guess_type(file_obj.name if hasattr(file_obj, 'name') else '')
                ext = mimetypes.guess_extension(mime_type) if mime_type else '.bin'
                original_filename = f"file{ext}"
            
            filename = cls.generate_unique_filename(original_filename)
        
        # Dosya tam yolunu oluştur (depolama dizinine göre)
        file_path = os.path.join(directory, filename)
        
        # Dosyayı kaydet
        storage = cls.get_storage_backend()
        
        if hasattr(file_obj, 'chunks'):
            # Django UploadedFile nesnesi
            content = b''
            for chunk in file_obj.chunks():
                content += chunk
            file_path = storage.save(file_path, ContentFile(content))
        else:
            # Açık dosya nesnesi
            file_path = storage.save(file_path, file_obj)
        
        logger.info(f"Dosya kaydedildi: {file_path}")
        
        return file_path
    
    @classmethod
    def save_histopathology_image(cls, image_file: BinaryIO, filename: Optional[str] = None) -> str:
        """
        Histopatolojik görüntüyü kaydeder.
        
        Args:
            image_file: Görüntü dosyası
            filename: Dosya adı (None ise otomatik oluşturulur)
            
        Returns:
            Kaydedilen görüntünün göreli yolu
        """
        return cls.save_file(image_file, cls.SAMPLE_DIRECTORY, filename)
    
    @classmethod
    def save_gradcam_image(cls, gradcam_image: BinaryIO, filename: Optional[str] = None) -> str:
        """
        Grad-CAM görüntüsünü kaydeder.
        
        Args:
            gradcam_image: Grad-CAM görüntü dosyası
            filename: Dosya adı (None ise otomatik oluşturulur)
            
        Returns:
            Kaydedilen Grad-CAM görüntüsünün göreli yolu
        """
        return cls.save_file(gradcam_image, cls.GRADCAM_DIRECTORY, filename)
    
    @classmethod
    def save_report(cls, report_content: Union[str, bytes], report_format: str, filename: Optional[str] = None) -> str:
        """
        Rapor dosyasını kaydeder.
        
        Args:
            report_content: Rapor içeriği
            report_format: Rapor formatı ('pdf', 'csv', 'json', vb.)
            filename: Dosya adı (None ise otomatik oluşturulur)
            
        Returns:
            Kaydedilen raporun göreli yolu
        """
        # Varsayılan uzantıyı ayarla
        if filename is None:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"report_{timestamp}.{report_format}"
        
        file_path = os.path.join(cls.REPORT_DIRECTORY, filename)
        
        # İçeriği kaydet
        storage = cls.get_storage_backend()
        
        if isinstance(report_content, str):
            file_path = storage.save(file_path, ContentFile(report_content.encode('utf-8')))
        else:
            file_path = storage.save(file_path, ContentFile(report_content))
        
        logger.info(f"Rapor kaydedildi: {file_path}")
        
        return file_path
    
    @classmethod
    def get_file_url(cls, file_path: str) -> str:
        """
        Dosya için URL döndürür.
        
        Args:
            file_path: Dosya yolu
            
        Returns:
            Dosya URL'si
        """
        storage = cls.get_storage_backend()
        return storage.url(file_path)
    
    @classmethod
    def delete_file(cls, file_path: str) -> bool:
        """
        Dosyayı siler.
        
        Args:
            file_path: Silinecek dosyanın yolu
            
        Returns:
            bool: Silme işlemi başarılıysa True
        """
        try:
            storage = cls.get_storage_backend()
            storage.delete(file_path)
            logger.info(f"Dosya silindi: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Dosya silinirken hata: {str(e)}")
            return False
    
    @classmethod
    def get_file_metadata(cls, file_path: str) -> Dict[str, Any]:
        """
        Dosya meta verilerini döndürür.
        
        Args:
            file_path: Dosya yolu
            
        Returns:
            Dosya meta verileri (boyut, oluşturma tarihi, vb.)
        """
        storage = cls.get_storage_backend()
        
        try:
            stat_result = storage.stat(file_path)
            
            return {
                'size': stat_result.st_size,
                'created_at': datetime.datetime.fromtimestamp(stat_result.st_ctime),
                'modified_at': datetime.datetime.fromtimestamp(stat_result.st_mtime),
                'path': file_path,
                'url': storage.url(file_path),
                'name': os.path.basename(file_path)
            }
        except Exception as e:
            logger.error(f"Dosya meta verileri alınırken hata: {str(e)}")
            return {
                'path': file_path,
                'name': os.path.basename(file_path),
                'error': str(e)
            }


class S3StorageService(StorageService):
    """
    AWS S3 için depolama servisi.
    
    Temel StorageService sınıfını genişleterek, AWS S3 özgü işlevsellik sağlar.
    """
    
    @classmethod
    def generate_presigned_url(cls, file_path: str, expiration: int = 3600) -> str:
        """
        Geçici bir ön imzalı URL oluşturur.
        
        Args:
            file_path: Dosya yolu
            expiration: URL'nin geçerlilik süresi (saniye)
            
        Returns:
            Ön imzalı URL
        """
        import boto3
        from botocore.exceptions import NoCredentialsError
        
        try:
            # S3 istemcisini oluştur
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME
            )
            
            # Ön imzalı URL oluştur
            bucket_name = settings.AWS_STORAGE_BUCKET_NAME
            response = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': bucket_name,
                    'Key': file_path
                },
                ExpiresIn=expiration
            )
            
            return response
        
        except NoCredentialsError:
            logger.error("AWS kimlik bilgileri bulunamadı")
            raise
        except Exception as e:
            logger.error(f"Ön imzalı URL oluşturulurken hata: {str(e)}")
            raise


class GoogleCloudStorageService(StorageService):
    """
    Google Cloud Storage için depolama servisi.
    
    Temel StorageService sınıfını genişleterek, GCS özgü işlevsellik sağlar.
    """
    
    @classmethod
    def generate_signed_url(cls, file_path: str, expiration: int = 3600) -> str:
        """
        Geçici bir imzalı URL oluşturur.
        
        Args:
            file_path: Dosya yolu
            expiration: URL'nin geçerlilik süresi (saniye)
            
        Returns:
            İmzalı URL
        """
        from google.cloud import storage
        
        try:
            # GCS istemcisini oluştur
            storage_client = storage.Client()
            
            # Bucket ve blob
            bucket_name = settings.GS_BUCKET_NAME
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(file_path)
            
            # İmzalı URL oluştur
            url = blob.generate_signed_url(
                version="v4",
                expiration=datetime.timedelta(seconds=expiration),
                method="GET"
            )
            
            return url
        
        except Exception as e:
            logger.error(f"İmzalı URL oluşturulurken hata: {str(e)}")
            raise