class OutreachGenerator:
    def create_message(self, prospect, product, website_data=None):
        website_data = website_data or {}
        name = prospect.get("name", "there")
        category = prospect.get("category", "business")
        product_name = product.get("product_name", "marketing package")

        observations = []
        if website_data.get("success"):
            title = website_data.get("title", "")
            observations.append(
                f"I came across {name}'s website" + (f" ({title})" if title else "") + "."
            )
            social = website_data.get("signals", {}).get("social_media", [])
            if social:
                observations.append("I noticed your site references " + ", ".join(social) + ".")
        else:
            observations.append(f"I came across your {category} business in public business listings.")

        observation_text = " ".join(observations)
        return f"""Subject: A free marketing idea for {name}

Hi {name},

{observation_text}

I work on a simple content package called {product_name}, designed to help small businesses create consistent marketing content without hiring a full marketing agency.

The starter package includes:

• 12 social media post ideas
• 12 ready-to-use captions
• 4 promotional offers
• 4 short-video ideas
• Monthly content calendar
• Call-to-action suggestions

I'd be happy to create one free sample post specifically for {name}, with no obligation.

If you'd like to see it, just reply and I'll prepare the sample.

Best,
AI Business Team
"""

    def create_record(self, prospect, product, website_data=None):
        return {
            "prospect": prospect.get("name"),
            "product": product.get("product_name"),
            "channel": "manual",
            "status": "draft",
            "message": self.create_message(prospect, product, website_data),
        }

    def generate(self, prospect, product, website_data=None):
        """Compatibility wrapper used by the main engine."""
        return self.create_record(prospect, product, website_data)
