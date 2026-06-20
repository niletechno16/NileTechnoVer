"""
Vercel entrypoint.
Vercel بيدور على ملفات جوه فولدر api/ ويبني serverless function منها.
هنا بس بنستورد الـ FastAPI app الموجودة في fastapi_app/Main.py ونعرضها
باسم `app` (ده الاسم اللي مكتبة @vercel/python بتتوقعه لـ ASGI apps).
"""
from fastapi_app.Main import app
