import os
import json
from datetime import datetime

DELIVERY_DIR = "deliveries"


def create_delivery(
    order_id,
    customer,
    product_name,
    business_name
):

    os.makedirs(
        DELIVERY_DIR,
        exist_ok=True
    )

    safe_name = (
        business_name
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
    )

    filename = (
        f"{order_id}_{safe_name}_"
        f"growth_kit.txt"
    )

    filepath = os.path.join(
        DELIVERY_DIR,
        filename
    )

    content = f"""
LOCAL BUSINESS GROWTH KIT
=========================

Customer:
{customer}

Business:
{business_name}

Product:
{product_name}

Generated:
{datetime.utcnow().isoformat()}

--------------------------------
1. SOCIAL MEDIA POST IDEAS
--------------------------------

1. Introduce your business
2. Showcase a popular product
3. Behind-the-scenes post
4. Customer experience
5. Staff introduction
6. Educational tip
7. Frequently asked question
8. Seasonal promotion
9. Product spotlight
10. Local community post
11. Customer testimonial
12. Special offer

--------------------------------
2. READY-TO-USE CAPTION IDEAS
--------------------------------

Caption 1:
Discover what makes {business_name} special.
Visit us and experience it for yourself.

Caption 2:
Looking for something worth sharing?
Come see what {business_name} has to offer.

Caption 3:
Your next favorite local experience
could be right here at {business_name}.

--------------------------------
3. PROMOTIONAL OFFERS
--------------------------------

Offer 1:
New Customer Special

Offer 2:
Bring a Friend Promotion

Offer 3:
Limited-Time Local Special

Offer 4:
Returning Customer Reward

--------------------------------
4. SHORT VIDEO IDEAS
--------------------------------

Video 1:
A 15-second tour of the business.

Video 2:
Show the product/service people love most.

Video 3:
Behind-the-scenes preparation.

Video 4:
Answer one common customer question.

--------------------------------
5. CALL TO ACTIONS
--------------------------------

Visit us today.
Message us for details.
Book your visit.
Try it this week.
Share this with a friend.

--------------------------------

This package was generated specifically
for the customer's business.
"""

    with open(filepath, "w") as file:
        file.write(content.strip())

    return filepath