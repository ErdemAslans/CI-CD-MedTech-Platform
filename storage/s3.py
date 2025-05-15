import boto3
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class S3Storage:
    """AWS S3 depolama işlemleri için yardımcı sınıf"""
    
    def __init__(self):
        """S3 bağlantısını başlatır"""
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME
            )
            self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
            logger.info(f"S3 client başarıyla başlatıldı. Bucket: {self.bucket_name}")
        except Exception as e:
            logger.error(f"S3 client başlatma hatası: {e}")
            self.s3_client = None
    
    def upload_file(self, local_path, s3_key):
        """
        Dosyayı S3'e yükler
        Args:
            local_path: Yüklenecek dosyanın yerel yolu
            s3_key: S3'e kaydedilecek dosya yolu
        Returns:
            (success, url): Başarı durumu ve S3 URL'si
        """
        if self.s3_client is None:
            logger.error("S3 client başlatılmadı. Dosya yüklenemedi.")
            return False, None
        
        try:
            self.s3_client.upload_file(
                Filename=local_path,
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            # URL oluştur
            url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"
            logger.info(f"Dosya başarıyla S3'e yüklendi: {url}")
            
            return True, url
        
        except Exception as e:
            logger.error(f"S3 dosya yükleme hatası: {e}")
            return False, None
    
    def download_file(self, s3_key, local_path):
        """
        S3'ten dosya indirir
        Args:
            s3_key: S3'ten indirilecek dosya yolu
            local_path: Kaydedilecek yerel yol
        Returns:
            success: Başarı durumu
        """
        if self.s3_client is None:
            logger.error("S3 client başlatılmadı. Dosya indirilemedi.")
            return False
        
        try:
            self.s3_client.download_file(
                Bucket=self.bucket_name,
                Key=s3_key,
                Filename=local_path
            )
            logger.info(f"Dosya başarıyla S3'ten indirildi: {local_path}")
            return True
        
        except Exception as e:
            logger.error(f"S3 dosya indirme hatası: {e}")
            return False
    
    def delete_file(self, s3_key):
        """
        S3'ten dosya siler
        Args:
            s3_key: S3'ten silinecek dosya yolu
        Returns:
            success: Başarı durumu
        """
        if self.s3_client is None:
            logger.error("S3 client başlatılmadı. Dosya silinemedi.")
            return False
        
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            logger.info(f"Dosya başarıyla S3'ten silindi: {s3_key}")
            return True
        
        except Exception as e:
            logger.error(f"S3 dosya silme hatası: {e}")
            return False