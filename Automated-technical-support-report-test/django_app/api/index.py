"""
Vercel entrypoint لتطبيق Django.
Vercel بيدور على ملفات جوه api/ ويبني منها serverless function.
هنا بنستورد WSGI application بتاعت Django ونعرضها باسم `app`.
"""
import os
import sys

# نضيف روت المشروع (اللي فيه config/, apps/, db_connection.py...) للـ path
# عشان الاستيرادات بصيغة "from config... " و"from db_connection..." تشتغل صح
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.wsgi import get_wsgi_application

app = get_wsgi_application()
