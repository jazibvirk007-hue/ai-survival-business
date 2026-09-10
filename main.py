"""AI SURVIVAL BUSINESS - VERSION 7.4

Real-business engine with zero starting capital.
No fake sales, fake payments, fake customers, or automatic spam.
"""

import os
import re
import uuid
from datetime import datetime

from business import Business
from market_research import MarketResearch
from memory import add_memory
from order_engine import create_order, mark_delivered, verify_order_payment
from outreach import OutreachGenerator
from payment_tracker import verified_payments, verified_revenue
from product_factory import ProductFactory
from prospect_research import ProspectResearcher
from prospect_scoring import ProspectScorer
from sales_engine import SalesEngine
from website_research import WebsiteResearcher

OPPORTUNITIES = [
    "short video script service", "social media content service",
    "resume optimization service", "small business marketing service",
    "AI automation service", "YouTube script writing service",
    "product description writing service", "presentation design service",
]


def header():
    print("\n" + "=" * 70)
    print("             AI SURVIVAL BUSINESS")
    print("             VERSION 7.4")
    print("=" * 70)
    print("\nStarting capital: $0.00")
    print("Fake sales: DISABLED")
    print("Fake payments: DISABLED")
    print("Revenue simulation: DISABLED")
    print("Automatic spam: DISABLED\n")


def run_market_research():
    print("=" * 70); print("1. AI MARKET RESEARCH"); print("=" * 70)
    try:
        ranked = MarketResearch().rank(MarketResearch().research_opportunities(OPPORTUNITIES) or [])
    except Exception as error:
        print(f"❌ Market research failed: {type(error).__name__}: {error}"); return None
    if not ranked:
        print("❌ No research results. The AI will not invent an opportunity."); return None
    for i, r in enumerate(ranked, 1):
        print(f"{i}. {r.get('opportunity', 'Unknown')} | Score: {r.get('score', 0)}/100 | Demand: {r.get('demand', 0)}% | Commercial: {r.get('commercial', 0)}% | Competition: {r.get('competition', 0)}% | Trend: {r.get('trend', 0)}%")
    selected = ranked[0]
    print(f"\nSelected opportunity: 👉 {selected.get('opportunity')}")
    print("Note: headline signals are market indicators, not proof of customer demand.\n")
    return selected


def run_product_factory(selected):
    print("=" * 70); print("2. AI PRODUCT FACTORY"); print("=" * 70)
    try:
        factory = ProductFactory()
        product = factory.build_product(selected["opportunity"], selected)
        path = factory.save_product(product)
    except Exception as error:
        print(f"❌ Product factory failed: {type(error).__name__}: {error}"); return None
    print(f"Product: {product.get('product_name', 'Unknown')}")
    print(f"Target: {product.get('target_customer', 'Unknown')}")
    print(f"Price: ${float(product.get('starter_price', 0)):.2f}")
    print(f"Cost: ${float(product.get('estimated_cost', 0)):.2f}")
    print(f"Saved: {path}\n")
    return product


def run_prospect_discovery(city):
    print("=" * 70); print("3. CUSTOMER ACQUISITION"); print("=" * 70)
    try:
        prospects = ProspectResearcher().find_businesses(city, limit=30)
    except Exception as error:
        print(f"❌ Prospect search failed: {type(error).__name__}: {error}"); return []
    print(f"Raw prospects found: {len(prospects)}")
    return prospects


def research_website(prospect):
    try:
        return WebsiteResearcher().research(prospect)
    except Exception as error:
        return {"success": False, "website": prospect.get("website", ""), "title": "", "text_length": 0, "signals": {}, "reason": f"{type(error).__name__}: {error}"}


def qualify_prospects(prospects):
    print("\n" + "=" * 70); print("4. PROSPECT QUALIFICATION"); print("=" * 70)
    scorer, qualified = ProspectScorer(), []
    for index, prospect in enumerate(prospects, 1):
        print(f"[{index}/{len(prospects)}] Analyzing: {prospect.get('name', 'Unknown')}")
        website_data = research_website(prospect)
        try: score_data = scorer.score(prospect, website_data)
        except Exception as error: score_data = {"score": 0, "priority": "LOW", "reasons": [f"Scoring failed: {error}"]}
        result = dict(prospect); result.update(score_data if isinstance(score_data, dict) else {}); result["_website_research"] = website_data
        try: score = float(result.get("score", result.get("prospect_score", 0)) or 0)
        except (TypeError, ValueError): score = 0.0
        result["_final_score"] = score
        print(f"   Score: {score:.0f}/100 | Priority: {result.get('priority', 'LOW')}")
        if score >= 50: qualified.append(result)
    qualified.sort(key=lambda x: x.get("_final_score", 0), reverse=True)
    print(f"\nQualified prospects: {len(qualified)}")
    return qualified


