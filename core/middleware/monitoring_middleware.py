"""
Monitoring Middleware

Bu middleware, sistem performansını ve isteklerin durumunu izlemek için kullanılır.
Yüksek işlem süreleri, bellek kullanımı veya hata oranları tespit edilebilir.
"""
import time
import psutil
import logging
from django.conf import settings
from django.http import JsonResponse

# Monitoring logger'ı
logger = logging.getLogger('lungvision.monitoring')

class PerformanceMonitoringMiddleware:
    """
    Sistem performansını ve istek performansını izleyen middleware.
    
    Bu middleware şunları ölçer ve loglar:
    - İstek işleme süresi
    - Bellek kullanımı
    - CPU kullanımı
    - İstek başarı/başarısızlık durumu
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.slow_threshold = getattr(settings, 'PERFORMANCE_SLOW_THRESHOLD', 1.0)  # 1 saniye
        self.memory_threshold = getattr(settings, 'PERFORMANCE_MEMORY_THRESHOLD', 90.0)  # %90
        self.cpu_threshold = getattr(settings, 'PERFORMANCE_CPU_THRESHOLD', 90.0)  # %90
        
    def __call__(self, request):
        # İstek zamanını kaydet
        start_time = time.time()
        
        # Sistem kaynaklarını başlangıçta ölç
        start_memory = psutil.virtual_memory().percent
        start_cpu = psutil.cpu_percent()
        
        # İsteği işle
        response = self.get_response(request)
        
        # İşlem süresini hesapla
        duration = time.time() - start_time
        
        # Sadece yavaş istekleri, API isteklerini veya hataları logla
        if (duration > self.slow_threshold or
            request.path.startswith('/api/') or
            response.status_code >= 400):
            
            # Sistem kaynaklarını sonunda ölç
            end_memory = psutil.virtual_memory().percent
            end_cpu = psutil.cpu_percent()
            
            # Performans metriklerini hazırla
            metrics = {
                'path': request.path,
                'method': request.method,
                'status_code': response.status_code,
                'duration': f"{duration:.3f}s",
                'memory_usage': f"{end_memory:.1f}%",
                'memory_change': f"{end_memory - start_memory:.1f}%",
                'cpu_usage': f"{end_cpu:.1f}%",
                'cpu_change': f"{end_cpu - start_cpu:.1f}%",
            }
            
            # Duruma göre log seviyesini belirle
            if response.status_code >= 500:
                logger.error(f"Server Error: {metrics}")
            elif response.status_code >= 400:
                logger.warning(f"Client Error: {metrics}")
            elif duration > self.slow_threshold:
                logger.warning(f"Slow Request: {metrics}")
            elif end_memory > self.memory_threshold:
                logger.warning(f"High Memory Usage: {metrics}")
            elif end_cpu > self.cpu_threshold:
                logger.warning(f"High CPU Usage: {metrics}")
            else:
                logger.info(f"Request Metrics: {metrics}")
                
        return response

class HealthCheckMiddleware:
    """
    Sistem sağlık kontrolü endpoint'i sağlayan middleware.
    
    /health/ endpoint'ine yapılan isteklere yanıt verir ve
    sistemin genel durumu hakkında bilgi sağlar.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.health_endpoint = '/health/'
        
    def __call__(self, request):
        # Sağlık kontrolü endpoint'ini kontrol et
        if request.path == self.health_endpoint:
            health_info = self.get_health_info()
            return JsonResponse(health_info)
            
        return self.get_response(request)
        
    def get_health_info(self):
        """Sistem sağlık bilgilerini toplar"""
        # MongoDB bağlantısını kontrol et
        from core.db import MongoManager
        mongo = MongoManager()
        db_status = "UP" if mongo.db is not None else "DOWN"
        
        # TensorFlow modelini kontrol et
        import os
        from django.conf import settings
        model_status = "UP" if os.path.exists(settings.MODEL_PATH) else "DOWN"
        
        # Sistem kaynaklarını kontrol et
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'status': 'UP' if db_status == 'UP' and model_status == 'UP' else 'DEGRADED',
            'timestamp': time.time(),
            'components': {
                'database': {
                    'status': db_status,
                    'type': 'MongoDB'
                },
                'ml_model': {
                    'status': model_status,
                    'path': settings.MODEL_PATH
                }
            },
            'system': {
                'memory_used': f"{memory.percent:.1f}%",
                'disk_used': f"{disk.percent:.1f}%",
                'cpu_used': f"{psutil.cpu_percent():.1f}%"
            }
        }