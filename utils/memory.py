from typing import Dict, List

class MemoryManager:
    """Manages short-term conversation context for Discord channels/DMs."""

    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.history: Dict[int, List[Dict[str, str]]] = {}

    def get_history(self, channel_id: int) -> List[Dict[str, str]]:
        return self.history.get(channel_id, [])

    def add_message(self, channel_id: int, role: str, content: str):
        if channel_id not in self.history:
            self.history[channel_id] = []

        self.history[channel_id].append({"role": role, "content": content})

        # Keep sliding window
        if len(self.history[channel_id]) > self.max_history:
            self.history[channel_id] = self.history[channel_id][-self.max_history :]

    def clear(self, channel_id: int):
        if channel_id in self.history:
            self.history[channel_id] = []
