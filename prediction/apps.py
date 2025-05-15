"""
Prediction uygulaması yapılandırması.
Bu modül, Prediction Django uygulamasının yapılandırmasını tanımlar.
Histopatolojik görüntülerin tahmini ve işlenmesi için gerekli bileşenleri içerir.
"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
import os
from django.conf import settings  # Bu satırı ekleyin - settings modülünü import edin

class PredictionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'prediction'
   
    def ready(self):
        """
        Uygulama başlatıldığında çalışacak kod.
        Model dizinlerini kontrol eder ve gerekli servisleri başlatır.
        """
        # ML model dizinini kontrol et
        model_dir = os.path.dirname(settings.ML_MODEL_PATH)
        if not os.path.exists(model_dir):
            os.makedirs(model_dir, exist_ok=True)
            print(f"Model dizini oluşturuldu: {model_dir}")
       
        # Grad-CAM dizinini kontrol et
        gradcam_dir = os.path.join(settings.MEDIA_ROOT, 'gradcam')
        if not os.path.exists(gradcam_dir):
            os.makedirs(gradcam_dir, exist_ok=True)
            print(f"Grad-CAM dizini oluşturuldu: {gradcam_dir}")
       
        # Tahmin sonuçları dizinini kontrol et
        prediction_results_dir = os.path.join(settings.MEDIA_ROOT, 'prediction_results')  
        if not os.path.exists(prediction_results_dir):
            os.makedirs(prediction_results_dir, exist_ok=True)
            print(f"Tahmin sonuçları dizini oluşturuldu: {prediction_results_dir}")
           
        # Model var mı kontrol et
        if not os.path.exists(settings.ML_MODEL_PATH):
            print(f"UYARI: Model dosyası bulunamadı: {settings.ML_MODEL_PATH}")
            print("Modeli uygun konuma yerleştirdiğinizden emin olun.")
        else:
            print(f"Model dosyası bulundu: {settings.ML_MODEL_PATH}")
           
        # Gerekli diğer başlatma işlemleri
        try:
            # TensorFlow uyarılarını bastır
            import tensorflow as tf
            tf.get_logger().setLevel('ERROR')
            print("TensorFlow başarıyla yüklendi ve yapılandırıldı.")
        except ImportError:
            print("TensorFlow yüklü değil veya yapılandırılamadı.")
           
        # MongoDB koleksiyonlarını ve indekslerini hazırla (isteğe bağlı)
        self._setup_mongodb_collections()
   
    def _setup_mongodb_collections(self):  # Metod adını düzelttim - * yerine _ kullanın
        """
        MongoDB koleksiyonlarını ve indekslerini hazırlar.
        """
        try:
            from core.db import MongoManager
            mongo = MongoManager()
           
            if mongo.db is not None:
                # patient_cases koleksiyonu için indeksler
                mongo.db.patient_cases.create_index([("uuid", 1)], unique=True)
                mongo.db.patient_cases.create_index([("doctor_id", 1)])
                mongo.db.patient_cases.create_index([("created_at", -1)])
               
                # image_samples koleksiyonu için indeksler
                mongo.db.image_samples.create_index([("uuid", 1)], unique=True)
                mongo.db.image_samples.create_index([("case_id", 1)])
                mongo.db.image_samples.create_index([("uploaded_at", -1)])
               
                print(f"MongoDB indeksleri başarıyla oluşturuldu")
        except Exception as e:
            print(f"MongoDB indeksleri oluşturulurken hata: {e}")