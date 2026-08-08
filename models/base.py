from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple

class BaseLLMProvider(ABC):
    """Abstract Base Class for LLM Providers."""

    def __init__(self, name: str, default_model_name: str):
        self.name = name
        self.default_model_name = default_model_name

    @abstractmethod
    async def generate_response(
        self,
        prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        image_bytes_list: Optional[List[bytes]] = None,
        system_instruction: Optional[str] = None,
    ) -> Tuple[str, int, int]:
        """Generate response. Returns (response_text, prompt_tokens, completion_tokens)."""
        pass
