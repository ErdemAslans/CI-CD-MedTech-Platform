# users/auth.py
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone
from django.conf import settings
from core.db import MongoManager
import uuid

class MongoDBAuthBackend(BaseBackend):
    """
    MongoDB için özel kimlik doğrulama backend'i
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        MongoDB'de kullanıcı kimlik doğrulama
        """
        mongo = MongoManager()
        if mongo.db is None:
            return None
        
        # Email ile kullanıcıyı bul
        user_doc = mongo.db.users.find_one({'email': username})
        
        if user_doc is not None and check_password(password, user_doc.get('password')):
            # Kullanıcı doğrulandı, MongoUser nesnesini oluştur ve döndür
            user = MongoUser(user_doc)
            
            # Son giriş zamanını güncelle
            mongo.db.users.update_one(
                {'_id': user_doc['_id']},
                {'$set': {'last_login': timezone.now(), 'login_count': user_doc.get('login_count', 0) + 1}}
            )
            
            return user
        
        return None
    
    def get_user(self, user_id):
        """
        Kullanıcı ID'sine göre kullanıcıyı getir
        """
        mongo = MongoManager()
        if mongo.db is None:
            return None
        
        user_doc = mongo.db.users.find_one({'_id': user_id})
        if user_doc:
            return MongoUser(user_doc)
        
        return None

class MongoUser:
    """
    MongoDB kullanıcı dokümanını Django auth sistemi ile uyumlu hale getiren sınıf
    """
    
    def __init__(self, user_doc):
        self._user_doc = user_doc
        self.id = str(user_doc['_id'])
        self.username = user_doc.get('username', '')
        self.email = user_doc.get('email', '')
        self.first_name = user_doc.get('first_name', '')
        self.last_name = user_doc.get('last_name', '')
        self.is_active = user_doc.get('is_active', True)
        self.is_staff = user_doc.get('is_staff', False)
        self.is_superuser = user_doc.get('is_superuser', False)
        self.user_type = user_doc.get('user_type', 'doctor')
        self.organization = user_doc.get('organization', '')
        self.specialty = user_doc.get('specialty', '')
        self.phone_number = user_doc.get('phone_number', '')
        self.date_joined = user_doc.get('date_joined', timezone.now())
        self.last_login = user_doc.get('last_login')
    
    def __str__(self):
        return f"{self.email} ({self.get_user_type_display()})"
    
    def is_authenticated(self):
        return True
    
    def is_anonymous(self):
        return False
    
    def get_username(self):
        return self.email
    
    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username or self.email
    
    def get_short_name(self):
        return self.first_name or self.username
    
    def get_user_type_display(self):
        user_types = {
            'doctor': 'Doktor',
            'pathologist': 'Patolog',
            'admin': 'Yönetici',
            'researcher': 'Araştırmacı'
        }
        return user_types.get(self.user_type, self.user_type)
    
    def has_perm(self, perm, obj=None):
        """
        Kullanıcının belirli bir izne sahip olup olmadığını kontrol et
        """
        if self.is_superuser:
            return True
        
        # Temel izin sistemi
        mongo = MongoManager()
        if mongo.db is None:
            return False
        
        permission_doc = mongo.db.permissions.find_one({
            'user_id': self.id,
            'permission': perm
        })
        
        return permission_doc is not None
    
    def has_module_perms(self, app_label):
        """
        Kullanıcının belirli bir modüle erişim izni olup olmadığını kontrol et
        """
        if self.is_superuser:
            return True
        
        # Modül izinleri kontrolü
        return True  # Basitleştirmek için tüm modüllere izin ver
    
    def set_password(self, raw_password):
        """
        Kullanıcı şifresini güncelle
        """
        mongo = MongoManager()
        if mongo.db is not None:
            mongo.db.users.update_one(
                {'_id': self._user_doc['_id']},
                {'$set': {
                    'password': make_password(raw_password),
                    'last_password_change': timezone.now()
                }}
            )
    
    def check_password(self, raw_password):
        """
        Verilen ham şifrenin, kullanıcının şifresiyle eşleşip eşleşmediğini kontrol et
        """
        return check_password(raw_password, self._user_doc.get('password', ''))