# users/apps.py
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    verbose_name = _('Kullanıcılar')
    
    def ready(self):
        """
        Uygulama hazır olduğunda çalışacak kod
        """
        # MongoDB indeksleri oluştur
        from core.db import MongoManager
        mongo = MongoManager()
        
        if mongo.db is not None:
            # Kullanıcı koleksiyonu indeksleri
            mongo.db.users.create_index('email', unique=True)
            mongo.db.users.create_index('username', unique=True)
            
            # Aktivite günlükleri indeksleri
            mongo.db.activity_logs.create_index([('user_id', 1), ('timestamp', -1)])
            
            # Giriş günlükleri indeksleri
            mongo.db.login_logs.create_index([('user_id', 1), ('timestamp', -1)])
            mongo.db.login_logs.create_index([('ip_address', 1), ('timestamp', -1)])
            
            # Kullanıcı ayarları indeksi
            mongo.db.user_settings.create_index('user_id', unique=True)
            
            # Admin kullanıcısını kontrol et ve yoksa oluştur
            from django.contrib.auth.hashers import make_password
            import uuid
            
            admin_email = 'admin@lungvision.com'
            admin_exists = mongo.db.users.find_one({'email': admin_email})
            
            if not admin_exists:
                from django.utils import timezone
                
                admin_id = str(uuid.uuid4())
                mongo.db.users.insert_one({
                    '_id': admin_id,
                    'email': admin_email,
                    'username': 'admin',
                    'password': make_password('Admin123!'),  # Güvenli bir şifre kullanın
                    'first_name': 'Admin',
                    'last_name': 'User',
                    'user_type': 'admin',
                    'is_active': True,
                    'is_staff': True,
                    'is_superuser': True,
                    'date_joined': timezone.now(),
                    'last_login': None
                })
                
                # Admin kullanıcısı için ayarlar oluştur
                mongo.db.user_settings.insert_one({
                    'user_id': admin_id,
                    'theme': 'light',
                    'notifications_enabled': True,
                    'dashboard_favorites': [],
                    'created_at': timezone.now()
                })