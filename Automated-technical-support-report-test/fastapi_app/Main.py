from fastapi import FastAPI
from fastapi_app.routes.webhook import router

# ملحوظة: على Vercel كل request بياخد instance منفصل (serverless)،
# فمفيش معنى لـ uvicorn.run() ولا keep-alive loop (دول كانوا مخصوصين لـ Render
# عشان يمنعوا الخدمة من النوم). تم حذفهم بالكامل هنا.

app = FastAPI()

app.include_router(router)
