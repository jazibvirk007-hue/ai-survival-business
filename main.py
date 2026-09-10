"""AI SURVIVAL BUSINESS - VERSION 7.3

Real-business engine with zero starting capital.
No fake sales, fake payments, fake customers, or automatic spam.
"""

import json
import os
import re
import uuid
from datetime import datetime

from business import Business
from market_research import MarketResearch
from memory import add_memory
from outreach import OutreachGenerator
from payment_tracker import verified_payments, verified_revenue
from product_factory import ProductFactory
from prospect_research import ProspectResearcher
from prospect_scoring import ProspectScorer
from sales_engine import SalesEngine
from website_research import WebsiteResearcher

OPPORTUNITIES = [
    "short video script service",
    "social media content service",
    "resume optimization service",
    "small business marketing service",
    "AI automation service",
    "YouTube script writing service",
    "product description writing service",
    "presentation design service",
]

ORDERS_FILE = "orders.json"
DELIVERY_DIR = "deliveries"


def header():
    print("\n" + "=" * 70)
    print("             AI SURVIVAL BUSINESS")
    print("             VERSION 7.3")
    print("=" * 70)
    print("\nStarting capital: $0.00")
    print("Fake sales: DISABLED")
    print("Fake payments: DISABLED")
    print("Revenue simulation: DISABLED")
    print("Automatic spam: DISABLED\n")


def run_market_research():
    print("=" * 70)
    print("1. AI MARKET RESEARCH")
    print("=" * 70)
    try:
        researcher = MarketResearch()
        results = researcher.research_opportunities(OPPORTUNITIES)
        ranked = researcher.rank(results or [])
    except Exception as error:
        print(f"❌ Market research failed: {type(error).__name__}: {error}")
        return None

    if not ranked:
        print("❌ No research results. The AI will not invent an opportunity.")
        return None

    for index, result in enumerate(ranked, 1):
        print(f"{index}. {result.get('opportunity', 'Unknown')}")
        print(f"   Articles: {result.get('articles', 0)}")
        print(f"   Demand: {result.get('demand', 0)}%")
        print(f"   Commercial: {result.get('commercial', 0)}%")
        print(f"   Competition: {result.get('competition', 0)}%")
        print(f"   Trend: {result.get('trend', 0)}%")
        print(f"   Research Score: {result.get('score', 0)}/100\n")

    selected = ranked[0]
    print("=" * 70)
    print("🧠 RESEARCH-BASED SELECTION")
    print("=" * 70)
    print(f"Selected opportunity: 👉 {selected.get('opportunity')}")
    print(f"Research score: {selected.get('score', 0)}/100")
    print("Note: headline signals are market indicators, not proof of customer demand.\n")
    return selected


def run_product_factory(selected):
    print("=" * 70)
    print("2. AI PRODUCT FACTORY")
    print("=" * 70)
    try:
        factory = ProductFactory()
        product = factory.build_product(selected["opportunity"], selected)
        path = factory.save_product(product)
    except Exception as error:
        print(f"❌ Product factory failed: {type(error).__name__}: {error}")
        return None

    print(f"Product: {product.get('product_name', 'Unknown')}")
    print(f"Target: {product.get('target_customer', 'Unknown')}")
    print(f"Price: ${float(product.get('starter_price', 0)):.2f}")
    print(f"Cost: ${float(product.get('estimated_cost', 0)):.2f}")
    print(f"Saved: {path}\n")
    return product


def run_prospect_discovery(city):
    print("=" * 70)
    print("3. CUSTOMER ACQUISITION")
    print("=" * 70)
    try:
        prospects = ProspectResearcher().find_businesses(city, limit=30)
    except Exception as error:
        print(f"❌ Prospect search failed: {type(error).__name__}: {error}")
        return []
    print(f"Raw prospects found: {len(prospects)}")
    return prospects


def research_website(prospect):
    try:
        return WebsiteResearcher().research(prospect)
    except Exception as error:
        return {
            "success": False,
            "website": prospect.get("website", ""),
            "title": "",
            "text_length": 0,
            "signals": {},
            "reason": f"{type(error).__name__}: {error}",
        }


