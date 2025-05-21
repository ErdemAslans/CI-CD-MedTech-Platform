FROM python:3.12-slim
WORKDIR /app

# Gerekli paketleri yükle
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    libffi-dev \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Node.js 20 kurulumu (npm 11.4.0 için gereken sürüm)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs

# requirements.txt'yi kopyala ve bağımlılıkları yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Django Tailwind için gerekli npm paketlerini yükle
RUN mkdir -p /app/theme/static_src/node_modules

# Uygulama dosyalarını kopyala
COPY . .

# Django Tailwind için NPM_BIN_PATH'i ayarla
ENV NPM_BIN_PATH=/usr/bin/npm

# Gerekli dizinleri oluştur
RUN mkdir -p /app/logs /app/static /app/staticfiles /app/media

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
