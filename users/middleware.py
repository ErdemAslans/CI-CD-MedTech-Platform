# users/middleware.py
from core.db import MongoManager
from core.auth import MongoDBUser

class MongoDBAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Kullanıcı ID'sini session'dan al
        user_id = request.session.get('user_id')
        
        if user_id:
            # MongoDB'den kullanıcıyı al
            mongo = MongoManager()
            if mongo.db:
                user_doc = mongo.db.users.find_one({'_id': user_id})
                if user_doc:
                    # Kullanıcı nesnesini oluştur ve request'e ekle
                    request.user = MongoDBUser(user_doc)
                    request.user.is_authenticated = True
                else:
                    # Kullanıcı bulunamadı, session'ı temizle
                    del request.session['user_id']
                    request.user = None
                    request.user.is_authenticated = False
        else:
            request.user = None
            request.user.is_authenticated = False
        
        response = self.get_response(request)
        return response