import base64
import logging
from typing import List, Dict, Optional, Tuple
from openai import AsyncOpenAI

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)

class OpenAIProvider(BaseLLMProvider):
    """OpenAI API Provider (GPT-4o / GPT-4o-mini)."""

    def __init__(self, api_key: str, model_name: str = "gpt-4o"):
        super().__init__(name="OpenAI GPT", default_model_name=model_name)
        self.api_key = api_key
        self.client = AsyncOpenAI(api_key=api_key) if api_key else None

    async def generate_response(
        self,
        prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        image_bytes_list: Optional[List[bytes]] = None,
        system_instruction: Optional[str] = None,
    ) -> Tuple[str, int, int]:
        if not self.client:
            return "❌ OpenAI API Key is missing.", 0, 0

        messages = []

        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})

        if history:
            for msg in history:
                messages.append({"role": msg["role"], "content": msg["content"]})

        user_content = [{"type": "text", "text": prompt}]

        if image_bytes_list:
            for img_bytes in image_bytes_list:
                b64_img = base64.b64encode(img_bytes).decode("utf-8")
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}
                })

        messages.append({"role": "user", "content": user_content})

        try:
            response = await self.client.chat.completions.create(
                model=self.default_model_name,
                messages=messages,
                max_tokens=1500,
            )
            text = response.choices[0].message.content or "No response from OpenAI."
            usage = response.usage
            prompt_tokens = usage.prompt_tokens if usage else int(len(prompt.split()) * 1.3)
            completion_tokens = usage.completion_tokens if usage else int(len(text.split()) * 1.3)
            return text, prompt_tokens, completion_tokens
        except Exception as e:
            logger.error(f"OpenAI API Error: {e}")
            return f"❌ OpenAI Error: {str(e)}", 0, 0
