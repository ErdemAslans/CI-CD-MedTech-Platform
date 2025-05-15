# test_ml.py
import os
import sys
import django

# Django projenizin ayarlarını yükle
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from ml.predictor import LungCancerPredictor
import cv2

def test_model():
    print(f"BASE_DIR: {settings.BASE_DIR}")
    print(f"Model yolu: {settings.MODEL_PATH}")
    print(f"Model dosyası var mı: {os.path.exists(settings.MODEL_PATH)}")
    
    # Eğer dosya yoksa doğru yolu bulmaya çalışalım
    if not os.path.exists(settings.MODEL_PATH):
        possible_path = os.path.join(os.getcwd(), 'ml', 'models', 'EfficientNetV2L_supreme.keras')
        print(f"Alternatif yol kontrolü: {possible_path}")
        print(f"Alternatif yol var mı: {os.path.exists(possible_path)}")
    
    try:
        # Model yükle
        predictor = LungCancerPredictor()
        print("Model başarıyla yüklendi!")
        
        # Test görüntüsü yükle
        test_image_path = os.path.join(settings.MEDIA_ROOT, 'samples', 'test_image.jpg')
        if os.path.exists(test_image_path):
            image = cv2.imread(test_image_path)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Tahmin yap
            prediction = predictor.predict(image)
            print(f"Tahmin sonucu: {prediction}")
            print("Test başarılı!")
        else:
            print(f"Test görüntüsü bulunamadı: {test_image_path}")
    
    except Exception as e:
        print(f"Model yükleme veya tahmin hatası: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_model()