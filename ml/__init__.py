"""
ML Modülleri için başlatma dosyası
"""

# alt modüllerin ve sınıfların dışa aktarılması
from ml.predictor import LungCancerPredictor

__all__ = [
    'LungCancerPredictor',
]