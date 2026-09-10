class ProspectScorer:

    def score(self, prospect, website_data=None):

        if website_data is None:
            website_data = {}

        score = 0
        reasons = []

        category = prospect.get(
            "category",
            ""
        ).lower()

        # --------------------------------------------------
        # Local business fit
        # --------------------------------------------------

        good_categories = [
            "restaurant",
            "cafe",
            "bakery",
            "beauty",
            "fitness",
            "hotel",
            "shop",
            "bar",
            "food",
            "retail"
        ]

        if category in good_categories:
            score += 25
            reasons.append(
                "Good fit for local-business marketing."
            )
        else:
            score += 15

        # --------------------------------------------------
        # Website
        # --------------------------------------------------

        if website_data.get("success"):

            score += 15

            reasons.append(
                "Website is publicly accessible."
            )

            text_length = website_data.get(
                "text_length",
                0
            )

            if text_length < 1500:

                score += 10

                reasons.append(
                    "Website has relatively limited public content."
                )

        else:

            # Do NOT heavily penalize missing website research.
            # A local business can still be a good prospect.

            reasons.append(
                "Website could not be verified; prospect retained."
            )

        # --------------------------------------------------
        # Social presence
        # --------------------------------------------------

        signals = website_data.get(
            "signals",
            {}
        )

        social = signals.get(
            "social_media",
            []
        )

        if social:

            score += 10

            reasons.append(
                "Website references social media."
            )

        # --------------------------------------------------
        # Marketing signals
        # --------------------------------------------------

        marketing = signals.get(
            "marketing",
            []
        )

        if len(marketing) >= 2:

            score += 15

            reasons.append(
                "Business already uses marketing/promotional language."
            )

        elif len(marketing) == 1:

            score += 8

            reasons.append(
                "Business shows some marketing activity."
            )

        # --------------------------------------------------
        # Contact availability
        # --------------------------------------------------

        if prospect.get("website"):

            score += 5

            reasons.append(
                "Business website/contact channel available."
            )

        if prospect.get("phone"):

            score += 5

            reasons.append(
                "Business phone number available."
            )

        # --------------------------------------------------
        # Name / local-business quality
        # --------------------------------------------------

        name = prospect.get(
            "name",
            ""
        ).lower()

        if name:

            score += 5

            reasons.append(
                "Business has an identifiable name."
            )

        # --------------------------------------------------
        # Large-chain filtering
        # --------------------------------------------------

        large_brands = [
            "starbucks",
            "mcdonald",
            "mcdonald's",
            "subway",
            "burger king",
            "domino's",
            "pizza hut",
            "kfc",
            "marriott",
            "hilton"
        ]

        if any(
            brand in name
            for brand in large_brands
        ):

            score -= 40

            reasons.append(
                "Likely large chain; lower priority."
            )

        # --------------------------------------------------
        # Clamp
        # --------------------------------------------------

        score = max(
            0,
            min(
                100,
                score
            )
        )

        # --------------------------------------------------
        # Priority
        # --------------------------------------------------

        if score >= 75:

            priority = "HIGH"

        elif score >= 50:

            priority = "MEDIUM"

        else:

            priority = "LOW"

        return {
            "score": score,
            "priority": priority,
            "reasons": reasons
        }

    # ------------------------------------------------------
    # Rank prospects
    # ------------------------------------------------------

    def rank(self, prospects):

        return sorted(
            prospects,
            key=lambda x: x.get(
                "prospect_score",
                x.get("score", 0)
            ),
            reverse=True
        )