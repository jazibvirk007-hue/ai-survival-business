"""Multi-provider AI runtime for TJ Cortex.

Provides one safe interface for the provider catalog: discover available models,
select a provider/model, test connectivity, and generate text. Credentials stay
server-side in environment variables and are never returned in status payloads.
Native request formats are used where providers are not OpenAI-compatible.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Mapping, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from cortex_ai_catalog import AIProviderPreset, get_provider


class AIRuntimeError(RuntimeError):
    pass


@dataclass(frozen=True)
class AISelection:
    provider_id: str
    model: str

    def __post_init__(self) -> None:
        if not self.provider_id or not self.model or len(self.model) > 200:
            raise ValueError("provider_id and model are required; model must be <= 200 characters")
        get_provider(self.provider_id)


class CortexAIRuntime:
    """Provider-neutral runtime with native protocol handling."""

    def __init__(self, *, opener=urlopen, timeout_seconds: float = 30.0) -> None:
        if not 1 <= float(timeout_seconds) <= 120:
            raise ValueError("timeout_seconds must be between 1 and 120")
        self._opener = opener
        self.timeout_seconds = float(timeout_seconds)

    @staticmethod
    def _key(preset: AIProviderPreset) -> str:
        if not preset.auth_env:
            return ""
        key = os.getenv(preset.auth_env, "").strip()
        if not key:
            raise AIRuntimeError(f"missing server-side {preset.auth_env} environment variable")
        return key

    def _request(self, preset: AIProviderPreset, path: str, *, method: str = "GET", payload: Optional[Mapping[str, Any]] = None) -> dict[str, Any]:
        if not preset.base_url:
            raise AIRuntimeError("provider base URL is not configured")
        url = urljoin(preset.base_url.rstrip("/") + "/", path.lstrip("/"))
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        key = self._key(preset) if preset.auth_env else ""
        if preset.protocol in {"openai_compatible", "cohere"} and key:
            headers["Authorization"] = f"Bearer {key}"
        elif preset.protocol == "anthropic":
            headers["x-api-key"] = key
            headers["anthropic-version"] = "2023-06-01"
        elif preset.protocol == "gemini" and key:
            headers["x-goog-api-key"] = key
        body = None if payload is None else json.dumps(dict(payload)).encode("utf-8")
        request = Request(url, data=body, headers=headers, method=method)
        try:
            with self._opener(request, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            raise AIRuntimeError(f"AI provider HTTP error {exc.code}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise AIRuntimeError(f"AI provider connection failed: {type(exc).__name__}") from exc
        try:
            value = json.loads(raw)
        except (TypeError, ValueError) as exc:
            raise AIRuntimeError("AI provider returned invalid JSON") from exc
        if not isinstance(value, dict):
            raise AIRuntimeError("AI provider returned an invalid response object")
        if "error" in value:
            raise AIRuntimeError("AI provider returned an error")
        return value

    def discover_models(self, provider_id: str) -> list[str]:
        preset = get_provider(provider_id)
        if not preset.supports_model_listing:
            return []
        if preset.protocol == "anthropic":
            data = self._request(preset, "/models")
            return self._ids(data, ("data",))
        if preset.protocol == "gemini":
            data = self._request(preset, "/models")
            return [str(x["name"]).removeprefix("models/") for x in data.get("models", []) if isinstance(x, dict) and x.get("name")]
        if preset.protocol == "cohere":
            data = self._request(preset, "/models")
            return self._ids(data, ("models", "data"))
        data = self._request(preset, "/models")
        return self._ids(data, ("data",))

    @staticmethod
    def _ids(data: Mapping[str, Any], containers: tuple[str, ...]) -> list[str]:
        values: Any = None
        for key in containers:
            candidate = data.get(key)
            if isinstance(candidate, list):
                values = candidate
                break
        if values is None:
            return []
        return [str(item["id"]) for item in values if isinstance(item, dict) and item.get("id")][:200]

    def generate(self, selection: AISelection, messages: list[Mapping[str, str]], *, temperature: float = 0.2) -> str:
        if not messages or any(not isinstance(m, Mapping) for m in messages):
            raise ValueError("messages must be a non-empty list of mappings")
        if not 0 <= float(temperature) <= 2:
            raise ValueError("temperature must be between 0 and 2")
        preset = get_provider(selection.provider_id)
        if preset.protocol == "anthropic":
            system = "\n".join(str(m.get("content", "")) for m in messages if m.get("role") == "system")
            body = {
                "model": selection.model,
                "max_tokens": 2048,
                "temperature": float(temperature),
                "messages": [dict(m) for m in messages if m.get("role") != "system"],
            }
            if system:
                body["system"] = system
            data = self._request(preset, "/messages", method="POST", payload=body)
            try:
                return str(data["content"][0]["text"])
            except (KeyError, IndexError, TypeError) as exc:
                raise AIRuntimeError("Anthropic returned no assistant text") from exc
        if preset.protocol == "gemini":
            contents = []
            for message in messages:
                role = "model" if message.get("role") == "assistant" else "user"
                contents.append({"role": role, "parts": [{"text": str(message.get("content", ""))}]})
            body = {"contents": contents, "generationConfig": {"temperature": float(temperature)}}
            data = self._request(preset, f"/models/{selection.model}:generateContent", method="POST", payload=body)
            try:
                return str(data["candidates"][0]["content"]["parts"][0]["text"])
            except (KeyError, IndexError, TypeError) as exc:
                raise AIRuntimeError("Gemini returned no assistant text") from exc
        if preset.protocol == "cohere":
            body = {"model": selection.model, "messages": [dict(m) for m in messages], "temperature": float(temperature)}
            data = self._request(preset, "/chat", method="POST", payload=body)
            try:
                return str(data["message"]["content"][0]["text"])
            except (KeyError, IndexError, TypeError) as exc:
                raise AIRuntimeError("Cohere returned no assistant text") from exc
        data = self._request(
            preset,
            "/chat/completions",
            method="POST",
            payload={"model": selection.model, "messages": [dict(m) for m in messages], "temperature": float(temperature)},
        )
        try:
            return str(data["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError) as exc:
            raise AIRuntimeError("OpenAI-compatible provider returned no assistant text") from exc

    def status(self, selection: AISelection) -> dict[str, Any]:
        """Return UI-safe configuration only; never return credential values."""
        preset = get_provider(selection.provider_id)
        return {
            "provider_id": preset.provider_id,
            "provider": preset.name,
            "protocol": preset.protocol,
            "model": selection.model,
            "configured": bool(not preset.auth_env or os.getenv(preset.auth_env, "").strip()),
            "credential_env": preset.auth_env,
        }
