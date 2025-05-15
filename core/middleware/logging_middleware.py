"""
Logging Middleware

Bu middleware, uygulamaya gelen tüm HTTP isteklerini ve yanıtlarını loglar.
Performans izleme, hata ayıklama ve güvenlik denetimi için kullanılır.
"""
import time
import json
import logging
from django.conf import settings
from django.utils import timezone

# Özel logger yapılandırması
logger = logging.getLogger('lungvision.api')

class APILoggingMiddleware:
    """
    API istek ve yanıtlarını loglamak için middleware.
    
    Bu middleware, her API isteğini ve yanıtını yapılandırılmış logger'a kaydeder.
    İstek gövdesi, yanıt durumu, işlem süresi ve diğer önemli bilgileri içerir.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Ayarlardan hassas alan listesini al
        self.sensitive_fields = getattr(settings, 'API_LOGGING_SENSITIVE_FIELDS', [
            'password', 'token', 'access', 'refresh', 'secret', 'credential', 'api_key'
        ])
        
        # API prefix kontrolü için
        self.api_paths = getattr(settings, 'API_LOGGING_PATHS', ['/api/'])
        
    def __call__(self, request):
        # Sadece API isteklerini logla
        if not any(request.path.startswith(path) for path in self.api_paths):
            return self.get_response(request)
            
        # İstek zamanını kaydet
        start_time = time.time()
        
        # İstek bilgilerini hazırla
        request_data = {
            'timestamp': timezone.now().isoformat(),
            'method': request.method,
            'path': request.path,
            'query_params': dict(request.GET.items()),
            'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
            'ip': self.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
        
        # İstek gövdesini alın (JSON ise)
        if request.content_type == 'application/json' and request.body:
            try:
                body = json.loads(request.body)
                # Hassas alanları maskele
                for field in self.sensitive_fields:
                    if field in body:
                        body[field] = '******'
                request_data['body'] = body
            except:
                request_data['body'] = '[Unable to parse JSON body]'
        
        # İsteği logla
        logger.info(f"API Request: {json.dumps(request_data, default=str)}")
        
        # Yanıtı al
        response = self.get_response(request)
        
        # İşlem süresini hesapla
        duration = time.time() - start_time
        
        # Yanıt bilgilerini hazırla
        response_data = {
            'status_code': response.status_code,
            'duration': f"{duration:.3f}s",
            'content_type': response.get('Content-Type', ''),
            'content_length': response.get('Content-Length', ''),
        }
        
        # Yanıt gövdesini almaya çalış (JSON ise)
        if hasattr(response, 'data') and response.status_code != 204:
            try:
                # Hassas alanları maskele
                response_body = response.data.copy() if hasattr(response.data, 'copy') else response.data
                if isinstance(response_body, dict):
                    for field in self.sensitive_fields:
                        if field in response_body:
                            response_body[field] = '******'
                response_data['body'] = response_body
            except:
                response_data['body'] = '[Unable to process response body]'
        
        # Log seviyesini durum koduna göre belirle
        if 200 <= response.status_code < 400:
            logger.info(f"API Response: {json.dumps(response_data, default=str)}")
        else:
            logger.warning(f"API Response: {json.dumps(response_data, default=str)}")
            
        return response
    
    def get_client_ip(self, request):
        """İstemci IP adresini alır."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip