# dashboard/services/models.py
"""
Servis katmanı için veri modelleri ve transfer nesneleri
Bu sınıflar servisler arası ve view katmanıyla veri paylaşımı için kullanılır
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any


@dataclass
class AnalyticsResult:
    """Analitik sonuç transfer nesnesi"""
    success: bool
    data: Dict[str, Any]
    timestamp: datetime = datetime.now()
    message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Objeyi sözlüğe dönüştürür"""
        return {
            'success': self.success,
            'data': self.data,
            'timestamp': self.timestamp.isoformat(),
            'message': self.message
        }


@dataclass
class ReportConfig:
    """Rapor yapılandırması"""
    title: str
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    doctor_id: Optional[str] = None
    include_predictions: bool = True
    include_gradcam: bool = True
    format: str = 'pdf'
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReportConfig':
        """Sözlükten ReportConfig nesnesi oluşturur"""
        config = cls(
            title=data.get('title', 'Untitled Report'),
            description=data.get('description'),
            include_predictions=data.get('include_predictions', True),
            include_gradcam=data.get('include_gradcam', True),
            format=data.get('format', 'pdf')
        )
        
        # Tarih alanlarını işle
        if 'start_date' in data and data['start_date']:
            try:
                config.start_date = datetime.fromisoformat(data['start_date'])
            except (ValueError, TypeError):
                pass
                
        if 'end_date' in data and data['end_date']:
            try:
                config.end_date = datetime.fromisoformat(data['end_date'])
            except (ValueError, TypeError):
                pass
        
        # Doctor ID'yi ayarla
        config.doctor_id = data.get('doctor_id')
        
        return config


@dataclass
class PredictionMetrics:
    """Tahmin metriklerini temsil eden veri sınıfı"""
    class_name: str
    count: int
    percentage: float
    display_name: str
    color: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PredictionMetrics':
        """Sözlükten PredictionMetrics nesnesi oluşturur"""
        return cls(
            class_name=data.get('class_name', ''),
            count=data.get('count', 0),
            percentage=data.get('percentage', 0.0),
            display_name=data.get('display_name', ''),
            color=data.get('color', '#CCCCCC')
        )


@dataclass
class DashboardStats:
    """Dashboard istatistikleri için veri sınıfı"""
    total_cases: int = 0
    total_predictions: int = 0
    pending_cases: int = 0
    completed_cases: int = 0
    in_progress_cases: int = 0
    archived_cases: int = 0
    recent_activities: List[Dict[str, Any]] = None
    prediction_distribution: List[PredictionMetrics] = None
    
    def __post_init__(self):
        """Başlangıç değerleri ata"""
        if self.recent_activities is None:
            self.recent_activities = []
        if self.prediction_distribution is None:
            self.prediction_distribution = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Objeyi sözlüğe dönüştürür"""
        return {
            'total_cases': self.total_cases,
            'total_predictions': self.total_predictions,
            'cases_by_status': {
                'pending': self.pending_cases,
                'in_progress': self.in_progress_cases,
                'completed': self.completed_cases,
                'archived': self.archived_cases
            },
            'recent_activities': self.recent_activities,
            'prediction_distribution': [
                p.__dict__ for p in self.prediction_distribution
            ]
        }