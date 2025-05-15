"""
Dashboard uygulaması yapılandırması.

Bu modül, Dashboard Django uygulamasının yapılandırmasını tanımlar.
Analitik görselleştirmeleri ve raporlama işlevlerini içerir.
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DashboardConfig(AppConfig):
    """
    Dashboard uygulaması yapılandırma sınıfı.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashboard'
    verbose_name = _('Dashboard')
    
    def ready(self):
        """
        Uygulama hazır olduğunda yapılacak işlemler.
        
        Bu metodda, analitik servisleri ve raporlama sistemlerini 
        başlatmak için gereken kodlar bulunur.
        """
        # Signal handlers'ları içe aktar
        
        # Dashboard görselleştirme türlerini tanımla
        from django.conf import settings
        
        # Dashboard widget türleri
        if not hasattr(settings, 'DASHBOARD_WIDGET_TYPES'):
            settings.DASHBOARD_WIDGET_TYPES = {
                'bar_chart': _('Bar Grafiği'),
                'line_chart': _('Çizgi Grafiği'),
                'pie_chart': _('Pasta Grafiği'),
                'stat_card': _('İstatistik Kartı'),
                'table': _('Tablo'),
                'heatmap': _('Isı Haritası')
            }
            
        # Dashboard rapor formatları
        if not hasattr(settings, 'DASHBOARD_REPORT_FORMATS'):
            settings.DASHBOARD_REPORT_FORMATS = {
                'pdf': _('PDF'),
                'csv': _('CSV'),
                'json': _('JSON')
            }