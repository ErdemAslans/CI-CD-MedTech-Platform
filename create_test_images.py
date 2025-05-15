import numpy as np
import cv2
import os

# Samples dizinini doğrudan belirt
samples_dir = '/app/media/samples'
os.makedirs(samples_dir, exist_ok=True)

# Test görüntüsü oluştur
img = np.ones((300, 300, 3), dtype=np.uint8) * 255  # Beyaz bir kare
cv2.circle(img, (150, 150), 100, (0, 0, 255), -1)    # Kırmızı daire

# Kaydet
img_path = os.path.join(samples_dir, 'test_sample.jpg')
cv2.imwrite(img_path, img)
print(f'Test görüntüsü oluşturuldu: {img_path}')
print(f'Dosya var mı: {os.path.exists(img_path)}')
print(f'Dosya boyutu: {os.path.getsize(img_path) if os.path.exists(img_path) else 0} bayt')

# İkinci basit test görüntüsü
img2 = np.ones((300, 300, 3), dtype=np.uint8) * 200  # Açık gri bir kare
cv2.rectangle(img2, (50, 50), (250, 250), (0, 255, 0), -1)  # Yeşil dikdörtgen

# Kaydet
img2_path = os.path.join(samples_dir, 'test_sample2.jpg')
cv2.imwrite(img2_path, img2)
print(f'İkinci test görüntüsü oluşturuldu: {img2_path}')
print(f'Dosya var mı: {os.path.exists(img2_path)}')
print(f'Dosya boyutu: {os.path.getsize(img2_path) if os.path.exists(img2_path) else 0} bayt')

# Dizindeki tüm dosyaları listele
files = os.listdir(samples_dir)
print(f'Samples dizinindeki dosyalar: {files}')