import os
from pathlib import Path
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-key-change-in-production')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
   
    # Third-party apps
    'corsheaders',
    'tailwind',
    'theme',
    'rest_framework',
   
    # Local apps
    'users',
    'prediction',
    'dashboard',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
            ],
        },
    },
]

TAILWIND_APP_NAME = 'theme'
WSGI_APPLICATION = 'config.wsgi.application'

# MongoDB settings - .env dosyasından alınıyor
MONGO_HOST = os.getenv('MONGO_HOST', 'mongodb')
MONGO_URI = os.getenv('MONGO_URI')
MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
MONGO_DB = os.getenv('MONGO_DB', 'lungvision_db')
MONGO_USER = os.getenv('MONGO_USER', 'admin')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', 'password')

# MongoManager için özel değişkenler
MONGODB_URI = MONGO_URI
MONGODB_NAME = MONGO_DB

# SQLite kullan
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Custom user model
AUTH_USER_MODEL = 'users.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'tr-tr'
TIME_ZONE = 'Europe/Istanbul'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS settings
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10
}

# AWS S3 Storage
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME', '')
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'us-east-1')

# Node.js NPM path
NPM_BIN_PATH = r"C:\Program Files\nodejs\npm.cmd"  # Windows için standart yol
# NPM_BIN_PATH = "/usr/bin/npm"  # Linux/Mac için standart yol

# Security settings for production
if not DEBUG:
    SECURE_HSTS_SECONDS = 518400
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True

    LOGIN_URL = '/users/login/'

# ML Yapılandırma
ML_MODEL_PATH = os.path.join(BASE_DIR, 'ml', 'models', 'EfficientNetV2L_supreme.keras')
ML_MODEL_VERSION = '1.0.0'
ML_MODEL_NAME = 'EfficientNetV2L_Supreme'
ML_LOGGING_LEVEL = 'INFO'  # Üretim ortamında 'INFO', geliştirme ortamında 'DEBUG'

# Grad-CAM ve diğer çıktılar için dizinleri oluştur
GRADCAM_DIR = os.path.join(MEDIA_ROOT, 'gradcam')
PREDICTION_RESULTS_DIR = os.path.join(MEDIA_ROOT, 'prediction_results')

# Loglama yapılandırması
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'formatter': 'verbose',
        },
        'ml_file': {
            'level': ML_LOGGING_LEVEL,
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'ml.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'lungvision': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'lungvision.predictor': {
            'handlers': ['console', 'ml_file'],
            'level': ML_LOGGING_LEVEL,
            'propagate': False,
        },
        'lungvision.tasks': {
            'handlers': ['console', 'ml_file'],
            'level': ML_LOGGING_LEVEL,
            'propagate': False,
        },
    },
}

# Celery yapılandırması (isteğe bağlı)
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Log ve media dizinlerini oluştur
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)
os.makedirs(MEDIA_ROOT, exist_ok=True)
os.makedirs(GRADCAM_DIR, exist_ok=True)
os.makedirs(PREDICTION_RESULTS_DIR, exist_ok=True)

# TensorFlow uyarılarını azalt (isteğe bağlı)
try:
    import tensorflow as tf
    tf.get_logger().setLevel('ERROR')
except ImportError:
    pass  # TensorFlow yüklü değilse geç