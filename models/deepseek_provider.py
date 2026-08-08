import logging
from typing import List, Dict, Optional, Tuple
from openai import AsyncOpenAI

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)

class DeepSeekProvider(BaseLLMProvider):
    """DeepSeek API Provider (DeepSeek-V3 / DeepSeek-R1)."""

    def __init__(self, api_key: str, model_name: str = "deepseek-chat"):
        super().__init__(name="DeepSeek", default_model_name=model_name)
        self.api_key = api_key
        self.client = (
            AsyncOpenAI(api_key=api_key, base_url="https://api.deepseek.com")
            if api_key
            else None
        )

    async def generate_response(
        self,
        prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        image_bytes_list: Optional[List[bytes]] = None,
        system_instruction: Optional[str] = None,
    ) -> Tuple[str, int, int]:
        if not self.client:
            return "❌ DeepSeek API Key is missing.", 0, 0

        messages = []

        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})

        if history:
            for msg in history:
                messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.client.chat.completions.create(
                model=self.default_model_name,
                messages=messages,
                max_tokens=2000,
            )
            choice = response.choices[0].message
            content = choice.content or ""
            reasoning = getattr(choice, "reasoning_content", None)

            usage = response.usage
            prompt_tokens = usage.prompt_tokens if usage else int(len(prompt.split()) * 1.3)
            completion_tokens = usage.completion_tokens if usage else int(len(content.split()) * 1.3)

            if reasoning:
                text = f"🧠 *Reasoning process:*\n_{reasoning[:500]}..._\n\n{content}"
            else:
                text = content or "No response from DeepSeek."

            return text, prompt_tokens, completion_tokens
        except Exception as e:
            logger.error(f"DeepSeek API Error: {e}")
            return f"❌ DeepSeek Error: {str(e)}", 0, 0
