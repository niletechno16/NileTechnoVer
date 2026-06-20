from groq import Groq
from fastapi_app.config.settings import GROQ_API_KEYS


def try_groq(prompt):
    for i, key in enumerate(GROQ_API_KEYS, 1):
        if not key:
            continue
        try:
            print(f"🔄 Groq key {i}/{len(GROQ_API_KEYS)}...")
            client   = Groq(api_key=key)
            response = client.chat.completions.create(
                model       = "llama-3.3-70b-versatile",
                messages    = [{"role": "user", "content": prompt}],
                max_tokens  = 1000,
                temperature = 0.3
            )
            result = response.choices[0].message.content.strip()
            print(f"✅ Groq key {i} success")
            return result
        except Exception as e:
            print(f"❌ Groq key {i} failed: {str(e)}")
            continue
    return None
