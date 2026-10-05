from abc import ABC, abstractmethod


class ProviderError(Exception):
    """Raised when the upstream AI provider fails."""


class AIProvider(ABC):
    name = "base"
    default_base_url = ""
    default_model = ""

    def __init__(self, api_key: str, model: str = "", base_url: str = ""):
        self.api_key = api_key
        self.model = model or self.default_model
        self.base_url = (base_url or self.default_base_url).rstrip("/")

    def is_configured(self) -> bool:
        return bool(self.api_key and self.model and self.base_url)

    @abstractmethod
    def chat(self, messages: list[dict]) -> str:
        """messages: [{"role": "system|user|assistant", "content": str}] -> reply text"""
