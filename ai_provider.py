"""Provider-neutral AI adapter for TJ Cortex.

Supports OpenAI-compatible local or hosted endpoints without exposing secrets to a UI.
The adapter only handles model communication; business actions remain outside it.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class AIProviderError(RuntimeError):
    """Raised when an AI provider cannot be reached or returns invalid data."""


@dataclass(frozen=True)
class AIProviderConfig:
    mode: str = "local"
    base_url: str = "http://127.0.0.1:11434/v1"
    model: str = ""
    api_key_env: str = "TJ_CORTEX_AI_API_KEY"
    timeout_seconds: float = 20.0

    def __post_init__(self) -> None:
        if self.mode not in {"local", "api"}:
            raise ValueError("mode must be 'local' or 'api'")
        if not self.base_url or not self.base_url.startswith(("http://", "https://")):
            raise ValueError("base_url must be an http(s) URL")
        if not self.model or len(self.model) > 200:
            raise ValueError("model must be a non-empty string up to 200 characters")
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", self.api_key_env):
            raise ValueError("api_key_env must be a valid environment variable name")
        if not 1 <= float(self.timeout_seconds) <= 120:
            raise ValueError("timeout_seconds must be between 1 and 120")

    @property
    def normalized_base_url(self) -> str:
        return self.base_url.rstrip("/")


class OpenAICompatibleProvider:
    """Small stdlib-only client for local and hosted OpenAI-compatible APIs."""

    def __init__(self, config: AIProviderConfig, opener=urlopen) -> None:
        self.config = config
        self._opener = opener

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.config.mode == "api":
            key = os.getenv(self.config.api_key_env, "").strip()
            if not key:
                raise AIProviderError(
                    f"API mode requires the server-side {self.config.api_key_env} environment variable"
                )
            headers["Authorization"] = f"Bearer {key}"
        return headers

    def _request(self, path: str, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.config.normalized_base_url}/{path.lstrip('/')}"
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(url, data=data, headers=self._headers(), method="POST" if data else "GET")
        try:
            with self._opener(request, timeout=float(self.config.timeout_seconds)) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            raise AIProviderError(f"AI provider HTTP error {exc.code}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise AIProviderError(f"AI provider connection failed: {exc}") from exc
        try:
            result = json.loads(raw)
        except (TypeError, ValueError) as exc:
            raise AIProviderError("AI provider returned invalid JSON") from exc
        if not isinstance(result, dict):
            raise AIProviderError("AI provider returned an invalid response object")
        if "error" in result:
            raise AIProviderError("AI provider returned an error")
        return result

    def test_connection(self) -> dict[str, Any]:
        """Return safe status data; never returns API credentials."""
        try:
            result = self._request("models")
            models = result.get("data", [])
            model_ids = [item.get("id") for item in models if isinstance(item, dict) and item.get("id")]
            return {"connected": True, "mode": self.config.mode, "model": self.config.model, "models": model_ids}
        except AIProviderError as exc:
            return {"connected": False, "mode": self.config.mode, "model": self.config.model, "error": str(exc)}

    def generate(self, messages: list[Mapping[str, str]], temperature: float = 0.2) -> str:
        """Generate text while keeping the model adapter separate from business actions."""
        if not messages or any(not isinstance(message, Mapping) for message in messages):
            raise ValueError("messages must be a non-empty list of mappings")
        if not 0 <= float(temperature) <= 2:
            raise ValueError("temperature must be between 0 and 2")
        result = self._request(
            "chat/completions",
            {"model": self.config.model, "messages": list(messages), "temperature": float(temperature)},
        )
        try:
            content = result["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AIProviderError("AI provider returned no assistant message") from exc
        if not isinstance(content, str):
            raise AIProviderError("AI provider returned non-text content")
        return content


def provider_from_env() -> OpenAICompatibleProvider:
    """Build a provider from server-side configuration without persisting secrets."""
    mode = os.getenv("TJ_CORTEX_AI_MODE", "local").strip().lower()
    default_url = "http://127.0.0.1:11434/v1" if mode == "local" else "https://api.openai.com/v1"
    config = AIProviderConfig(
        mode=mode,
        base_url=os.getenv("TJ_CORTEX_AI_BASE_URL", default_url).strip(),
        model=os.getenv("TJ_CORTEX_AI_MODEL", "local-model" if mode == "local" else "gpt-5.6").strip(),
        api_key_env=os.getenv("TJ_CORTEX_AI_KEY_ENV", "TJ_CORTEX_AI_API_KEY").strip(),
        timeout_seconds=float(os.getenv("TJ_CORTEX_AI_TIMEOUT", "20")),
    )
    return OpenAICompatibleProvider(config)
