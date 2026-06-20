from cerebras.cloud.sdk import Cerebras
from fastapi_app.config.settings import CEREBRAS_API_KEYS


def try_cerebras(prompt):
    for i, key in enumerate(CEREBRAS_API_KEYS, 1):
        if not key:
            continue
        try:
            print(f"🔄 Cerebras key {i}/{len(CEREBRAS_API_KEYS)}...")
            client   = Cerebras(api_key=key)
            response = client.chat.completions.create(
                model       = "llama-3.3-70b",
                messages    = [{"role": "user", "content": prompt}],
                max_tokens  = 1000,
                temperature = 0.3
            )
            result = response.choices[0].message.content.strip()
            print(f"✅ Cerebras key {i} success")
            return result
        except Exception as e:
            print(f"❌ Cerebras key {i} failed: {str(e)}")
            continue
    return None
