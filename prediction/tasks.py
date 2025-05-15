"""
Celery görev modülü.

Bu modül, akciğer kanseri tahmini için arka plan görevlerini tanımlar.
Celery kullanıldığında, tahminler asenkron olarak işlenir.
"""

from celery import shared_task
import logging
import cv2
import os
from django.conf import settings
from datetime import datetime
from bson import ObjectId

logger = logging.getLogger('lungvision.tasks')

@shared_task
def process_prediction(image_id, generate_gradcam=True, user_id=None):
    """
    Bir görüntü için tahmin işlemini arka planda gerçekleştirir.
    
    Args:
        image_id: MongoDB görüntü ID'si
        generate_gradcam: Grad-CAM oluşturulsun mu
        user_id: İşlemi başlatan kullanıcı ID'si
    
    Returns:
        dict: İşlem sonucu
    """
    from core.db import MongoManager
    
    logger.info(f"Tahmin işlemi başlatıldı: {image_id}, kullanıcı: {user_id}")
    
    try:
        # MongoDB bağlantısı
        mongo = MongoManager()
        
        # Görüntü bilgilerini al
        from prediction.models import ImageSampleRepository
        image_repo = ImageSampleRepository(mongo.db)
        
        image = image_repo.get_by_id(image_id)
        if not image:
            logger.error(f"Görüntü bulunamadı: {image_id}")
            return {'status': 'error', 'message': 'Görüntü bulunamadı'}
        
        # Görüntü yolunu al
        image_path = image.get('image_path')
        if not image_path:
            logger.error(f"Görüntü yolu bulunamadı: {image_id}")
            return {'status': 'error', 'message': 'Görüntü yolu bulunamadı'}
        
        # Tam dosya yolu
        full_path = os.path.join(settings.MEDIA_ROOT, image_path)
        if not os.path.exists(full_path):
            logger.error(f"Görüntü dosyası bulunamadı: {full_path}")
            return {'status': 'error', 'message': 'Görüntü dosyası bulunamadı'}
        
        # Görüntüyü yükle
        img = cv2.imread(full_path)
        if img is None:
            logger.error(f"Görüntü yüklenemedi: {full_path}")
            return {'status': 'error', 'message': 'Görüntü yüklenemedi'}
        
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Model yükle ve tahmin yap
        logger.debug(f"Model yükleniyor: {image_id}")
        from ml.predictor import LungCancerPredictor
        predictor = LungCancerPredictor()
        
        logger.debug(f"Tahmin yapılıyor: {image_id}")
        prediction_result = predictor.predict(img)
        
        # Grad-CAM oluştur
        gradcam_path = None
        if generate_gradcam:
            try:
                logger.debug(f"Grad-CAM oluşturuluyor: {image_id}")
                
                # Grad-CAM dizinini kontrol et
                gradcam_dir = os.path.join(settings.MEDIA_ROOT, 'gradcam')
                if not os.path.exists(gradcam_dir):
                    os.makedirs(gradcam_dir, exist_ok=True)
                
                # Grad-CAM görüntüsü oluştur
                cam_image = predictor.get_gradcam(img)
                
                if cam_image is not None:
                    # Dosya adını oluştur
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    gradcam_filename = f"gradcam_{image_id}_{timestamp}.jpg"
                    gradcam_rel_path = f"gradcam/{gradcam_filename}"
                    gradcam_abs_path = os.path.join(settings.MEDIA_ROOT, gradcam_rel_path)
                    
                    # Kaydet
                    cv2.imwrite(gradcam_abs_path, cv2.cvtColor(cam_image, cv2.COLOR_RGB2BGR))
                    
                    # Dosya oluştu mu kontrol et
                    if os.path.exists(gradcam_abs_path):
                        gradcam_path = gradcam_rel_path
                        logger.debug(f"Grad-CAM kaydedildi: {gradcam_rel_path}")
                    else:
                        logger.warning(f"Grad-CAM kaydedilemedi: {gradcam_abs_path}")
            except Exception as e:
                logger.error(f"Grad-CAM oluşturma hatası: {str(e)}")
        
        # Tahmin sonucunu güncelle
        prediction_result['gradcam_path'] = gradcam_path
        prediction_result['prediction_time'] = datetime.now().strftime('%d.%m.%Y %H:%M')
        prediction_result['processed_by_task'] = True
        
        # Tahmin sonucunu veritabanına ekle
        logger.debug(f"Tahmin sonucu veritabanına kaydediliyor: {image_id}")
        success = image_repo.add_prediction(image_id, prediction_result)
        
        if not success:
            logger.error(f"Tahmin sonucu veritabanına kaydedilemedi: {image_id}")
            return {'status': 'error', 'message': 'Tahmin sonucu veritabanına kaydedilemedi'}
        
        logger.info(f"Tahmin işlemi tamamlandı: {image_id}, sınıf: {prediction_result['predicted_class']}")
        
        return {
            'status': 'success',
            'message': 'Tahmin işlemi tamamlandı',
            'image_id': image_id,
            'predicted_class': prediction_result['predicted_class'],
            'confidence': prediction_result['confidence']
        }
    
    except Exception as e:
        import traceback
        logger.error(f"Tahmin işlemi hatası: {str(e)}")
        logger.error(traceback.format_exc())
        
        return {
            'status': 'error',
            'message': f'Tahmin işlemi hatası: {str(e)}',
            'image_id': image_id
        }