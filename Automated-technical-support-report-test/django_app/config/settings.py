from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------- SECURITY ----------------
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = ['*']

# ---------------- APPS ----------------
INSTALLED_APPS = [
    # شيلنا django.contrib.admin و django.contrib.sessions لأنهم محتاجين SQLite/ORM — بنستخدم MSSQL مباشرة
    # auth و contenttypes لازم يفضلوا موجودين لأن apps.users.models بيعمل import من django.contrib.auth.models
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'apps.users.apps.UsersConfig',
    'apps.agents.apps.AgentsConfig',
    'apps.customers.apps.CustomersConfig',
    'apps.reports.apps.ReportsConfig',
    'apps.dashboard.apps.DashboardConfig',
    'django.contrib.sitemaps',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',   # بيستخدم SESSION_ENGINE المخصص
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware', # بيستخدم AUTHENTICATION_BACKENDS المخصص
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ---------------- DATABASE ----------------
# لا SQLite — كل حاجة على SQL Server عشان Vercel serverless filesystem مؤقت.
# Django ORM مش بيُستخدم — الاتصال عن طريق pymssql مباشرة في db_connection.py
DATABASES = {}

# ---------------- AUTH BACKEND ----------------
AUTHENTICATION_BACKENDS = [
    'apps.users.backends.MSSQLAuthBackend',
]

# ---------------- SESSION BACKEND ----------------
SESSION_ENGINE = 'apps.users.session_backend'
SESSION_COOKIE_AGE = 60 * 60 * 8  # 8 ساعات

# نفس بيانات SQL Server دي، بس عن طريق pymssql مباشرة في الـ views
# (للـ stored procedures وجداول التقارير القديمة اللي مالهاش Django models)
MSSQL_CONFIG = {
    'server':      os.getenv('DB_SERVER'),
    'database':    os.getenv('DB_NAME'),
    'user':        os.getenv('DB_USER'),
    'password':    os.getenv('DB_PASSWORD'),
    'port':        int(os.getenv('DB_PORT', '1433')),
    'tds_version': '4.2',
    'charset':     'CP1256',
}

# ---------------- PASSWORD VALIDATION ----------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ---------------- LOCALIZATION ----------------
LANGUAGE_CODE = 'ar'
TIME_ZONE = 'Africa/Cairo'
USE_I18N = True
USE_TZ = True

# ---------------- STATIC FILES ----------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
# بما إن Vercel @vercel/python builder مش بيشغل build.sh / collectstatic تلقائيًا،
# بنخلي WhiteNoise يقرأ الملفات الثابتة مباشرة من STATICFILES_DIRS (مجلد static/)
# بدل ما يعتمد على STATIC_ROOT اللي محتاج collectstatic عشان يتملي.
WHITENOISE_USE_FINDERS = True
STATICFILES_DIRS = [BASE_DIR / 'static']
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------- AUTH ----------------
LOGIN_URL = '/users/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'