import json
import os
from datetime import datetime


class ProspectDatabase:

    def __init__(self, filename="prospects.json"):
        self.filename = filename

    def load(self):
        if not os.path.exists(self.filename):
            return []

        try:
            with open(
                self.filename,
                "r",
                encoding="utf-8"
            ) as file:
                return json.load(file)

        except Exception:
            return []

    def save(self, prospects):
        with open(
            self.filename,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                prospects,
                file,
                indent=4,
                ensure_ascii=False
            )

    def add_prospects(self, new_prospects):

        existing = self.load()

        existing_keys = {
            (
                item.get("name", "").lower(),
                item.get("address", "").lower()
            )
            for item in existing
        }

        added = 0

        for prospect in new_prospects:

            key = (
                prospect.get("name", "").lower(),
                prospect.get("address", "").lower()
            )

            if key in existing_keys:
                continue

            prospect["created_at"] = (
                datetime.now().isoformat()
            )

            existing.append(prospect)
            existing_keys.add(key)
            added += 1

        self.save(existing)

        return added

    def update(self, prospect_name, updates):

        prospects = self.load()

        updated = False

        for prospect in prospects:

            if prospect.get("name") == prospect_name:

                prospect.update(updates)
                updated = True

        self.save(prospects)

        return updated

    def get_all(self):
        return self.load()