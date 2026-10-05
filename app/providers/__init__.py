from app.config import settings
from app.providers.base import AIProvider, ProviderError  # noqa: F401
from app.providers.groq import GroqProvider
from app.providers.openai import OpenAICompatibleProvider
from app.providers.openrouter import OpenRouterProvider

_REGISTRY = {"groq": GroqProvider, "openai": OpenAICompatibleProvider, "openrouter": OpenRouterProvider}


def get_provider() -> AIProvider:
    cls = _REGISTRY.get(settings.AI_PROVIDER)
    if cls is None:
        raise ValueError(f"Unknown AI_PROVIDER '{settings.AI_PROVIDER}'. Use: {', '.join(_REGISTRY)}")
    return cls(settings.AI_API_KEY, settings.AI_MODEL, settings.AI_BASE_URL)
