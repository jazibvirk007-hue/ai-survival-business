"""Cortex Web Research: bounded internet research for market intelligence.

This module gives Cortex a controlled way to read public web pages and search
public web results. It does not bypass access controls, scrape private data,
or execute page-supplied code. Research is observational: external actions
remain behind Cortex Guard.
"""

from __future__ import annotations

import ipaddress
import os
import re
import socket
from dataclasses import dataclass
from html import unescape
from typing import Any
from urllib.parse import quote_plus, urljoin, urlparse
from urllib.request import Request, urlopen


class WebResearchError(RuntimeError):
    """Raised when public web research cannot be completed safely."""


@dataclass(frozen=True)
class ResearchResult:
    title: str
    url: str
    snippet: str
    source: str

    def to_dict(self) -> dict[str, str]:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
        }


class CortexWebResearch:
    """Fetch public pages and search results with SSRF and size limits."""

    USER_AGENT = "CortexResearch/1.0 (+authorized-public-web-research)"
    MAX_BYTES = 1_500_000
    MAX_RESULTS = 20
    BLOCKED_HOSTS = {"localhost", "localhost.localdomain"}

    def __init__(self, opener=urlopen, search_url: str | None = None) -> None:
        self._opener = opener
        self.search_url = (search_url or os.getenv(
            "TJ_CORTEX_SEARCH_URL",
            "https://html.duckduckgo.com/html/?q={query}",
        )).strip()
        if "{query}" not in self.search_url:
            raise ValueError("search_url must contain {query}")

    @classmethod
    def _validate_public_url(cls, url: str) -> str:
        parsed = urlparse(url.strip())
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise WebResearchError("only http(s) URLs are allowed")
        host = parsed.hostname.lower().rstrip(".")
        if host in cls.BLOCKED_HOSTS or host.endswith(".local"):
            raise WebResearchError("local hosts are not allowed")
        try:
            addresses = socket.getaddrinfo(host, None)
        except socket.gaierror as exc:
            raise WebResearchError("host could not be resolved") from exc
        for item in addresses:
            address = ipaddress.ip_address(item[4][0])
            if address.is_private or address.is_loopback or address.is_link_local or address.is_reserved or address.is_multicast:
                raise WebResearchError("private or non-public network targets are not allowed")
        return url.strip()

    def _get(self, url: str) -> str:
        safe_url = self._validate_public_url(url)
        request = Request(safe_url, headers={"User-Agent": self.USER_AGENT, "Accept": "text/html,application/xhtml+xml"})
        try:
            with self._opener(request, timeout=15) as response:
                content_type = response.headers.get("Content-Type", "")
                if content_type and "text/html" not in content_type and "application/xhtml+xml" not in content_type:
                    raise WebResearchError("only HTML pages are supported")
                raw = response.read(self.MAX_BYTES + 1)
        except WebResearchError:
            raise
        except Exception as exc:
            raise WebResearchError(f"web request failed: {type(exc).__name__}") from exc
        if len(raw) > self.MAX_BYTES:
            raise WebResearchError("page exceeds the research size limit")
        return raw.decode("utf-8", errors="replace")

    @staticmethod
    def _clean(text: str, limit: int = 500) -> str:
        text = unescape(re.sub(r"<[^>]+>", " ", text))
        text = re.sub(r"\s+", " ", text).strip()
        return text[:limit]

    def search(self, query: str, limit: int = 10) -> list[ResearchResult]:
        if not isinstance(query, str) or not query.strip() or len(query) > 500:
            raise ValueError("query must be a non-empty string up to 500 characters")
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= self.MAX_RESULTS:
            raise ValueError("limit must be between 1 and 20")
        search_url = self.search_url.format(query=quote_plus(query.strip()))
        html = self._get(search_url)
        pattern = re.compile(
            r'<a[^>]+class=["\'][^"\']*(?:result__a|result-link)[^"\']*["\'][^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
            re.I | re.S,
        )
        results: list[ResearchResult] = []
        for match in pattern.finditer(html):
            url = unescape(match.group(1))
            if url.startswith("//"):
                url = "https:" + url
            if not url.startswith(("http://", "https://")):
                continue
            title = self._clean(match.group(2), 200)
            start, end = match.end(), min(len(html), match.end() + 2500)
            snippet_match = re.search(r'(?:result__snippet|snippet)[^>]*>(.*?)</', html[start:end], re.I | re.S)
            snippet = self._clean(snippet_match.group(1), 500) if snippet_match else ""
            try:
                self._validate_public_url(url)
            except WebResearchError:
                continue
            results.append(ResearchResult(title=title or url, url=url, snippet=snippet, source="public_web_search"))
            if len(results) >= limit:
                break
        return results

    def fetch(self, url: str) -> dict[str, Any]:
        html = self._get(url)
        title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
        description_match = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']', html, re.I | re.S)
        text = self._clean(html, 8000)
        return {
            "url": url,
            "title": self._clean(title_match.group(1), 300) if title_match else url,
            "description": self._clean(description_match.group(1), 1000) if description_match else "",
            "text": text,
            "source": "public_web_page",
        }

    def research(self, query: str, limit: int = 8) -> dict[str, Any]:
        results = self.search(query, limit=limit)
        return {
            "query": query.strip(),
            "result_count": len(results),
            "results": [item.to_dict() for item in results],
            "observed_only": True,
            "external_actions": "guarded",
        }

    def status(self) -> dict[str, Any]:
        return {
            "engine": "Cortex Web Research",
            "version": "1.0",
            "internet": "public_http_https",
            "search": "configurable_public_search_endpoint",
            "private_network_targets": "blocked",
            "max_page_bytes": self.MAX_BYTES,
            "policy": "research_only_no_private_access_no_page_code_execution",
        }
