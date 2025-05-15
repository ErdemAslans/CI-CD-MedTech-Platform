"""
Tahmin servis modülü.

Bu modül, ML modelini ve görüntü işleme hizmetlerini soyutlayan
yüksek seviyeli bir servis sağlar.
"""

import os
import time
import numpy as np
import cv2
from typing import Dict, List, Tuple, Union, Optional, Any
from django.conf import settings
import threading
import logging

from ml.predictor import LungCancerPredictor
from ml.utils.preprocessing import preprocess_histopathology_image
from ml.utils.postprocessing import process_raw_prediction, save_prediction_visualization

# Loglama ayarları
logger = logging.getLogger('lungvision.prediction')

# Thread-local depolama
_thread_local = threading.local()


class PredictionService:
    """
    Tahmin işlemlerini yöneten servis sınıfı.
    
    Bu sınıf, görüntü önişleme, model tahmini ve sonuç işlemeyi
    kapsayan yüksek seviyeli bir API sağlar.
    """
    
    # Sınıf değişkenleri
    class_names = ['lung_aca', 'lung_n', 'lung_scc']
    
    @classmethod
    def get_predictor(cls) -> LungCancerPredictor:
        """
        Thread-safe bir şekilde tahmin edici nesne döndürür.
        
        Her thread için bir LungCancerPredictor örneği oluşturur ve yeniden kullanır,
        böylece model belleğe birden fazla kez yüklenmez.
        
        Returns:
            LungCancerPredictor: Tahmin edici nesne
        """
        if not hasattr(_thread_local, 'predictor'):
            try:
                logger.info("Yeni LungCancerPredictor örneği oluşturuluyor")
                _thread_local.predictor = LungCancerPredictor()
            except Exception as e:
                logger.error(f"Predictor oluşturulurken hata: {str(e)}")
                raise
        
        return _thread_local.predictor
    
    @classmethod
    def predict_image(cls, image_path: str, generate_gradcam: bool = True) -> Dict[str, Any]:
        """
        Bir görüntü dosyası için tahmin yapar.
        
        Args:
            image_path: Görüntü dosyasının yolu
            generate_gradcam: Grad-CAM oluşturulsun mu
            
        Returns:
            Tahmin sonucu (yapılandırılmış sözlük)
            
        Raises:
            FileNotFoundError: Görüntü dosyası bulunamazsa
            ValueError: Görüntü dosyası okunamazsa
        """
        start_time = time.time()
        
        # Dosyanın varlığını kontrol et
        if not os.path.exists(image_path):
            error_msg = f"Görüntü dosyası bulunamadı: {image_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        # Görüntüyü yükle
        try:
            image = cv2.imread(image_path)
            if image is None:
                error_msg = f"Görüntü dosyası okunamadı: {image_path}"
                logger.error(error_msg)
                raise ValueError(error_msg)
                
            # BGR -> RGB dönüşümü
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        except Exception as e:
            error_msg = f"Görüntü yüklenirken hata: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Önişleme
        try:
            img_processed = preprocess_histopathology_image(
                image, 
                target_size=(300, 300),
                normalize=True,
                standardize=False,
                color_normalize=False
            )
        except Exception as e:
            error_msg = f"Görüntü önişlenirken hata: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Tahmin yap
        try:
            # Thread-safe predictor al
            predictor = cls.get_predictor()
            prediction_result = predictor.predict(img_processed)
        except Exception as e:
            error_msg = f"Tahmin yapılırken hata: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        # Grad-CAM oluştur
        gradcam_path = None
        try:
            if generate_gradcam:
                # Grad-CAM görüntüsü oluştur
                predictor = cls.get_predictor()
                cam_image = predictor.get_gradcam(img_processed)
                
                if cam_image is not None:
                    # Dosya adını hazırla
                    from datetime import datetime
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = os.path.basename(image_path)
                    name, ext = os.path.splitext(filename)
                    
                    gradcam_filename = f"gradcam_{name}_{timestamp}.jpg"
                    gradcam_dir = os.path.join(settings.MEDIA_ROOT, 'gradcam')
                    os.makedirs(gradcam_dir, exist_ok=True)
                    
                    gradcam_path = os.path.join('gradcam', gradcam_filename)
                    gradcam_full_path = os.path.join(settings.MEDIA_ROOT, gradcam_path)
                    
                    # Grad-CAM görüntüsünü kaydet
                    cv2.imwrite(gradcam_full_path, cv2.cvtColor(cam_image, cv2.COLOR_RGB2BGR))
        except Exception as e:
            logger.warning(f"Grad-CAM oluşturulurken hata: {str(e)}")
            # Grad-CAM oluşturma hatası kritik değil, devam et
        
        # İşlem süresini hesapla
        processing_time = time.time() - start_time
        
        # Tahmin sonucunu güncelle
        prediction_result['gradcam_path'] = gradcam_path
        prediction_result['processing_time'] = processing_time
        
        logger.info(f"Tahmin tamamlandı: {prediction_result['predicted_class']} "
                   f"({prediction_result['confidence']:.2%}) - {processing_time:.2f}s")
        
        return prediction_result
    
    @classmethod
    def predict_image_data(cls, image_data: np.ndarray, generate_gradcam: bool = True) -> Dict[str, Any]:
        """
        Bir numpy dizisi olarak verilen görüntü için tahmin yapar.
        
        Args:
            image_data: Görüntü verisi (numpy dizisi)
            generate_gradcam: Grad-CAM oluşturulsun mu
            
        Returns:
            Tahmin sonucu (yapılandırılmış sözlük)
        """
        start_time = time.time()
        
        # Görüntünün geçerliliğini kontrol et
        if image_data is None or image_data.size == 0:
            error_msg = "Geçersiz görüntü verisi"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # BGR -> RGB dönüşümü (gerekirse)
        if len(image_data.shape) == 3 and image_data.shape[2] == 3:
            if image_data[0, 0, 0] > image_data[0, 0, 2]:  # BGR kontrolü (kaba tahmin)
                image_data = cv2.cvtColor(image_data, cv2.COLOR_BGR2RGB)
        
        # Önişleme
        try:
            img_processed = preprocess_histopathology_image(
                image_data, 
                target_size=(300, 300),
                normalize=True,
                standardize=False,
                color_normalize=False
            )
        except Exception as e:
            error_msg = f"Görüntü önişlenirken hata: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Tahmin yap
        try:
            predictor = cls.get_predictor()
            prediction_result = predictor.predict(img_processed)
        except Exception as e:
            error_msg = f"Tahmin yapılırken hata: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        # Grad-CAM oluştur
        cam_image = None
        if generate_gradcam:
            try:
                predictor = cls.get_predictor()
                cam_image = predictor.get_gradcam(img_processed)
            except Exception as e:
                logger.warning(f"Grad-CAM oluşturulurken hata: {str(e)}")
        
        # İşlem süresini hesapla
        processing_time = time.time() - start_time
        
        # Tahmin sonucunu güncelle
        prediction_result['gradcam_image'] = cam_image
        prediction_result['processing_time'] = processing_time
        
        logger.info(f"Tahmin tamamlandı: {prediction_result['predicted_class']} "
                   f"({prediction_result['confidence']:.2%}) - {processing_time:.2f}s")
        
        return prediction_result
    
    @classmethod
    def generate_visualization(cls, 
                             image_path: str, 
                             prediction_result: Dict[str, Any],
                             output_dir: str = None) -> str:
        """
        Tahmin sonucunun görselleştirilmiş bir versiyonunu oluşturur.
        
        Args:
            image_path: Görüntü dosyasının yolu
            prediction_result: Tahmin sonucu
            output_dir: Çıktı dizini (None ise, settings.MEDIA_ROOT/prediction_results kullanılır)
            
        Returns:
            Oluşturulan görselleştirme dosyasının yolu
        """
        # Görüntüyü yükle
        image = cv2.imread(image_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Grad-CAM görüntüsünü yükle (varsa)
        gradcam_image = None
        if 'gradcam_path' in prediction_result and prediction_result['gradcam_path']:
            gradcam_path = os.path.join(settings.MEDIA_ROOT, prediction_result['gradcam_path'])
            if os.path.exists(gradcam_path):
                gradcam_image = cv2.imread(gradcam_path)
                gradcam_image = cv2.cvtColor(gradcam_image, cv2.COLOR_BGR2RGB)
        elif 'gradcam_image' in prediction_result and prediction_result['gradcam_image'] is not None:
            gradcam_image = prediction_result['gradcam_image']
        
        # Görselleştirmeyi oluştur ve kaydet
        return save_prediction_visualization(
            image, 
            prediction_result, 
            gradcam_image, 
            output_dir
        )