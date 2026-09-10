import json
import os
from datetime import datetime


class SalesEngine:

    VALID_STATUSES = [
        "not_contacted",
        "draft_created",
        "approved",
        "contacted",
        "replied",
        "interested",
        "negotiating",
        "payment_requested",
        "paid",
        "delivered",
        "completed",
        "rejected"
    ]

    def __init__(
        self,
        filename="sales_pipeline.json"
    ):

        self.filename = filename

    def load(self):

        if not os.path.exists(
            self.filename
        ):
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

    def save(self, records):

        with open(
            self.filename,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                records,
                file,
                indent=4,
                ensure_ascii=False
            )

    def add_prospect(
        self,
        prospect,
        product
    ):

        records = self.load()

        for record in records:

            if (
                record.get("prospect")
                == prospect.get("name")
            ):

                return False

        record = {
            "prospect": prospect.get("name"),
            "category": prospect.get("category"),
            "product": product.get("product_name"),
            "price": product.get("starter_price"),
            "status": "not_contacted",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }

        records.append(
            record
        )

        self.save(
            records
        )

        return True

    def update_status(
        self,
        prospect_name,
        status
    ):

        if status not in self.VALID_STATUSES:

            raise ValueError(
                f"Invalid sales status: {status}"
            )

        records = self.load()

        for record in records:

            if (
                record.get("prospect")
                == prospect_name
            ):

                record["status"] = status
                record["last_updated"] = (
                    datetime.now().isoformat()
                )

                self.save(
                    records
                )

                return True

        return False

    def get_pipeline(self):

        return self.load()