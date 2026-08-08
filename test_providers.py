import asyncio
import logging
from config import GEMINI_API_KEY, OPENAI_API_KEY, DEEPSEEK_API_KEY
from models import ModelRouter

logging.basicConfig(level=logging.INFO)

async def test():
    print("Testing ModelRouter...")
    router = ModelRouter(
        gemini_key=GEMINI_API_KEY,
        openai_key=OPENAI_API_KEY,
        deepseek_key=DEEPSEEK_API_KEY,
    )

    for provider_name in ["gemini", "gpt", "deepseek"]:
        print(f"\n--- Testing Provider: {provider_name} ---")
        router.set_active_model(1234, provider_name)
        response, used_provider = await router.generate(
            channel_id=1234,
            prompt="Hello! Say 'API connection working' in 5 words or less.",
        )
        print(f"Used: {used_provider}")
        print(f"Response: {response}")

if __name__ == "__main__":
    asyncio.run(test())