def qualify_prospects(prospects):
    print("\n" + "=" * 70)
    print("4. PROSPECT QUALIFICATION")
    print("=" * 70)

    scorer = ProspectScorer()
    qualified = []
    total = len(prospects)

    for index, prospect in enumerate(prospects, 1):
        name = prospect.get("name", "Unknown")
        print(f"[{index}/{total}] Analyzing: {name}")
        website_data = research_website(prospect)

        try:
            score_data = scorer.score(prospect, website_data)
        except Exception as error:
            print(f"   ⚠ Scoring error: {type(error).__name__}: {error}")
            score_data = {"score": 0, "priority": "LOW", "reasons": ["Scoring failed."]}

        result = dict(prospect)
        result.update(score_data if isinstance(score_data, dict) else {})
        result["_website_research"] = website_data
        try:
            score = float(result.get("score", result.get("prospect_score", 0)) or 0)
        except (TypeError, ValueError):
            score = 0.0
        result["_final_score"] = score

        print(f"   Score: {score:.0f}/100 | Priority: {result.get('priority', 'LOW')}")
        if website_data.get("reason"):
            print(f"   Website: {website_data['reason']}")
        if score >= 50:
            qualified.append(result)

    qualified.sort(key=lambda item: item.get("_final_score", 0), reverse=True)
    print(f"\nQualified prospects: {len(qualified)}")
    for index, prospect in enumerate(qualified[:20], 1):
        print(f"{index}. {prospect.get('name', 'Unknown')} — {prospect.get('_final_score', 0):.0f}")
    return qualified


def create_outreach(prospect, product):
    print("\n" + "=" * 70)
    print("5. OUTREACH DRAFT")
    print("=" * 70)
    try:
        draft = OutreachGenerator().generate(
            prospect, product, prospect.get("_website_research", {})
        )
    except Exception as error:
        print(f"❌ Outreach generation failed: {type(error).__name__}: {error}")
        return None

    message = draft.get("message", str(draft)) if isinstance(draft, dict) else str(draft)
    print("\n" + message)
    print("\n⚠️ This message has NOT been sent.")
    return draft


def load_orders():
    if not os.path.exists(ORDERS_FILE):
        return []
    try:
        with open(ORDERS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, list) else []
    except (OSError, ValueError, TypeError):
        return []


def save_orders(orders):
    if not isinstance(orders, list):
        raise TypeError("orders must be a list")
    with open(ORDERS_FILE, "w", encoding="utf-8") as file:
        json.dump(orders, file, indent=4, ensure_ascii=False)


def create_real_order(customer, business_name, product_name, amount):
    amount = float(amount)
    if amount <= 0:
        raise ValueError("order amount must be greater than zero")
    order = {
        "order_id": "ORD-" + uuid.uuid4().hex[:10].upper(),
        "customer": customer,
        "business_name": business_name,
        "product": product_name,
        "amount": amount,
        "currency": "USD",
        "status": "payment_pending",
        "payment_status": "unpaid",
        "delivery_status": "not_started",
        "created_at": datetime.now().isoformat(),
        "paid_at": None,
        "delivered_at": None,
        "delivery_file": None,
    }
    orders = load_orders()
    orders.append(order)
    save_orders(orders)
    return order


def _safe_filename(value):
    value = re.sub(r"[^a-zA-Z0-9._-]+", "_", str(value)).strip("._")
    return value[:80] or "customer"


def deliver_paid_order(order):
    if order.get("payment_status") != "paid":
        print("❌ Delivery blocked: payment has not been independently verified.")
        return None

    os.makedirs(DELIVERY_DIR, exist_ok=True)
    filename = f"{order['order_id']}_{_safe_filename(order.get('business_name'))}_growth_kit.txt"
    filepath = os.path.join(DELIVERY_DIR, filename)
    content = f"""LOCAL BUSINESS GROWTH KIT

Customer: {order.get('customer', '')}
Business: {order.get('business_name', '')}
Product: {order.get('product', '')}
Generated: {datetime.now().isoformat()}

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
"""
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(content.strip())
    return filepath


