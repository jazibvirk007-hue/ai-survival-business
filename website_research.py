import re
import urllib.request
import urllib.error
from html import unescape


class WebsiteResearcher:

    def __init__(self):
        self.timeout = 15

    def normalize_url(self, url):
        if not url:
            return ""

        url = url.strip()

        # Fix common malformed URLs
        if url.startswith("https.//"):
            url = "https://" + url[7:]

        if url.startswith("http.//"):
            url = "http://" + url[7:]

        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        return url

    def clean_text(self, html):
        html = re.sub(
            r"<script.*?</script>",
            " ",
            html,
            flags=re.IGNORECASE | re.DOTALL
        )

        html = re.sub(
            r"<style.*?</style>",
            " ",
            html,
            flags=re.IGNORECASE | re.DOTALL
        )

        html = re.sub(
            r"<[^>]+>",
            " ",
            html
        )

        html = unescape(html)

        html = re.sub(
            r"\s+",
            " ",
            html
        )

        return html.strip()

    def extract_title(self, html):
        match = re.search(
            r"<title[^>]*>(.*?)</title>",
            html,
            flags=re.IGNORECASE | re.DOTALL
        )

        if not match:
            return ""

        return self.clean_text(match.group(1))

    def find_signals(self, text):

        lower = text.lower()

        signals = {
            "social_media": [],
            "marketing": [],
            "contact": [],
            "ecommerce": []
        }

        social_terms = [
            "instagram",
            "facebook",
            "tiktok",
            "youtube",
            "linkedin"
        ]

        marketing_terms = [
            "promotion",
            "special offer",
            "discount",
            "newsletter",
            "blog",
            "events",
            "book now",
            "order online"
        ]

        contact_terms = [
            "contact",
            "email",
            "phone",
            "call us",
            "get in touch"
        ]

        ecommerce_terms = [
            "shop",
            "cart",
            "checkout",
            "buy now",
            "order online"
        ]

        for term in social_terms:
            if term in lower:
                signals["social_media"].append(term)

        for term in marketing_terms:
            if term in lower:
                signals["marketing"].append(term)

        for term in contact_terms:
            if term in lower:
                signals["contact"].append(term)

        for term in ecommerce_terms:
            if term in lower:
                signals["ecommerce"].append(term)

        return signals

    def research(self, prospect):

        website = prospect.get("website", "")

        if not website:
            return {
                "success": False,
                "website": "",
                "title": "",
                "text_length": 0,
                "signals": {},
                "reason": "No website listed in public business data."
            }

        url = self.normalize_url(website)

        try:

            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent":
                    "Mozilla/5.0 "
                    "(compatible; AI-Survival-Business/6.0)"
                }
            )

            with urllib.request.urlopen(
                request,
                timeout=self.timeout
            ) as response:

                content_type = response.headers.get(
                    "Content-Type",
                    ""
                )

                if "text/html" not in content_type.lower():
                    return {
                        "success": False,
                        "website": url,
                        "title": "",
                        "text_length": 0,
                        "signals": {},
                        "reason": "Website did not return HTML."
                    }

                raw = response.read(
                    500_000
                ).decode(
                    "utf-8",
                    errors="ignore"
                )

            text = self.clean_text(raw)

            return {
                "success": True,
                "website": url,
                "title": self.extract_title(raw),
                "text_length": len(text),
                "signals": self.find_signals(text),
                "reason": ""
            }

        except urllib.error.HTTPError as error:

            return {
                "success": False,
                "website": url,
                "title": "",
                "text_length": 0,
                "signals": {},
                "reason": f"HTTP error {error.code}"
            }

        except Exception as error:

            return {
                "success": False,
                "website": url,
                "title": "",
                "text_length": 0,
                "signals": {},
                "reason": str(error)
            }