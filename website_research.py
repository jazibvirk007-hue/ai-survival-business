import re
import urllib.request
import urllib.error
from html import unescape


class WebsiteResearcher:
    def __init__(self, timeout=15):
        self.timeout = timeout

    def normalize_url(self, url):
        if not url:
            return ""
        url = str(url).strip()
        if url.startswith("https.//"):
            url = "https://" + url[8:]
        elif url.startswith("http.//"):
            url = "http://" + url[7:]
        elif not url.startswith(("http://", "https://")):
            url = "https://" + url
        return url

    def clean_text(self, html):
        html = re.sub(r"<script.*?</script>", " ", html, flags=re.I | re.S)
        html = re.sub(r"<style.*?</style>", " ", html, flags=re.I | re.S)
        html = re.sub(r"<[^>]+>", " ", html)
        html = unescape(html)
        return re.sub(r"\s+", " ", html).strip()

    def extract_title(self, html):
        match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.I | re.S)
        return self.clean_text(match.group(1)) if match else ""

    def find_signals(self, text):
        lower = text.lower()
        groups = {
            "social_media": ["instagram", "facebook", "tiktok", "youtube", "linkedin"],
            "marketing": ["promotion", "special offer", "discount", "newsletter", "blog", "events", "book now", "order online"],
            "contact": ["contact", "email", "phone", "call us", "get in touch"],
            "ecommerce": ["shop", "cart", "checkout", "buy now", "order online"],
        }
        return {key: [term for term in terms if term in lower] for key, terms in groups.items()}

    def _failure(self, website, reason):
        return {
            "success": False,
            "website": website,
            "title": "",
            "text_length": 0,
            "signals": {"social_media": [], "marketing": [], "contact": [], "ecommerce": []},
            "reason": reason,
        }

    def research(self, prospect):
        # Accept both the prospect dict and a raw URL for backwards compatibility.
        if isinstance(prospect, dict):
            website = prospect.get("website", "")
        else:
            website = str(prospect or "")

        if not website:
            return self._failure("", "No website listed in public business data.")

        url = self.normalize_url(website)
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; AI-Survival-Business/7.2)"},
            )
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                content_type = response.headers.get("Content-Type", "")
                if "text/html" not in content_type.lower():
                    return self._failure(url, "Website did not return HTML.")
                raw = response.read(500_000).decode("utf-8", errors="ignore")

            text = self.clean_text(raw)
            return {
                "success": True,
                "website": url,
                "title": self.extract_title(raw),
                "text_length": len(text),
                "signals": self.find_signals(text),
                "reason": "",
            }
        except urllib.error.HTTPError as error:
            return self._failure(url, f"HTTP error {error.code}")
        except urllib.error.URLError as error:
            return self._failure(url, f"Connection error: {error.reason}")
        except Exception as error:
            return self._failure(url, f"{type(error).__name__}: {error}")