def main():
    header()
    business = Business()

    selected = run_market_research()
    if not selected:
        return

    product = run_product_factory(selected)
    if not product:
        return

    city = input("Enter target city: ").strip()
    if not city:
        print("❌ City cannot be empty.")
        return

    prospects = run_prospect_discovery(city)
    if not prospects:
        print("No real prospects found. Revenue remains $0.00.")
        return

    qualified = qualify_prospects(prospects)
    if not qualified:
        print("No qualified prospects. Revenue remains $0.00.")
        return

    print("\n" + "=" * 70)
    print("6. SALES PIPELINE")
    print("=" * 70)
    sales = SalesEngine()
    added = 0
    for prospect in qualified:
        try:
            if sales.add_prospect(prospect, product):
                added += 1
        except Exception as error:
            print(f"⚠️ Pipeline error for {prospect.get('name')}: {error}")
    print(f"Added {added} new prospects.")

    best = qualified[0]
    print("\n" + "=" * 70)
    print("7. BEST SALES OPPORTUNITY")
    print("=" * 70)
    print(f"Business: {best.get('name', 'Unknown')}")
    print(f"Category: {best.get('category', 'Unknown')}")
    print(f"Score: {best.get('_final_score', 0):.0f}/100")
    print(f"Website: {best.get('website') or 'Not available'}")

    draft = create_outreach(best, product)
    if draft:
        approval = input("Approve this outreach? (yes/no): ").strip().lower()
        if approval == "yes":
            sales.update_status(best.get("name"), "approved")
            print("✅ Outreach approved for manual sending; it was NOT sent automatically.")
        else:
            sales.update_status(best.get("name"), "draft_created")
            print("Outreach left as draft.")

    revenue = verified_revenue()
    payments = verified_payments()
    business.sync_verified_financials(revenue, len(payments))

    print("\n" + "=" * 70)
    print("8. REAL PAYMENT STATUS")
    print("=" * 70)
    print(f"Verified payments: {len(payments)}")
    print(f"Verified revenue: ${revenue:.2f}")
    print("No payment has been invented.")

    print("\n" + "=" * 70)
    print("9. ORDER + DELIVERY SYSTEM")
    print("=" * 70)
    print("Order record creation: READY")
    print("Payment request tracking: READY")
    print("Payment verification: MANUAL CONFIRMATION ONLY")
    print("Delivery generation: READY")
    print("Payment-gated delivery: ENABLED")
    print("Real gateway/webhook: NOT CONNECTED YET")
    print("No test order created.")

    try:
        add_memory({
            "event": "business_run",
            "version": "7.3",
            "city": city,
            "opportunity": selected.get("opportunity"),
            "opportunity_score": selected.get("score", 0),
            "prospects_found": len(prospects),
            "qualified_prospects": len(qualified),
            "verified_payments": len(payments),
            "verified_revenue": revenue,
            "timestamp": datetime.now().isoformat(),
        })
        print("🧠 AI memory updated.")
    except Exception as error:
        print(f"⚠️ Memory update failed: {error}")

    print("\n" + "=" * 70)
    print("10. BUSINESS STATUS")
    print("=" * 70)
    business.status()

    pipeline = sales.get_pipeline()
    print("\n" + "=" * 70)
    print("11. SALES PIPELINE SUMMARY")
    print("=" * 70)
    print(f"Pipeline records: {len(pipeline)}")
    for record in pipeline[-10:]:
        print(f"• {record.get('prospect')} | {record.get('status')} | ${record.get('price', 0)}")

    print("\n" + "=" * 70)
    print("VERSION 7.3 COMPLETE")
    print("=" * 70)
    print("✅ Market research with explicit evidence limitation")
    print("✅ Product generation + persistence")
    print("✅ Public prospect discovery")
    print("✅ Website research")
    print("✅ Prospect scoring with preserved prospect data")
    print("✅ Hardened sales pipeline persistence")
    print("✅ Outreach generation + human approval")
    print("✅ Verified-payment-only revenue")
    print("✅ Transaction replay protection")
    print("✅ Payment-gated delivery architecture")
    print("✅ Persistent memory")
    print(f"\n💰 VERIFIED REVENUE: ${revenue:.2f}")
    print("\nNext milestone: real payment-provider/webhook integration and the control-center UI.")


if __name__ == "__main__":
    main()
