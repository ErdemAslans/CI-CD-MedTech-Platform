from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from core.db import MongoManager
from dashboard.services.analytics_service import AnalyticsService

@login_required
def dashboard_home(request):
    """Dashboard ana sayfası görünümü"""
    # MongoDB'ye bağlan
    mongo = MongoManager()
    if mongo.db is None:
        return render(request, 'dashboard/index.html', {'error': "Veritabanı bağlantısı kurulamadı"})
    
    # Analytics servisi başlat
    analytics = AnalyticsService()
    
    # İstatistik verilerini al
    stats = {}
    
    # Vaka ve tahmin sayılarını al
    total_cases = mongo.db.patient_cases.count_documents({})
    
    # Doktora özel veriler
    if request.user.user_type == 'doctor':
        total_cases = mongo.db.patient_cases.count_documents({"doctor_id": str(request.user.id)})
    
    # Tahmini sayısını hesapla
    pipeline = [
        {"$project": {"prediction_count": {"$size": {"$ifNull": ["$predictions", []]}}}}
    ]
    result = list(mongo.db.image_samples.aggregate(pipeline))
    total_predictions = sum(doc.get('prediction_count', 0) for doc in result)
    
    # Tahmin dağılımını al
    prediction_distribution = analytics.get_prediction_distribution(
        doctor_id=request.user.id if request.user.user_type == 'doctor' else None
    )
    
    # Son aktiviteleri al
    recent_activities = analytics.get_recent_activity(
        limit=5, 
        user_id=request.user.id if request.user.user_type == 'doctor' else None
    )
    
    # İstatistikleri hazırla
    stats = {
        'total_cases': total_cases,
        'total_predictions': total_predictions,
        'prediction_distribution': prediction_distribution,
        'recent_activities': recent_activities
    }
    
    return render(request, 'dashboard/index.html', {'stats': stats})