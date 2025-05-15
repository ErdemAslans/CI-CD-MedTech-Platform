# gradcam_debug.py
import os
import cv2
import numpy as np
import tensorflow as tf
from django.conf import settings
from ml.predictor import LungCancerPredictor

def test_gradcam():
    """
    Grad-CAM oluşturma ve kaydetme işlemini test eder
    """
    # Test görseli yükle (varsa bir örnek görüntü kullanın)
    sample_path = os.path.join(settings.MEDIA_ROOT, 'samples', 'sample_image_001.jpg')
    
    # Eğer örnek yoksa basit bir test görüntüsü oluştur
    if not os.path.exists(sample_path):
        print(f"Örnek görüntü bulunamadı: {sample_path}")
        print("Test için yeni bir görüntü oluşturuluyor...")
        
        test_img = np.ones((300, 300, 3), dtype=np.uint8) * 255  # Beyaz bir kare
        cv2.circle(test_img, (150, 150), 100, (0, 0, 255), -1)   # Kırmızı daire
        
        # Test görüntüsünü kaydet
        samples_dir = os.path.join(settings.MEDIA_ROOT, 'samples')
        os.makedirs(samples_dir, exist_ok=True)
        cv2.imwrite(sample_path, test_img)
        print(f"Test görüntüsü oluşturuldu: {sample_path}")
    
    # Görüntüyü yükle
    image = cv2.imread(sample_path)
    if image is None:
        print(f"Hata: Görüntü okunamadı: {sample_path}")
        return
    
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    try:
        # Grad-CAM oluştur
        predictor = LungCancerPredictor()
        cam_image = predictor.get_gradcam(image)
        
        if cam_image is None:
            print("Hata: Grad-CAM görüntüsü oluşturulamadı")
            return
        
        # Grad-CAM'i kaydet
        timestamp = "test"
        gradcam_filename = f"gradcam_test_{timestamp}.jpg"
        gradcam_rel_path = f"gradcam/{gradcam_filename}"
        gradcam_abs_path = os.path.join(settings.MEDIA_ROOT, gradcam_rel_path)
        
        # Dizin yoksa oluştur
        print(f"Grad-CAM dizini oluşturuluyor: {os.path.dirname(gradcam_abs_path)}")
        os.makedirs(os.path.dirname(gradcam_abs_path), exist_ok=True)
        
        # Kaydet
        print(f"Grad-CAM görüntüsü kaydediliyor: {gradcam_abs_path}")
        success = cv2.imwrite(gradcam_abs_path, cv2.cvtColor(cam_image, cv2.COLOR_RGB2BGR))
        
        if not success:
            print(f"Hata: Grad-CAM görüntüsü kaydedilemedi")
            return
        
        # Dosya kontrolü
        if os.path.exists(gradcam_abs_path):
            print(f"Başarılı: Grad-CAM görüntüsü oluşturuldu: {gradcam_abs_path}")
            print(f"Dosya boyutu: {os.path.getsize(gradcam_abs_path)} bytes")
            
            # URL oluştur
            from django.contrib.sites.shortcuts import get_current_site
            from django.http import HttpRequest
            
            # Django uygulamasındaysanız bu URL'yi kullanabilirsiniz
            media_url = settings.MEDIA_URL
            gradcam_url = f"{media_url}{gradcam_rel_path}"
            print(f"Grad-CAM URL: {gradcam_url}")
            
            return gradcam_rel_path
        else:
            print(f"Hata: Grad-CAM görüntüsü bulunamadı: {gradcam_abs_path}")
            
    except Exception as e:
        print(f"Hata: Grad-CAM işlemi sırasında bir hata oluştu: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Django ortamını yükle
    import os
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    
    # Testi çalıştır
    test_gradcam()