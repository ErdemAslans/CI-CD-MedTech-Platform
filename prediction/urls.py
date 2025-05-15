from django.urls import path
from . import views

app_name = 'prediction'

urlpatterns = [
    # Vaka yönetimi URL'leri
    path('cases/', views.case_list, name='case_list'),
    path('cases/new/', views.case_create, name='case_create'),
    path('cases/<str:case_id>/', views.case_detail, name='case_detail'),
    path('cases/<str:case_id>/edit/', views.case_edit, name='case_edit'),
    path('cases/<str:case_id>/delete/', views.case_delete, name='case_delete'),
    
    # Görüntü yönetimi URL'leri
    path('cases/<str:case_id>/images/', views.image_list, name='image_list'),
    path('cases/<str:case_id>/images/upload/', views.image_upload, name='image_upload'),
    path('cases/images/<str:image_id>/', views.image_detail, name='image_detail'),
    
    # Raporlar
    path('cases/<str:case_id>/report/', views.case_report, name='case_report'),
    
    # Tahmin işlemi URL'leri
    path('', views.prediction_home, name='home'),
    path('images/<str:image_id>/predict/', views.predict_image, name='predict_image'),
    path('results/<str:image_id>/', views.prediction_results, name='results'),
    
    # Grad-CAM görselleştirme
    path('visualize/<str:image_id>/', views.visualize_prediction, name='visualize'),
    
    # Toplu tahmin işlemleri
    path('batch/', views.batch_prediction, name='batch'),
    path('batch/results/', views.batch_results, name='batch_results'),
    
    # Model bilgileri
    path('model-info/', views.model_info, name='model_info'),
    path('images/<str:image_id>/analyze/', views.analyze_image, name='analyze_image'),
    
]