def create_outreach(prospect, product):
    print("\n" + "=" * 70); print("5. OUTREACH DRAFT"); print("=" * 70)
    try: draft = OutreachGenerator().generate(prospect, product, prospect.get("_website_research", {}))
    except Exception as error:
        print(f"❌ Outreach generation failed: {type(error).__name__}: {error}"); return None
    message = draft.get("message", str(draft)) if isinstance(draft, dict) else str(draft)
    print("\n" + message); print("\n⚠️ This message has NOT been sent.")
    return draft


def create_business_order(prospect, product):
    """Create a real payment-pending order; this never creates revenue."""
    order_id = "ORD-" + uuid.uuid4().hex[:10].upper()
    return create_order(order_id, prospect.get("name", ""), prospect.get("name", ""), product.get("product_name", "Digital product"), float(product.get("starter_price", 0)))


def verify_business_order(order_id, transaction_id):
    """Trusted confirmation hook for a provider/webhook or controlled human workflow."""
    return verify_order_payment(order_id, transaction_id, confirmed=True)


def deliver_business_order(order_id, delivery_file):
    """Record delivery only after order_engine confirms the order is paid."""
    return mark_delivered(order_id, delivery_file)


def main():
    header(); business = Business()
    selected = run_market_research()
    if not selected: return
    product = run_product_factory(selected)
    if not product: return

    city = input("Enter target city: ").strip()
    if not city: print("❌ City cannot be empty."); return
    prospects = run_prospect_discovery(city)
    if not prospects: print("No real prospects found. Revenue remains $0.00."); return
    qualified = qualify_prospects(prospects)
    if not qualified: print("No qualified prospects. Revenue remains $0.00."); return

    print("\n" + "=" * 70); print("6. SALES PIPELINE"); print("=" * 70)
    sales = SalesEngine(); added = 0
    for prospect in qualified:
        try:
            if sales.add_prospect(prospect, product): added += 1
        except Exception as error: print(f"⚠️ Pipeline error for {prospect.get('name')}: {error}")
    print(f"Added {added} new prospects.")

    best = qualified[0]
    print("\n" + "=" * 70); print("7. BEST SALES OPPORTUNITY"); print("=" * 70)
    print(f"Business: {best.get('name', 'Unknown')} | Category: {best.get('category', 'Unknown')} | Score: {best.get('_final_score', 0):.0f}/100")
    draft = create_outreach(best, product)
    if draft:
        approval = input("Approve this outreach? (yes/no): ").strip().lower()
        if approval == "yes":
            sales.update_status(best.get("name"), "approved")
            print("✅ Outreach approved for manual sending; it was NOT sent automatically.")
        else:
            sales.update_status(best.get("name"), "draft_created")

    revenue, payments = verified_revenue(), verified_payments()
    business.sync_verified_financials(revenue, len(payments))
    print("\n" + "=" * 70); print("8. REAL PAYMENT STATUS"); print("=" * 70)
    print(f"Verified payments: {len(payments)}"); print(f"Verified revenue: ${revenue:.2f}"); print("No payment has been invented.")

    print("\n" + "=" * 70); print("9. V7.4 ORDER LIFECYCLE"); print("=" * 70)
    print("Order creation: READY")
    print("Payment request: CREATED WITH ORDER")
    print("Payment verification: INDEPENDENT CONFIRMATION REQUIRED")
    print("Paid state synchronization: ENABLED")
    print("Delivery gate: PAYMENT REQUIRED")
    print("Real provider/webhook: NOT CONNECTED YET")
    print("No test order created.")

    try:
        add_memory({"event": "business_run", "version": "7.4", "city": city, "opportunity": selected.get("opportunity"), "opportunity_score": selected.get("score", 0), "prospects_found": len(prospects), "qualified_prospects": len(qualified), "verified_payments": len(payments), "verified_revenue": revenue, "timestamp": datetime.now().isoformat()})
        print("🧠 AI memory updated.")
    except Exception as error: print(f"⚠️ Memory update failed: {error}")

    print("\n" + "=" * 70); print("10. BUSINESS STATUS"); print("=" * 70); business.status()
    pipeline = sales.get_pipeline()
    print("\n" + "=" * 70); print("11. SALES PIPELINE SUMMARY"); print("=" * 70)
    print(f"Pipeline records: {len(pipeline)}")
    for record in pipeline[-10:]: print(f"• {record.get('prospect')} | {record.get('status')} | ${record.get('price', 0)}")

    print("\n" + "=" * 70); print("VERSION 7.4 COMPLETE"); print("=" * 70)
    print("✅ Research → product → prospects → qualification → outreach")
    print("✅ Verified-payment-only revenue")
    print("✅ Payment-gated order lifecycle")
    print("✅ Paid-state synchronization")
    print("✅ Delivery cannot occur before payment")
    print(f"\n💰 VERIFIED REVENUE: ${revenue:.2f}")
    print("\nNext milestone: connect a real payment provider/webhook, then build the control-center UI.")


if __name__ == "__main__": main()
