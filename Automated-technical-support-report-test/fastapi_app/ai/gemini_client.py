import google.generativeai as genai
from fastapi_app.config.settings import GEMINI_API_KEYS


def try_gemini(prompt):
    for i, key in enumerate(GEMINI_API_KEYS, 1):
        if not key:
            continue
        try:
            print(f"🔄 Gemini key {i}/{len(GEMINI_API_KEYS)}...")
            genai.configure(api_key=key)
            model    = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            result   = response.text.strip()
            print(f"✅ Gemini key {i} success")
            return result
        except Exception as e:
            print(f"❌ Gemini key {i} failed: {str(e)}")
            continue
    return None
