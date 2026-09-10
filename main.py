"""
AI SURVIVAL BUSINESS
VERSION 7

Real business engine:
- $0 starting capital
- Real market research
- Real prospect discovery
- Real sales pipeline
- Real payment verification
- Real order management
- Payment-gated delivery
- No fake revenue
- No fake customers
- No automatic spam
"""

import os
import json
import uuid
from datetime import datetime

from market_research import MarketResearch
from sales_engine import SalesEngine
from payment_tracker import verified_revenue

from business import Business
from memory import add_memory

from product_factory import ProductFactory
from prospect_research import ProspectResearcher
from prospect_scoring import ProspectScorer
from website_research import WebsiteResearcher
from outreach import OutreachGenerator


# ============================================================
# CONFIGURATION
# ============================================================

OPPORTUNITIES = [
    "short video script service",
    "social media content service",
    "resume optimization service",
    "small business marketing service",
    "AI automation service",
    "YouTube script writing service",
    "product description writing service",
    "presentation design service"
]

ORDERS_FILE = "orders.json"
DELIVERY_DIR = "deliveries"


# ============================================================
# DISPLAY
# ============================================================

def header():

    print()
    print("=" * 70)
    print("             AI SURVIVAL BUSINESS")
    print("             VERSION 7.1")
    print("=" * 70)

    print()
    print("Starting capital: $0.00")
    print("Fake sales: DISABLED")
    print("Fake payments: DISABLED")
    print("Revenue simulation: DISABLED")
    print("Automatic spam: DISABLED")
    print()


# ============================================================
# MARKET RESEARCH
# ============================================================

def run_market_research():

    print("=" * 70)
    print("1. AI MARKET RESEARCH")
    print("=" * 70)

    researcher = MarketResearch()

    print()

    try:

        results = researcher.research_opportunities(
            OPPORTUNITIES
        )

    except Exception as error:

        print()
        print(
            f"❌ Market research failed: {error}"
        )

        return None

    if not results:

        print()
        print(
            "❌ Market research returned no results."
        )

        print(
            "The AI will NOT invent an opportunity."
        )

        return None

    ranked = researcher.rank(
        results
    )

    if not ranked:

        print()
        print(
            "❌ Ranking returned no opportunities."
        )

        return None

    print()

    for index, result in enumerate(
        ranked,
        start=1
    ):

        print(
            f"{index}. "
            f"{result['opportunity']}"
        )

        print(
            f"   Articles:      "
            f"{result['articles']}"
        )

        print(
            f"   Demand:        "
            f"{result['demand']}%"
        )

        print(
            f"   Commercial:    "
            f"{result['commercial']}%"
        )

        print(
            f"   Competition:   "
            f"{result['competition']}%"
        )

        print(
            f"   Trend:         "
            f"{result['trend']}%"
        )

        print(
            f"   AI Score:      "
            f"{result['score']}/100"
        )

        print()

    selected = ranked[0]

    print("=" * 70)
    print("🧠 AI DECISION")
    print("=" * 70)

    print()
    print(
        "Selected opportunity:"
    )

    print(
        f"👉 {selected['opportunity']}"
    )

    print(
        f"Opportunity score: "
        f"{selected['score']}/100"
    )

    print()

    return selected


# ============================================================
# PRODUCT FACTORY
# ============================================================

def run_product_factory(
    selected
):

    print("=" * 70)
    print("2. AI PRODUCT FACTORY")
    print("=" * 70)

    factory = ProductFactory()

    try:

        product = factory.build_product(
            selected["opportunity"],
            selected
        )

    except Exception as error:

        print(
            f"❌ Product factory failed: "
            f"{type(error).__name__}: {error}"
        )

        return None

    if not product:

        print(
            "❌ No product was created."
        )

        return None

    print()

    if isinstance(
        product,
        dict
    ):

        print(
            "Product:",
            product.get(
                "product_name",
                product.get(
                    "name",
                    "Unknown"
                )
            )
        )

        print(
            "Target:",
            product.get(
                "target_customer",
                product.get(
                    "customer",
                    "Unknown"
                )
            )
        )

        print(
            "Price: $",
            product.get(
                "starter_price",
                product.get(
                    "price",
                    0
                )
            )
        )

        print(
            "Cost: $",
            product.get(
                "creation_cost",
                product.get(
                    "cost",
                    0
                )
            )
        )

    else:

        print(
            product
        )

    return product


