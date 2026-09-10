import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import re


class MarketResearch:

    def __init__(self):
        self.results = []

    def search_google_news(self, query):

        encoded_query = urllib.parse.quote(query)

        url = (
            "https://news.google.com/rss/search?"
            f"q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        )

        try:

            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0"
                }
            )

            with urllib.request.urlopen(
                request,
                timeout=10
            ) as response:

                data = response.read()

            root = ET.fromstring(data)

            articles = []

            for item in root.findall(".//item"):

                title = item.findtext("title")

                if title:
                    articles.append(title.strip())

            return articles

        except Exception as error:

            print(f"⚠️ Search failed: {error}")

            return []

    def clean_text(self, text):

        text = text.lower()

        text = re.sub(
            r"[^a-z0-9\s]",
            " ",
            text
        )

        return re.sub(
            r"\s+",
            " ",
            text
        ).strip()

    def analyze(self, opportunity):

        # Different searches give us different signals.
        queries = {

            "demand": [
                f"{opportunity} demand",
                f"{opportunity} businesses need",
                f"{opportunity} outsourcing"
            ],

            "commercial": [
                f"{opportunity} pricing",
                f"{opportunity} freelance",
                f"{opportunity} agency"
            ],

            "trend": [
                f"{opportunity} growth",
                f"{opportunity} trend",
                f"{opportunity} 2026"
            ]
        }

        collected = {
            "demand": [],
            "commercial": [],
            "trend": []
        }

        for category, query_list in queries.items():

            for query in query_list:

                articles = self.search_google_news(
                    query
                )

                collected[category].extend(
                    articles
                )

        # Remove duplicate headlines.
        for category in collected:

            cleaned = []

            seen = set()

            for headline in collected[category]:

                normalized = self.clean_text(
                    headline
                )

                if normalized not in seen:

                    seen.add(normalized)

                    cleaned.append(
                        headline
                    )

            collected[category] = cleaned

        # --------------------------------------
        # DEMAND
        # --------------------------------------

        demand_words = [
            "need",
            "demand",
            "businesses",
            "customers",
            "clients",
            "hiring",
            "outsourcing",
            "small business"
        ]

        demand_hits = 0

        for headline in collected["demand"]:

            text = self.clean_text(
                headline
            )

            if any(
                word in text
                for word in demand_words
            ):

                demand_hits += 1

        demand_articles = len(
            collected["demand"]
        )

        if demand_articles > 0:

            demand_quality = (
                demand_hits /
                demand_articles
            )

        else:

            demand_quality = 0

        # Base demand + quality.
        demand_score = min(
            100,
            30
            + min(demand_articles, 20) * 2
            + demand_quality * 40
        )

        # --------------------------------------
        # COMMERCIAL SIGNAL
        # --------------------------------------

        commercial_words = [
            "price",
            "pricing",
            "cost",
            "freelance",
            "agency",
            "hire",
            "service",
            "clients",
            "revenue",
            "marketplace"
        ]

        commercial_hits = 0

        for headline in collected["commercial"]:

            text = self.clean_text(
                headline
            )

            if any(
                word in text
                for word in commercial_words
            ):

                commercial_hits += 1

        commercial_articles = len(
            collected["commercial"]
        )

        if commercial_articles > 0:

            commercial_quality = (
                commercial_hits /
                commercial_articles
            )

        else:

            commercial_quality = 0

        commercial_score = min(
            100,
            25
            + min(commercial_articles, 20) * 2
            + commercial_quality * 50
        )

        # --------------------------------------
        # TREND
        # --------------------------------------

        trend_words = [
            "growth",
            "growing",
            "rise",
            "rising",
            "surge",
            "boom",
            "trend",
            "record",
            "2026",
            "future"
        ]

        trend_hits = 0

        for headline in collected["trend"]:

            text = self.clean_text(
                headline
            )

            if any(
                word in text
                for word in trend_words
            ):

                trend_hits += 1

        trend_articles = len(
            collected["trend"]
        )

        if trend_articles > 0:

            trend_quality = (
                trend_hits /
                trend_articles
            )

        else:

            trend_quality = 0

        trend_score = min(
            100,
            20
            + min(trend_articles, 20) * 2
            + trend_quality * 50
        )

        # --------------------------------------
        # COMPETITION
        # --------------------------------------

        competition_words = [
            "agency",
            "platform",
            "software",
            "tool",
            "competitor",
            "marketplace",
            "provider",
            "freelancer"
        ]

        competition_hits = 0

        for category in collected:

            for headline in collected[category]:

                text = self.clean_text(
                    headline
                )

                if any(
                    word in text
                    for word in competition_words
                ):

                    competition_hits += 1

        total_articles = sum(
            len(items)
            for items in collected.values()
        )

        if total_articles > 0:

            competition_ratio = (
                competition_hits /
                total_articles
            )

        else:

            competition_ratio = 0

        competition_score = min(
            100,
            competition_ratio * 100
        )

        # --------------------------------------
        # FINAL OPPORTUNITY SCORE
        # --------------------------------------

        # Commercial intent is more valuable
        # than raw article volume.

        score = (
            demand_score * 0.35
            + commercial_score * 0.30
            + trend_score * 0.20
            + (100 - competition_score) * 0.15
        )

        headlines = []

        for category in collected:

            headlines.extend(
                collected[category]
            )

        # Remove duplicate headlines again.
        headlines = list(
            dict.fromkeys(headlines)
        )

        return {

            "opportunity":
                opportunity,

            "articles":
                total_articles,

            "demand":
                round(demand_score, 1),

            "commercial":
                round(commercial_score, 1),

            "competition":
                round(competition_score, 1),

            "trend":
                round(trend_score, 1),

            "score":
                round(score, 1),

            "headlines":
                headlines[:10]
        }

    def research_opportunities(
        self,
        opportunities
    ):

        results = []

        for opportunity in opportunities:

            print(
                f"\n🌐 Researching: {opportunity}"
            )

            result = self.analyze(
                opportunity
            )

            results.append(result)

        self.results = results

        return results

    def rank(self, results):

        return sorted(
            results,
            key=lambda x: x["score"],
            reverse=True
        )