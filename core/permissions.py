from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponseForbidden

class IsOwnerOrAdminMixin(UserPassesTestMixin):
    """
    Sadece kaydın sahibine veya admin kullanıcılara erişim izni verir
    """
    def test_func(self):
        obj = self.get_object()
        
        # Admin kullanıcılara her zaman izin ver
        if self.request.user.is_staff:
            return True
        
        # Nesneye bağlı olarak sahibini kontrol et
        if hasattr(obj, 'doctor'):
            return obj.doctor == self.request.user
        elif hasattr(obj, 'uploaded_by'):
            return obj.uploaded_by == self.request.user
        elif hasattr(obj, 'user'):
            return obj.user == self.request.user
        
        # Hiçbir durum karşılanmadıysa erişimi reddet
        return False
    
    def handle_no_permission(self):
        return HttpResponseForbidden("Bu işlemi gerçekleştirmek için yetkiniz yok.")

class IsDoctorOrPathologistMixin(UserPassesTestMixin):
    """
    Sadece doktor veya patolog kullanıcılara erişim izni verir
    """
    def test_func(self):
        return (
            self.request.user.is_authenticated and
            hasattr(self.request.user, 'user_type') and
            self.request.user.user_type in ['doctor', 'pathologist']
        )
    
    def handle_no_permission(self):
        return HttpResponseForbidden("Bu sayfaya erişim için doktor veya patolog olmanız gerekiyor.")

class IsPredictionAllowedMixin(UserPassesTestMixin):
    """
    Sadece belirli kullanıcıların tahmin yapmasına izin verir
    """
    def test_func(self):
        # Temel izin kontrolü
        if not self.request.user.is_authenticated:
            return False
        
        # Sadece doktor ve patologlar tahmin yapabilir
        if hasattr(self.request.user, 'user_type'):
            return self.request.user.user_type in ['doctor', 'pathologist']
        
        return False
    
    def get_object_permission(self, obj):
        # Admin her zaman erişebilir
        if self.request.user.is_staff:
            return True
        
        # Görüntünün yükleyicisi veya vakanın doktoru tahmin yapabilir
        if hasattr(obj, 'uploaded_by'):
            if obj.uploaded_by == self.request.user:
                return True
        
        # Vakayı kontrol et
        if hasattr(obj, 'case') and hasattr(obj.case, 'doctor'):
            return obj.case.doctor == self.request.user
        
        return False
    
    def handle_no_permission(self):
        return HttpResponseForbidden("Tahmin yapma yetkiniz bulunmuyor.")