# ============================================================
# PROSPECT DISCOVERY
# ============================================================

def run_prospect_discovery(
    city
):

    print()
    print("=" * 70)
    print("3. CUSTOMER ACQUISITION")
    print("=" * 70)

    researcher = ProspectResearcher()

    try:

        prospects = researcher.find_businesses(
            city,
            limit=30
        )

    except TypeError:

        try:

            prospects = researcher.find_businesses(
                city
            )

        except Exception as error:

            print(
                f"❌ Prospect search failed: {error}"
            )

            return []

    except Exception as error:

        print(
            f"❌ Prospect search failed: {error}"
        )

        return []

    if not prospects:

        print()
        print(
            "No prospects found."
        )

        return []

    print()
    print(
        f"Raw prospects found: "
        f"{len(prospects)}"
    )

    return prospects


# ============================================================
# WEBSITE RESEARCH
# ============================================================

def research_website(
    prospect
):

    website = prospect.get(
        "website"
    )

    if not website:

        return {}

    researcher = WebsiteResearcher()

    try:

        result = researcher.research(
            website
        )

    except Exception:

        return {}

    if isinstance(
        result,
        dict
    ):

        return result

    return {}


# ============================================================
# PROSPECT SCORING
# ============================================================

def qualify_prospects(
    prospects
):

    print()
    print("=" * 70)
    print("4. PROSPECT QUALIFICATION")
    print("=" * 70)

    scorer = ProspectScorer()

    qualified = []

    for prospect in prospects:

        website_data = research_website(
            prospect
        )

        try:

            result = scorer.score(
                prospect,
                website_data
            )

        except TypeError:

            try:

                result = scorer.score(
                    prospect
                )

            except Exception:

                result = prospect

        except Exception:

            result = prospect

        if not isinstance(
            result,
            dict
        ):

            result = prospect.copy()

        # Preserve website research.

        result["_website_research"] = (
            website_data
        )

        score = (
            result.get("score")
            or result.get(
                "prospect_score"
            )
            or 0
        )

        try:

            score = float(
                score
            )

        except Exception:

            score = 0

        result["_final_score"] = score

        if score >= 50:

            qualified.append(
                result
            )

    qualified.sort(
        key=lambda x:
            x.get(
                "_final_score",
                0
            ),
        reverse=True
    )

    print()

    print(
        f"Qualified prospects: "
        f"{len(qualified)}"
    )

    print()

    for index, prospect in enumerate(
        qualified[:20],
        start=1
    ):

        print(
            f"{index}. "
            f"{prospect.get('name', 'Unknown')} "
            f"— "
            f"{prospect.get('_final_score', 0):.0f}"
        )

    return qualified


# ============================================================
# OUTREACH
# ============================================================

def create_outreach(
    prospect,
    product
):

    print()
    print("=" * 70)
    print("5. OUTREACH DRAFT")
    print("=" * 70)

    generator = OutreachGenerator()

    website_data = prospect.get(
        "_website_research",
        {}
    )

    try:

        draft = generator.generate(
            prospect,
            product,
            website_data
        )

    except TypeError:

        try:

            draft = generator.generate(
                prospect,
                product
            )

        except Exception:

            draft = None

    except Exception:

        draft = None

    if not draft:

        print(
            "⚠️ Could not generate outreach."
        )

        return None

    print()

    if isinstance(
        draft,
        dict
    ):

        print(
            draft.get(
                "message",
                draft.get(
                    "draft",
                    str(draft)
                )
            )
        )

    else:

        print(
            draft
        )

    print()

    print(
        "⚠️ This message has NOT been sent."
    )

    return draft


# ============================================================
# ORDER STORAGE
# ============================================================

