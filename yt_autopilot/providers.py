"""Provider contracts. Implementations belong in adapters and workers."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Sequence
from .core import Asset, RightsRecord


class LLMProvider(Protocol):
    def complete(self, prompt: str, *, temperature: float = 0.2) -> str: ...


class TTSProvider(Protocol):
    def synthesize(self, text: str, *, voice: str, language: str) -> bytes: ...


class MediaSearchProvider(Protocol):
    def search(self, query: str, *, limit: int = 20) -> Sequence[Asset]: ...


class MediaDownloadProvider(Protocol):
    def download(self, asset: Asset, destination: str) -> str: ...


class YouTubeProvider(Protocol):
    def upload(self, video_path: str, *, title: str, description: str, privacy: str) -> str: ...
    def schedule(self, video_id: str, publish_at: str) -> None: ...
    def set_thumbnail(self, video_id: str, image_path: str) -> None: ...


class StorageProvider(Protocol):
    def put(self, local_path: str, key: str) -> str: ...
    def delete(self, key: str) -> None: ...


@dataclass(frozen=True)
class ProviderRegistry:
    """Dependency-injection container; no persisted record becomes executable code."""
    llm: LLMProvider | None = None
    tts: TTSProvider | None = None
    media_search: MediaSearchProvider | None = None
    media_download: MediaDownloadProvider | None = None
    youtube: YouTubeProvider | None = None
    storage: StorageProvider | None = None
