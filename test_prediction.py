import os
import cv2
import numpy as np
import sys

# Django ayarlarını yükle
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from ml.predictor import LungCancerPredictor

# Samples dizinindeki test görüntülerini al
samples_dir = '/app/media/samples'
if os.path.exists(samples_dir):
    files = os.listdir(samples_dir)
    print(f'Samples dizinindeki dosyalar: {files}')
    
    if files:
        # İlk görüntüyü test için kullan
        test_img_path = os.path.join(samples_dir, files[0])
        print(f'Test için kullanılacak görüntü: {test_img_path}')
        
        # Görüntüyü yükle
        img = cv2.imread(test_img_path)
        if img is None:
            print(f'HATA: Görüntü yüklenemedi: {test_img_path}')
        else:
            print(f'Görüntü başarıyla yüklendi. Boyut: {img.shape}')
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Model ile tahmin yap
            try:
                print('Model yükleniyor...')
                predictor = LungCancerPredictor()
                print('Model yüklendi.')
                
                print('Tahmin yapılıyor...')
                prediction_result = predictor.predict(img)
                print(f'Tahmin sonucu: {prediction_result}')
                
                # Grad-CAM oluştur
                print('Grad-CAM oluşturuluyor...')
                cam_image = predictor.get_gradcam(img)
                print(f'Grad-CAM oluşturuldu mu? {cam_image is not None}')
                
                if cam_image is not None:
                    # Gradcam dizinini kontrol et
                    gradcam_dir = '/app/media/gradcam'
                    os.makedirs(gradcam_dir, exist_ok=True)
                    
                    # Kaydet
                    gradcam_path = os.path.join(gradcam_dir, 'test_cam.jpg')
                    print(f'Grad-CAM kaydediliyor: {gradcam_path}')
                    success = cv2.imwrite(gradcam_path, cv2.cvtColor(cam_image, cv2.COLOR_RGB2BGR))
                    print(f'Kayıt başarılı mı? {success}')
                    print(f'Dosya oluştu mu? {os.path.exists(gradcam_path)}')
                else:
                    print('Grad-CAM oluşturulamadı - Alternatif yöntem deneniyor...')
                    
                    # Alternatif görselleştirme (Matplotlib)
                    try:
                        import matplotlib.pyplot as plt
                        plt.figure(figsize=(6, 6))
                        plt.imshow(img)
                        plt.title(prediction_result['predicted_class_display'])
                        plt.axis('off')
                        
                        alt_path = os.path.join(gradcam_dir, 'alt_cam.jpg')
                        plt.savefig(alt_path, dpi=100, bbox_inches='tight')
                        plt.close()
                        
                        print(f'Alternatif görselleştirme oluşturuldu: {alt_path}')
                        print(f'Dosya oluştu mu? {os.path.exists(alt_path)}')
                    except Exception as e:
                        print(f'Alternatif görselleştirme hatası: {e}')
            
            except Exception as e:
                import traceback
                print(f'Tahmin sırasında hata: {e}')
                traceback.print_exc()
    else:
        print('Samples dizininde dosya bulunamadı!')
else:
    print('Samples dizini bulunamadı!')