def load_orders():

    if not os.path.exists(
        ORDERS_FILE
    ):

        return []

    try:

        with open(
            ORDERS_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(
                file
            )

    except Exception:

        return []


def save_orders(
    orders
):

    with open(
        ORDERS_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            orders,
            file,
            indent=4,
            ensure_ascii=False
        )


# ============================================================
# REAL ORDER
# ============================================================

def create_real_order(
    customer,
    business_name,
    product_name,
    amount
):

    orders = load_orders()

    order = {

        "order_id":
            "ORD-" +
            uuid.uuid4().hex[:10].upper(),

        "customer":
            customer,

        "business_name":
            business_name,

        "product":
            product_name,

        "amount":
            float(amount),

        "currency":
            "USD",

        "status":
            "payment_pending",

        "payment_status":
            "unpaid",

        "delivery_status":
            "not_started",

        "created_at":
            datetime.now().isoformat(),

        "paid_at":
            None,

        "delivered_at":
            None,

        "delivery_file":
            None
    }

    orders.append(
        order
    )

    save_orders(
        orders
    )

    return order


# ============================================================
# DELIVERY
# ============================================================

def deliver_paid_order(
    order
):

    if order.get(
        "payment_status"
    ) != "paid":

        print(
            "❌ Delivery blocked."
        )

        print(
            "Payment has not been verified."
        )

        return None

    os.makedirs(
        DELIVERY_DIR,
        exist_ok=True
    )

    safe_name = (
        order["business_name"]
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
    )

    filename = (
        f'{order["order_id"]}_'
        f'{safe_name}_growth_kit.txt'
    )

    filepath = os.path.join(
        DELIVERY_DIR,
        filename
    )

    content = f"""
LOCAL BUSINESS GROWTH KIT

Customer:
{order["customer"]}

Business:
{order["business_name"]}

Product:
{order["product"]}

Generated:
{datetime.now().isoformat()}

========================================

SOCIAL MEDIA POST IDEAS

1. Introduce your business
2. Showcase a popular product
3. Behind-the-scenes content
4. Customer experience
5. Staff introduction
6. Educational tip
7. Frequently asked question
8. Seasonal promotion
9. Local community post
10. Product spotlight
11. Customer testimonial
12. Special offer


PROMOTIONAL OFFERS

1. New Customer Special
2. Bring a Friend Promotion
3. Limited-Time Local Special
4. Returning Customer Reward


SHORT VIDEO IDEAS

1. 15-second business tour
2. Showcase your best product
3. Behind-the-scenes preparation
4. Answer a common customer question


CALL TO ACTIONS

Visit us today.
Message us for details.
Book your visit.
Try it this week.
Share this with a friend.

========================================
"""

    with open(
        filepath,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            content.strip()
        )

    return filepath


# ============================================================
# MAIN
# ============================================================

def main():

    header()

    business = Business()

    # --------------------------------------------------------
    # MARKET
    # --------------------------------------------------------

    selected = run_market_research()

    if not selected:

        print()
        print(
            "❌ V7 stopped safely."
        )

        return

    # --------------------------------------------------------
    # PRODUCT
    # --------------------------------------------------------

    product = run_product_factory(
        selected
    )

    if not product:

        print()
        print(
            "❌ V7 stopped because no product exists."
        )

        return

    # --------------------------------------------------------
    # CITY
    # --------------------------------------------------------

    print()

    city = input(
        "Enter target city: "
    ).strip()

    if not city:

        print(
            "❌ City cannot be empty."
        )

        return

    # --------------------------------------------------------
    # PROSPECTS
    # --------------------------------------------------------

    prospects = run_prospect_discovery(
        city
    )

    if not prospects:

        print()
        print(
            "No real prospects found."
        )

        print(
            "Revenue remains $0.00."
        )

        return

    # --------------------------------------------------------
    # QUALIFICATION
    # --------------------------------------------------------

    qualified = qualify_prospects(
        prospects
    )

    if not qualified:

        print()
        print(
            "No qualified prospects."
        )

        return

    # --------------------------------------------------------
    # SALES ENGINE
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("6. SALES PIPELINE")
    print("=" * 70)

    sales = SalesEngine()

    added = 0

    for prospect in qualified:

        try:

            if sales.add_prospect(
                prospect,
                product
            ):

                added += 1

        except Exception as error:

            print(
                f"⚠️ Pipeline error: {error}"
            )

    print()

    print(
        f"Added {added} prospects."
    )

    # --------------------------------------------------------
    # BEST PROSPECT
    # --------------------------------------------------------

    best = qualified[0]

    print()
    print("=" * 70)
    print("7. BEST SALES OPPORTUNITY")
    print("=" * 70)

    print()

    print(
        "Business:",
        best.get(
            "name",
            "Unknown"
        )
    )

    print(
        "Category:",
        best.get(
            "category",
            "Unknown"
        )
    )

    print(
        "Score:",
        best.get(
            "_final_score",
            0
        )
    )

    print(
        "Website:",
        best.get(
            "website",
            "Not available"
        )
    )

    # --------------------------------------------------------
    # OUTREACH
    # --------------------------------------------------------

    draft = create_outreach(
        best,
        product
    )

    if draft:

        print()

        approval = input(
            "Approve this outreach? (yes/no): "
        ).strip().lower()

        if approval == "yes":

            sales.update_status(
                best.get("name"),
                "approved"
            )

            print()
            print(
                "✅ Outreach approved."
            )

            print(
                "⚠️ It has NOT been automatically sent."
            )

        else:

            sales.update_status(
                best.get("name"),
                "draft_created"
            )

            print(
                "Outreach rejected."
            )

    # --------------------------------------------------------
    # REAL REVENUE
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("8. REAL PAYMENT STATUS")
    print("=" * 70)

    revenue = verified_revenue()

    print()

    print(
        f"Verified revenue: ${revenue:.2f}"
    )

    print(
        "No payment has been invented."
    )

    # --------------------------------------------------------
    # ORDER SYSTEM
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("9. ORDER + DELIVERY SYSTEM")
    print("=" * 70)

    print()

    print(
        "Order management: READY"
    )

    print(
        "Payment verification: READY"
    )

    print(
        "Delivery generation: READY"
    )

    print(
        "Payment-gated delivery: ENABLED"
    )

    print()

    print(
        "No test order created."
    )

    print(
        "Real order requires a real customer."
    )

    # --------------------------------------------------------
    # MEMORY
    # --------------------------------------------------------

    try:

        add_memory(
            {
                "event": "v7_run",

                "city": city,

                "opportunity":
                    selected[
                        "opportunity"
                    ],

                "opportunity_score":
                    selected[
                        "score"
                    ],

                "qualified_prospects":
                    len(
                        qualified
                    ),

                "verified_revenue":
                    revenue,

                "timestamp":
                    datetime.now().isoformat()
            }
        )

        print()
        print(
            "🧠 AI memory updated."
        )

    except Exception as error:

        print(
            f"⚠️ Memory update failed: {error}"
        )

    # --------------------------------------------------------
    # BUSINESS STATUS
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("10. BUSINESS STATUS")
    print("=" * 70)

    business.status()

    # --------------------------------------------------------
    # PIPELINE
    # --------------------------------------------------------

    pipeline = sales.get_pipeline()

    print()
    print("=" * 70)
    print("11. SALES PIPELINE SUMMARY")
    print("=" * 70)

    print()

    print(
        f"Pipeline records: "
        f"{len(pipeline)}"
    )

    for record in pipeline[-10:]:

        print(
            f"• {record.get('prospect')} | "
            f"{record.get('status')} | "
            f"${record.get('price', 0)}"
        )

    # --------------------------------------------------------
    # FINAL
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("VERSION 7.1 COMPLETE")
    print("=" * 70)

    print()

    print("✅ Real market research")
    print("✅ AI opportunity selection")
    print("✅ AI product factory")
    print("✅ Real prospect discovery")
    print("✅ Prospect qualification")
    print("✅ Website research")
    print("✅ Sales pipeline")
    print("✅ Personalized outreach draft")
    print("✅ Human approval")
    print("✅ Real payment tracking")
    print("✅ Real revenue verification")
    print("✅ Order architecture")
    print("✅ Payment-gated delivery")
    print("✅ Persistent memory")

    print()

    print(
        f"💰 VERIFIED REVENUE: "
        f"${revenue:.2f}"
    )

    print()

    print(
        "Fake revenue: DISABLED"
    )

    print(
        "Fake payments: DISABLED"
    )

    print(
        "Fake customers: DISABLED"
    )

    print()
    print(
        "NEXT:"
    )

    print(
        "VERSION 8 — AI DECISION ENGINE"
    )

    print()


if __name__ == "__main__":

    main()