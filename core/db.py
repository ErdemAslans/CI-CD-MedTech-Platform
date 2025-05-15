# core/db.py
from django.conf import settings
import pymongo
import logging

logger = logging.getLogger(__name__)

class MongoManager:
    """
    MongoDB bağlantı yöneticisi
    """
    _instance = None
    
    def __new__(cls):
        """Singleton pattern - her zaman aynı örneği döndür"""
        if cls._instance is None:
            cls._instance = super(MongoManager, cls).__new__(cls)
            cls._instance._client = None
            cls._instance._db = None
            cls._instance.connect()
        return cls._instance
    
    def connect(self):
        """MongoDB bağlantısını yap"""
        try:
            # MongoDB bağlantı URL'sini al
            mongo_url = getattr(settings, 'MONGODB_URI', None)
            mongo_db_name = getattr(settings, 'MONGODB_NAME', None)
            
            if not mongo_url or not mongo_db_name:
                logger.error("MongoDB bağlantı bilgileri (MONGODB_URI, MONGODB_NAME) settings.py dosyasında bulunamadı.")
                return
            
            # Bağlantıyı oluştur
            self._client = pymongo.MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
            
            # Bağlantıyı test et
            self._client.server_info()
            
            # Veritabanını al
            self._db = self._client[mongo_db_name]
            
            logger.info(f"MongoDB bağlantısı başarılı: {mongo_db_name}")
        
        except pymongo.errors.ServerSelectionTimeoutError as e:
            logger.error(f"MongoDB sunucusuna bağlanılamadı: {str(e)}")
            self._client = None
            self._db = None
        
        except pymongo.errors.ConfigurationError as e:
            logger.error(f"MongoDB yapılandırma hatası: {str(e)}")
            self._client = None
            self._db = None
        
        except Exception as e:
            logger.error(f"MongoDB bağlantısı sırasında beklenmeyen hata: {str(e)}")
            self._client = None
            self._db = None
    
    @property
    def client(self):
        """MongoDB istemcisini döndür"""
        if self._client is None:
            self.connect()
        return self._client
    
    @property
    def db(self):
        """MongoDB veritabanını döndür"""
        if self._db is None and self.client is not None:
            mongo_db_name = getattr(settings, 'MONGODB_NAME', None)
            if mongo_db_name:
                self._db = self.client[mongo_db_name]
        return self._db
    
    def close(self):
        """MongoDB bağlantısını kapat"""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("MongoDB bağlantısı kapatıldı.")