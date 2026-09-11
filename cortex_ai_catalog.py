"""Cortex AI provider/model catalog.

The catalog is intentionally provider-neutral. It contains safe UI metadata and
connection presets; live model lists can be discovered from providers that expose
model-list APIs, so Cortex does not become stale when providers add models.
Secrets are never stored here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class AIProviderPreset:
    provider_id: str
    name: str
    family: str
    base_url: str
    auth_env: str
    protocol: str
    docs_url: str
    supports_model_listing: bool = True


PROVIDERS: Dict[str, AIProviderPreset] = {
    "local_ollama": AIProviderPreset("local_ollama", "Ollama (Local)", "local", "http://127.0.0.1:11434/v1", "", "openai_compatible", "https://ollama.com/"),
    "openai": AIProviderPreset("openai", "OpenAI", "hosted", "https://api.openai.com/v1", "OPENAI_API_KEY", "openai_compatible", "https://platform.openai.com/docs/models"),
    "google_gemini": AIProviderPreset("google_gemini", "Google Gemini", "hosted", "https://generativelanguage.googleapis.com/v1beta", "GEMINI_API_KEY", "gemini", "https://ai.google.dev/gemini-api/docs/models"),
    "anthropic": AIProviderPreset("anthropic", "Anthropic Claude", "hosted", "https://api.anthropic.com/v1", "ANTHROPIC_API_KEY", "anthropic", "https://platform.claude.com/docs/en/api/models/list"),
    "mistral": AIProviderPreset("mistral", "Mistral AI", "hosted", "https://api.mistral.ai/v1", "MISTRAL_API_KEY", "openai_compatible", "https://docs.mistral.ai/models"),
    "xai": AIProviderPreset("xai", "xAI Grok", "hosted", "https://api.x.ai/v1", "XAI_API_KEY", "openai_compatible", "https://docs.x.ai/"),
    "deepseek": AIProviderPreset("deepseek", "DeepSeek", "hosted", "https://api.deepseek.com/v1", "DEEPSEEK_API_KEY", "openai_compatible", "https://api-docs.deepseek.com/"),
    "groq": AIProviderPreset("groq", "Groq", "hosted", "https://api.groq.com/openai/v1", "GROQ_API_KEY", "openai_compatible", "https://console.groq.com/docs"),
    "cohere": AIProviderPreset("cohere", "Cohere", "hosted", "https://api.cohere.com/v2", "COHERE_API_KEY", "cohere", "https://docs.cohere.com/"),
    "together": AIProviderPreset("together", "Together AI", "hosted", "https://api.together.xyz/v1", "TOGETHER_API_KEY", "openai_compatible", "https://docs.together.ai/"),
    "openrouter": AIProviderPreset("openrouter", "OpenRouter", "gateway", "https://openrouter.ai/api/v1", "OPENROUTER_API_KEY", "openai_compatible", "https://openrouter.ai/docs"),
    "custom_openai": AIProviderPreset("custom_openai", "Custom OpenAI-Compatible", "custom", "", "CUSTOM_AI_API_KEY", "openai_compatible", "", supports_model_listing=True),
}


def providers() -> List[dict]:
    """Return safe provider metadata for the Command Center."""
    return [
        {
            "id": p.provider_id,
            "name": p.name,
            "family": p.family,
            "base_url": p.base_url,
            "auth_env": p.auth_env,
            "protocol": p.protocol,
            "docs_url": p.docs_url,
            "supports_model_listing": p.supports_model_listing,
        }
        for p in PROVIDERS.values()
    ]


def get_provider(provider_id: str) -> AIProviderPreset:
    try:
        return PROVIDERS[provider_id]
    except KeyError as exc:
        raise ValueError("unsupported AI provider") from exc
