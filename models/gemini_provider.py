import io
import logging
from typing import List, Dict, Optional, Tuple
from PIL import Image

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)

class GeminiProvider(BaseLLMProvider):
    """Google Gemini API Provider."""

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        super().__init__(name="Gemini", default_model_name=model_name)
        self.api_key = api_key

    async def generate_response(
        self,
        prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        image_bytes_list: Optional[List[bytes]] = None,
        system_instruction: Optional[str] = None,
    ) -> Tuple[str, int, int]:
        if not self.api_key:
            return "❌ Gemini API Key is missing.", 0, 0

        contents = []

        if image_bytes_list:
            for img_bytes in image_bytes_list:
                try:
                    img = Image.open(io.BytesIO(img_bytes))
                    contents.append(img)
                except Exception as e:
                    logger.error(f"Error reading image for Gemini: {e}")

        formatted_prompt = ""
        if system_instruction:
            formatted_prompt += f"System: {system_instruction}\n\n"

        if history:
            for msg in history:
                role = "User" if msg["role"] == "user" else "Assistant"
                formatted_prompt += f"{role}: {msg['content']}\n"

        formatted_prompt += f"User: {prompt}"
        contents.append(formatted_prompt)

        # Estimate prompt tokens
        prompt_tokens = int(len(formatted_prompt.split()) * 1.3) + (len(image_bytes_list or []) * 258)

        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model=self.default_model_name,
                contents=contents,
            )
            text = response.text or "No response returned from Gemini."
            
            # Try getting usage metadata if present
            completion_tokens = int(len(text.split()) * 1.3)
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                p_tok = getattr(response.usage_metadata, "prompt_token_count", prompt_tokens)
                c_tok = getattr(response.usage_metadata, "candidates_token_count", completion_tokens)
                return text, p_tok, c_tok

            return text, prompt_tokens, completion_tokens
        except Exception as e:
            logger.error(f"Gemini API generation error: {e}")
            return f"❌ Gemini Error: {str(e)}", 0, 0
