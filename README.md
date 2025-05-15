# LungVision AI 🫁🔍

![LungVision AI Logo](https://github.com/ErdemAslans/lungvision-ai-with-DevOPS/raw/main/media/samples/20250515_120616_b639e281.jpeg)

## Akciğer Kanseri Tespiti için Yapay Zeka Destekli Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![Django Version](https://img.shields.io/badge/django-4.2-green.svg)](https://www.djangoproject.com/)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://www.docker.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-5.0-green.svg)](https://www.mongodb.com/)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.13-orange.svg)](https://www.tensorflow.org/)

LungVision AI, patologları ve bilim insanlarını güçlü derin öğrenme yapay zeka ve bulut tabanlı teknoloji ile donatır. Akciğer kanseri tanısında %95+ doğruluk oranı sunan platformumuz, büyük ve karmaşık tıbbi görüntüleri analiz etmenin hızını, doğruluğunu ve tutarlılığını artırmayı amaçlar.

## 🌟 Özellikler

- 🔍 **Yüksek Doğruluk**: %95+ doğruluk oranıyla güvenilir tanı desteği
- ⚡ **Hızlı Sonuç**: Saniyeler içinde tahmin sonuçları (ortalama 2.3 saniye)
- 📊 **Ayrıntılı Analiz**: Grad-CAM görselleştirmeleriyle kararların açıklanabilirliği
- 📱 **Modern Arayüz**: Tailwind CSS ile geliştirilmiş duyarlı ve kullanıcı dostu arayüz
- 🔄 **DevOps Entegrasyonu**: CI/CD pipeline, Docker konteynerizasyonu ve otomatik deployment
- 🛠️ **Yüksek Skalabilite**: Mikroservis mimarisi ve Docker konteynerizasyonu
- 🔒 **Güvenli**: Hassas tıbbi veriler için HIPAA uyumlu güvenlik

## 📸 Görsel Örnekler

<div align="center">
  <img src="https://github.com/ErdemAslans/lungvision-ai-with-DevOPS/raw/main/media/samples/20250515_121111_b466aa52.jpeg" alt="LungVision AI Örnek Görüntü 1" width="400"/>
  <p><em>Akciğer dokusunun EfficientNetV2L modeli ile analizi</em></p>
</div>

<div align="center">
  <img src="https://github.com/ErdemAslans/lungvision-ai-with-DevOPS/raw/main/media/samples/20250515_133124_133a717b.jpeg" alt="LungVision AI Grad-CAM Görselleştirmesi" width="400"/>
  <p><em>Grad-CAM ısı haritası ile modelin odaklandığı bölgeler</em></p>
</div>

## 🛠️ Teknoloji Yığını

### 💻 Frontend
- **Framework**: Django Templates
- **CSS**: Tailwind CSS
- **JavaScript**: Vanilla JS

### 🖥️ Backend
- **Framework**: Django 4.2
- **API**: Django REST Framework
- **Python Sürümü**: 3.9+

### 🧠 Yapay Zeka
- **Framework**: TensorFlow
- **Model**: EfficientNetV2L
- **Görselleştirme**: Grad-CAM

### 🗄️ Veritabanı
- **Belge Deposu**: MongoDB 5.0
- **Veri Tabanı**: SQLite (Geliştirme) / PostgreSQL (Üretim)

### 🚢 DevOps
- **Konteynerizasyon**: Docker & Docker Compose
- **CI/CD**: GitHub Actions
- **Web Sunucusu**: Nginx
- **İzleme**: Prometheus & Grafana

## 🗃️ Proje Yapısı

```
lungvision-ai-with-DevOPS/
├── config/                # Django yapılandırma
├── core/                  # Çekirdek uygulama
│   ├── middleware/        # Özel middleware (logging, monitoring)
│   └── utils/             # Yardımcı fonksiyonlar
├── dashboard/             # Dashboard uygulaması
│   └── services/          # İş mantığı servisleri
├── prediction/            # Tahmin uygulaması ve API
│   └── services/          # Tahmin servisleri
├── ml/                    # Makine öğrenmesi modelleri
│   └── models/            # Eğitilmiş modeller
├── templates/             # HTML şablonları
│   ├── components/        # Yeniden kullanılabilir bileşenler
│   ├── dashboard/         # Dashboard şablonları
│   └── prediction/        # Tahmin şablonları
├── users/                 # Kullanıcı yönetimi
├── docker/                # Docker yapılandırmaları
│   ├── django/            # Django konteyner yapılandırması
│   ├── mongodb/           # MongoDB konteyner yapılandırması
│   └── nginx/             # Nginx yapılandırması
├── media/                 # Kullanıcı yüklenen medya dosyaları
│   ├── samples/           # Örnek görüntüler
│   └── gradcam/           # Grad-CAM görselleştirmeleri
├── static/                # Statik dosyalar
├── .github/workflows/     # GitHub Actions CI/CD yapılandırması
├── docker-compose.yml     # Docker Compose yapılandırması
├── Dockerfile             # Ana Dockerfile
└── README.md              # Proje belgesi
```

## 🚀 Kurulum

### 🐳 Docker ile (Tavsiye Edilen)

Docker kullanarak tüm sistem bağımlılıklarını kolayca kurabilir ve uygulamayı çalıştırabilirsiniz:

```bash
# Repo'yu klonlayın
git clone https://github.com/ErdemAslans/lungvision-ai-with-DevOPS.git
cd lungvision-ai-with-DevOPS

# .env dosyasını oluşturun
cp .env.example .env
# .env dosyasını düzenleyin ve gerekli değişkenleri ayarlayın

# Docker Compose ile çalıştırın
docker-compose up -d

# Web tarayıcısında açın
# http://localhost:8000
```

### 🐍 Manuel Kurulum (Geliştirme İçin)

```bash
# Repo'yu klonlayın
git clone https://github.com/ErdemAslans/lungvision-ai-with-DevOPS.git
cd lungvision-ai-with-DevOPS

# Sanal ortam oluşturun ve etkinleştirin
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Bağımlılıkları yükleyin
pip install -r requirements.txt

# .env dosyasını oluşturun
cp .env.example .env
# .env dosyasını düzenleyin ve gerekli değişkenleri ayarlayın

# Veritabanı migrasyonlarını uygulayın
python manage.py migrate

# Geliştirme sunucusunu başlatın
python manage.py runserver

# Web tarayıcısında açın
# http://127.0.0.1:8000
```

## 📝 Yapılandırma

Django için `.env` dosyasında aşağıdaki çevre değişkenlerini yapılandırabilirsiniz:

```
# Django Yapılandırması
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# MongoDB Yapılandırması
MONGO_HOST=mongodb
MONGO_PORT=27017
MONGO_DB=lungvision_db
MONGO_USER=admin
MONGO_PASSWORD=password
MONGO_URI=mongodb://admin:password@mongodb:27017/lungvision_db?authSource=admin

# AWS S3 Yapılandırması (isteğe bağlı)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1
```

## 📊 AI Model Performansı

LungVision AI platformu, akciğer kanseri tespiti için EfficientNetV2L modelini kullanır:

| Metrik           | Değer  |
|------------------|--------|
| Doğruluk (Accuracy) | %95.3  |
| Hassasiyet (Sensitivity) | %94.2  |
| Özgüllük (Specificity) | %96.1  |
| F1 Skoru         | %95.0  |
| AUC-ROC          | 0.982  |
| Ortalama İşlem Süresi | 2.3s   |

Model, şu sınıfları tespit edebilir:
- **lung_aca**: Akciğer Adenokarsinomu
- **lung_scc**: Akciğer Skuamöz Hücreli Karsinomu
- **lung_n**: Normal Akciğer Dokusu

## 📋 İş Akışı

1. **Görüntü Yükleme**: Histopatoloji görüntülerini platforma yükleyin
2. **AI Analizi**: Yapay zeka modelimiz görüntüleri EfficientNetV2L ile analiz eder
3. **Sonuçları İnceleme**: Detaylı raporlar ve Grad-CAM ısı haritalarını inceleyin
4. **Rapor Paylaşımı**: Sonuçları diğer uzmanlarla paylaşın veya hasta kayıtlarına ekleyin

## 🔒 Güvenlik

LungVision AI, hasta verilerinin gizliliğini ve güvenliğini sağlamak için çeşitli önlemleri uygular:

- HIPAA uyumlu veri depolama ve işleme
- End-to-end şifreleme
- Rol tabanlı erişim kontrolleri
- Kapsamlı loglama ve izleme
- Güvenli Docker konteynerizasyonu

## 🧪 Test Etme

```bash
# Unit testleri çalıştırın
python manage.py test

# Belirli bir uygulamayı test edin
python manage.py test prediction

# Test kapsamını kontrol edin
coverage run --source='.' manage.py test
coverage report
```

## 📄 Lisans

Bu proje MIT Lisansı ile lisanslanmıştır. Daha fazla bilgi için [LICENSE](LICENSE) dosyasına bakın.

## 👥 Katkıda Bulunma

Katkılarınızı memnuniyetle karşılıyoruz! Aşağıdaki adımları izleyin:

1. Bu repo'yu forklayın
2. Yeni bir dal oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add some amazing feature'`)
4. Dalınıza push edin (`git push origin feature/amazing-feature`)
5. Bir Pull Request açın

## 📞 İletişim

Proje Sahibi: Erdem Aslan - erdemaslanss@gmail.com

Proje Linki: [https://github.com/ErdemAslans/lungvision-ai-with-DevOPS](https://github.com/ErdemAslans/lungvision-ai-with-DevOPS)

---

<div align="center">
  <p>🫁 LungVision AI ile daha sağlıklı bir gelecek için yapay zeka gücünü keşfedin.</p>
</div>

