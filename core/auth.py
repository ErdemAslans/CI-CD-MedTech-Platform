from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone
from core.db import MongoManager
import uuid

class MongoDBUserBackend(BaseBackend):
    """MongoDB kullanıcı kimlik doğrulama backend'i"""
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """Kullanıcı kimlik doğrulaması yapar"""
        mongo = MongoManager()
        if mongo.db is None:
            return None
        
        # Email veya kullanıcı adı ile kullanıcıyı bul
        user_doc = mongo.db.users.find_one({'$or': [
            {'email': username},
            {'username': username}
        ]})
        
        if user_doc and check_password(password, user_doc.get('password', '')):
            # Kullanıcı doğrulandı, MongoUser nesnesini oluştur
            user = MongoDBUser(user_doc)
            
            # Son giriş zamanını güncelle
            mongo.db.users.update_one(
                {'_id': user_doc['_id']},
                {'$set': {'last_login': timezone.now()}}
            )
            
            return user
        
        return None
    
    def get_user(self, user_id):
        """User ID ile kullanıcıyı getirir"""
        mongo = MongoManager()
        if mongo.db is None:
            return None
        
        user_doc = mongo.db.users.find_one({'_id': user_id})
        if user_doc:
            return MongoDBUser(user_doc)
        
        return None

class MongoDBUser:
    """MongoDB kullanıcı sınıfı"""
    
    def __init__(self, user_doc):
        self.id = user_doc.get('_id')  # Django'nun session yönetimi için id gereklidir
        self.username = user_doc.get('username', '')
        self.email = user_doc.get('email', '')
        self.first_name = user_doc.get('first_name', '')
        self.last_name = user_doc.get('last_name', '')
        self.is_active = user_doc.get('is_active', True)
        self.is_staff = user_doc.get('is_staff', False)
        self.is_superuser = user_doc.get('is_superuser', False)
        self.user_type = user_doc.get('user_type', 'doctor')
        self.date_joined = user_doc.get('date_joined')
        self.last_login = user_doc.get('last_login')
        self._password = user_doc.get('password', '')
        self._user_doc = user_doc
    
    def __str__(self):
        return self.email or self.username
    
    def is_authenticated(self):
        """Django auth için gerekli metod"""
        return True
    
    def is_anonymous(self):
        """Django auth için gerekli metod"""
        return False
    
    def get_username(self):
        """Django auth için gerekli metod"""
        return self.username
    
    def get_id(self):
        """Kullanıcı ID'sini döndürür"""
        return self.id
    
    def check_password(self, raw_password):
        """Şifre doğrulama"""
        return check_password(raw_password, self._password)