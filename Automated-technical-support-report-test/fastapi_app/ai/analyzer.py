from fastapi_app.ai.groq_client import try_groq
from fastapi_app.ai.gemini_client import try_gemini
from fastapi_app.ai.cerebras_client import try_cerebras
from fastapi_app.utils.prompt_builder import build_prompt


def analyze_chat(chat_history, existing_categories: list):
    print("\n--- AI Analysis Start ---")
    prompt = build_prompt(chat_history, existing_categories)

    print("\n[1] Trying Groq...")
    result = try_groq(prompt)
    if result:
        return result

    print("\n[2] Groq exhausted → Trying Gemini...")
    result = try_gemini(prompt)
    if result:
        return result

    print("\n[3] Gemini exhausted → Trying Cerebras...")
    result = try_cerebras(prompt)
    if result:
        return result

    print("\n❌ All AI providers exhausted")
    return "⚠️ فشل الاتصال بجميع الـ AI providers"
