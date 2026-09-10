import json
import urllib.parse
import urllib.request
import urllib.error
import time


class ProspectResearcher:

    def __init__(self):

        self.nominatim_url = (
            "https://nominatim.openstreetmap.org/search"
        )

        # Multiple public Overpass instances.
        # If one is unavailable, try another.
        self.overpass_urls = [
            "https://overpass-api.de/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter",
            "https://overpass.private.coffee/api/interpreter",
        ]

        self.user_agent = (
            "ai-survival-business/6.1 "
            "(prospect research)"
        )

    # ======================================================
    # HTTP REQUEST
    # ======================================================

    def request_json(self, url):

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "application/json"
            }
        )

        with urllib.request.urlopen(
            request,
            timeout=20
        ) as response:

            return json.loads(
                response.read().decode("utf-8")
            )

    # ======================================================
    # GEOCODING
    # ======================================================

    def geocode_city(self, city):

        params = urllib.parse.urlencode({
            "q": city,
            "format": "json",
            "limit": 1
        })

        url = f"{self.nominatim_url}?{params}"

        try:

            result = self.request_json(url)

            if not result:
                return None

            return {
                "lat": float(result[0]["lat"]),
                "lon": float(result[0]["lon"]),
                "display_name": result[0]["display_name"]
            }

        except Exception as error:

            print(
                f"Geocoding failed: {error}"
            )

            return None

    # ======================================================
    # CATEGORY MAPPING
    # ======================================================

    def get_categories(self):

        return {
            "restaurant": [
                '["amenity"="restaurant"]'
            ],

            "cafe": [
                '["amenity"="cafe"]'
            ],

            "bakery": [
                '["shop"="bakery"]'
            ],

            "beauty": [
                '["shop"="beauty"]',
                '["shop"="hairdresser"]'
            ],

            "fitness": [
                '["leisure"="fitness_centre"]',
                '["sport"="fitness"]'
            ],

            "hotel": [
                '["tourism"="hotel"]'
            ],

            "shop": [
                '["shop"]'
            ]
        }

    # ======================================================
    # SINGLE OVERPASS QUERY
    # ======================================================

    def query_overpass(
        self,
        query
    ):

        encoded = urllib.parse.urlencode({
            "data": query
        })

        for endpoint in self.overpass_urls:

            print(
                f"   Trying: {endpoint}"
            )

            try:

                request = urllib.request.Request(
                    endpoint,
                    data=encoded.encode("utf-8"),
                    headers={
                        "User-Agent": self.user_agent,
                        "Content-Type":
                        "application/x-www-form-urlencoded"
                    }
                )

                with urllib.request.urlopen(
                    request,
                    timeout=35
                ) as response:

                    data = json.loads(
                        response.read().decode("utf-8")
                    )

                print("   ✓ Server responded.")

                return data

            except urllib.error.HTTPError as error:

                print(
                    f"   ⚠ HTTP {error.code}"
                )

            except urllib.error.URLError as error:

                print(
                    f"   ⚠ Connection error: {error}"
                )

            except Exception as error:

                print(
                    f"   ⚠ Error: {error}"
                )

            # Small pause before another endpoint
            time.sleep(2)

        return None

    # ======================================================
    # PARSE BUSINESS
    # ======================================================

    def parse_business(
        self,
        element,
        city
    ):

        tags = element.get(
            "tags",
            {}
        )

        name = tags.get(
            "name"
        )

        if not name:
            return None

        address_parts = [
            tags.get("addr:housenumber"),
            tags.get("addr:street"),
            tags.get("addr:city"),
            tags.get("addr:postcode")
        ]

        address = ", ".join(
            part
            for part in address_parts
            if part
        )

        website = (
            tags.get("website")
            or tags.get("contact:website")
            or ""
        )

        phone = (
            tags.get("phone")
            or tags.get("contact:phone")
            or ""
        )

        category = (
            tags.get("amenity")
            or tags.get("shop")
            or tags.get("tourism")
            or tags.get("leisure")
            or tags.get("sport")
            or "business"
        )

        return {
            "name": name.strip(),
            "category": category,
            "address": address,
            "city": city,
            "website": website.strip(),
            "phone": phone.strip(),
            "source": "OpenStreetMap",
            "source_id": element.get("id"),
            "contact_status": "not_contacted",
            "response_status": "unknown",
            "payment_status": "not_paid"
        }

    # ======================================================
    # CHAIN FILTER
    # ======================================================

    def looks_like_large_chain(
        self,
        name
    ):

        name_lower = name.lower()

        chains = [
            "starbucks",
            "mcdonald",
            "mcdonald's",
            "subway",
            "burger king",
            "kfc",
            "pizza hut",
            "domino's",
            "dominos",
            "dunkin",
            "wendy's",
            "wendys",
            "taco bell",
            "chipotle",
            "marriott",
            "hilton",
            "holiday inn",
            "best western",
            "7-eleven",
            "walgreens",
            "cvs pharmacy",
            "walmart",
            "target"
        ]

        return any(
            chain in name_lower
            for chain in chains
        )

    # ======================================================
    # MAIN SEARCH
    # ======================================================

    def find_businesses(
        self,
        city,
        business_types=None,
        limit=30
    ):

        if business_types is None:

            business_types = [
                "restaurant",
                "cafe",
                "bakery",
                "beauty",
                "fitness",
                "hotel",
                "shop"
            ]

        location = self.geocode_city(
            city
        )

        if not location:

            print(
                "Could not locate city."
            )

            return []

        lat = location["lat"]
        lon = location["lon"]

        print(
            f"\n📍 Location: "
            f"{location['display_name']}"
        )

        print(
            "🔎 Searching public business data..."
        )

        category_map = (
            self.get_categories()
        )

        all_prospects = []

        # --------------------------------------------------
        # Search each category separately.
        # This is much lighter than one giant query.
        # --------------------------------------------------

        for business_type in business_types:

            if len(all_prospects) >= limit:
                break

            filters = category_map.get(
                business_type,
                []
            )

            if not filters:
                continue

            print(
                f"\n   Searching category: "
                f"{business_type}"
            )

            filter_text = ""

            for osm_filter in filters:

                filter_text += (
                    f"nwr{osm_filter}"
                    f"(around:5000,{lat},{lon});"
                )

            query = f"""
            [out:json][timeout:20];
            (
                {filter_text}
            );
            out center tags;
            """

            data = self.query_overpass(
                query
            )

            if not data:

                print(
                    "   ✗ No response from "
                    "available Overpass servers."
                )

                continue

            elements = data.get(
                "elements",
                []
            )

            print(
                f"   Found {len(elements)} "
                f"raw records."
            )

            for element in elements:

                prospect = self.parse_business(
                    element,
                    city
                )

                if not prospect:
                    continue

                # Skip obvious large chains.
                if self.looks_like_large_chain(
                    prospect["name"]
                ):

                    continue

                all_prospects.append(
                    prospect
                )

                if len(all_prospects) >= limit:
                    break

            # Be polite to public infrastructure.
            time.sleep(1)

        # ==================================================
        # DEDUPLICATE
        # ==================================================

        unique = []
        seen = set()

        for prospect in all_prospects:

            key = (
                prospect["name"].lower(),
                prospect["address"].lower()
            )

            if key in seen:
                continue

            seen.add(key)

            unique.append(
                prospect
            )

        # ==================================================
        # FINAL LIMIT
        # ==================================================

        unique = unique[:limit]

        print(
            f"\n✓ Final prospects: "
            f"{len(unique)}"
        )

        return unique