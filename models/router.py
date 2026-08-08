import logging
from typing import Dict, List, Optional, Tuple
from .base import BaseLLMProvider
from .gemini_provider import GeminiProvider
from .openai_provider import OpenAIProvider
from .deepseek_provider import DeepSeekProvider
from utils.token_tracker import TokenTracker

logger = logging.getLogger(__name__)

class ModelRouter:
    """Manages multi-LLM routing, active model per channel/user, fallbacks, and token tracking."""

    def __init__(
        self,
        gemini_key: str,
        openai_key: str,
        deepseek_key: str,
        token_tracker: TokenTracker,
        default_provider: str = "gemini",
    ):
        self.providers: Dict[str, BaseLLMProvider] = {
            "gemini": GeminiProvider(gemini_key, model_name="gemini-2.5-flash"),
            "gpt": OpenAIProvider(openai_key, model_name="gpt-4o"),
            "deepseek": DeepSeekProvider(deepseek_key, model_name="deepseek-chat"),
        }
        self.default_provider = default_provider if default_provider in self.providers else "gemini"
        self.active_model_per_channel: Dict[int, str] = {}
        self.token_tracker = token_tracker

    def get_active_model_name(self, channel_id: int) -> str:
        return self.active_model_per_channel.get(channel_id, self.default_provider)

    def set_active_model(self, channel_id: int, model_name: str) -> bool:
        clean_name = model_name.lower().strip()
        if clean_name in self.providers:
            self.active_model_per_channel[channel_id] = clean_name
            return True
        return False

    async def generate(
        self,
        channel_id: int,
        prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        image_bytes_list: Optional[List[bytes]] = None,
        system_instruction: Optional[str] = None,
    ) -> Tuple[str, str, int]:
        """Generates response using active model for channel. Returns (response_text, provider_name, total_tokens)."""
        active_key = self.get_active_model_name(channel_id)

        if image_bytes_list and active_key == "deepseek":
            logger.info("DeepSeek does not natively process images in this setup. Redirecting to Gemini.")
            active_key = "gemini"

        provider = self.providers.get(active_key, self.providers[self.default_provider])

        response, p_tokens, c_tokens = await provider.generate_response(
            prompt=prompt,
            history=history,
            image_bytes_list=image_bytes_list,
            system_instruction=system_instruction,
        )

        total_tokens = p_tokens + c_tokens

        # Log tokens if successful
        if not response.startswith("❌") and total_tokens > 0:
            self.token_tracker.log_usage(
                provider=provider.name,
                prompt_tokens=p_tokens,
                completion_tokens=c_tokens,
                channel_id=channel_id,
            )

        # Fallback check
        if response.startswith("❌") and len(self.providers) > 1:
            for fallback_key, fallback_provider in self.providers.items():
                if fallback_key != active_key:
                    logger.info(f"Fallback from {active_key} to {fallback_key}")
                    fallback_res, fb_p_tok, fb_c_tok = await fallback_provider.generate_response(
                        prompt=prompt,
                        history=history,
                        image_bytes_list=image_bytes_list,
                        system_instruction=system_instruction,
                    )
                    if not fallback_res.startswith("❌"):
                        fb_total = fb_p_tok + fb_c_tok
                        if fb_total > 0:
                            self.token_tracker.log_usage(
                                provider=fallback_provider.name,
                                prompt_tokens=fb_p_tok,
                                completion_tokens=fb_c_tok,
                                channel_id=channel_id,
                            )
                        return (
                            f"*(Fallback: switched from {active_key} to {fallback_key})*\n\n{fallback_res}",
                            fallback_provider.name,
                            fb_total,
                        )

        return response, provider.name, total_tokens
