import httpx
from app.providers.base import AIProvider, ProviderError


class OpenAICompatibleProvider(AIProvider):
    name = "openai"
    default_base_url = "https://api.openai.com/v1"
    default_model = "gpt-4o-mini"
    extra_headers: dict = {}

    def chat(self, messages: list[dict]) -> str:
        if not self.is_configured():
            raise ProviderError("AI provider is not configured")
        try:
            r = httpx.post(f"{self.base_url}/chat/completions", timeout=60,
                           headers={"Authorization": f"Bearer {self.api_key}", **self.extra_headers},
                           json={"model": self.model, "messages": messages})
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"] or ""
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            raise ProviderError(f"{self.name} request failed: {type(exc).__name__}") from exc
