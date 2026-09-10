import json
import os
import re
from datetime import datetime


class ProductFactory:

    def __init__(self):
        self.output_folder = "generated_products"
        os.makedirs(self.output_folder, exist_ok=True)

    def slugify(self, text):
        return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")

    def build_product(self, opportunity, market_data):
        name = opportunity.lower()

        if "small business marketing" in name:
            product = self.small_business_marketing(market_data)

        elif "social media content" in name:
            product = self.social_media_content(market_data)

        elif "ai automation" in name:
            product = self.ai_automation(market_data)

        elif "presentation design" in name:
            product = self.presentation_design(market_data)

        elif "resume optimization" in name:
            product = self.resume_service(market_data)

        elif "product description" in name:
            product = self.product_descriptions(market_data)

        elif "youtube script" in name:
            product = self.youtube_scripts(market_data)

        elif "short video script" in name:
            product = self.short_video_scripts(market_data)

        else:
            product = self.generic_service(opportunity, market_data)

        return product

    def small_business_marketing(self, data):
        return {
            "product_name": "Local Business Growth Kit",
            "type": "Digital Marketing Service",
            "target_customer": "Small local businesses",
            "problem": (
                "Many small businesses struggle to consistently create "
                "marketing content and attract attention online."
            ),
            "solution": (
                "A simple monthly marketing package that gives the business "
                "ready-to-use social media and promotional content."
            ),
            "deliverables": [
                "12 social media post ideas",
                "12 ready-to-use captions",
                "4 promotional offers",
                "4 short-form video ideas",
                "1 monthly content calendar",
                "Basic competitor content analysis",
                "Call-to-action suggestions"
            ],
            "delivery": "Digital delivery within 48 hours",
            "starter_price": 35,
            "upsell_price": 75,
            "estimated_cost": 0,
            "gross_margin_before_fees": 100,
            "sales_pitch": (
                "Get a month of ready-to-use marketing content without "
                "hiring an expensive marketing agency."
            ),
            "customer_benefit": [
                "Saves time",
                "Consistent online presence",
                "Ready-to-post content",
                "Affordable compared with an agency"
            ],
            "call_to_action": (
                "Want me to create a free sample post for your business?"
            ),
            "demo": (
                "Create one example social media post for the prospect's "
                "actual business."
            )
        }

    def social_media_content(self, data):
        return {
            "product_name": "30-Day Social Content Pack",
            "type": "Digital Content Service",
            "target_customer": "Small businesses and creators",
            "problem": "Customers struggle to consistently publish engaging content.",
            "solution": "A complete month of social media content prepared for the customer.",
            "deliverables": [
                "30 post ideas",
                "30 captions",
                "10 hooks",
                "10 short-video concepts",
                "Hashtag suggestions",
                "30-day content calendar"
            ],
            "delivery": "Digital delivery within 48 hours",
            "starter_price": 30,
            "upsell_price": 65,
            "estimated_cost": 0,
            "gross_margin_before_fees": 100,
            "sales_pitch": (
                "Stop wondering what to post. Get 30 days of social content "
                "planned and written for your business."
            ),
            "customer_benefit": [
                "Save content creation time",
                "Post consistently",
                "More content ideas",
                "Simple ready-to-use system"
            ],
            "call_to_action": "Want a free sample post based on your business?",
            "demo": "Create three sample posts for the prospect."
        }

    def ai_automation(self, data):
        return {
            "product_name": "Small Business AI Automation Starter",
            "type": "AI Consulting / Automation Service",
            "target_customer": "Small businesses performing repetitive tasks",
            "problem": "Businesses waste time repeating simple manual tasks.",
            "solution": "Identify repetitive workflows and design practical AI-assisted automation.",
            "deliverables": [
                "Business workflow audit",
                "3 automation opportunities",
                "AI workflow designs",
                "Prompt templates",
                "Implementation instructions",
                "Basic automation roadmap"
            ],
            "delivery": "Digital report within 72 hours",
            "starter_price": 50,
            "upsell_price": 150,
            "estimated_cost": 0,
            "gross_margin_before_fees": 100,
            "sales_pitch": (
                "I'll identify three repetitive tasks in your business "
                "that could potentially be reduced with AI."
            ),
            "customer_benefit": [
                "Save employee time",
                "Reduce repetitive work",
                "Discover practical AI use cases"
            ],
            "call_to_action": "Want a free automation opportunity analysis?",
            "demo": "Show one workflow before/after automation."
        }

    def presentation_design(self, data):
        return {
            "product_name": "Professional Presentation Starter",
            "type": "Presentation Design Service",
            "target_customer": "Students, entrepreneurs and small businesses",
            "problem": "Customers often have information but lack a professional presentation.",
            "solution": "Transform supplied information into a clear presentation structure.",
            "deliverables": [
                "Up to 10 slides",
                "Professional slide structure",
                "Titles and supporting text",
                "Visual suggestions",
                "Speaker notes",
                "Final presentation-ready content"
            ],
            "delivery": "Digital delivery within 48 hours",
            "starter_price": 30,
            "upsell_price": 60,
            "estimated_cost": 0,
            "gross_margin_before_fees": 100,
            "sales_pitch": (
                "Give me your raw information and I'll turn it into "
                "a clear, professional presentation."
            ),
            "customer_benefit": [
                "Save preparation time",
                "Clearer communication",
                "Professional structure"
            ],
            "call_to_action": "Want me to create one free sample slide?",
            "demo": "Transform one paragraph of customer information into a sample slide."
        }

    def resume_service(self, data):
        return {
            "product_name": "Job-Ready Resume Upgrade",
            "type": "Resume Writing Service",
            "target_customer": "Job seekers",
            "problem": "Many applicants have resumes that poorly communicate their experience.",
            "solution": "Improve structure, wording and clarity while preserving truthful information.",
            "deliverables": [
                "Resume structure review",
                "Professional wording improvements",
                "Achievement-focused bullet suggestions",
                "ATS-friendly formatting guidance",
                "One revision"
            ],
            "delivery": "Digital delivery within 48 hours",
            "starter_price": 30,
            "upsell_price": 60,
            "estimated_cost": 0,
            "gross_margin_before_fees": 100,
            "sales_pitch": (
                "Turn your existing resume into a clearer, more professional "
                "version without inventing experience."
            ),
            "customer_benefit": [
                "Clearer resume",
                "Better presentation of experience",
                "ATS-friendly structure"
            ],
            "call_to_action": "Want a free review of one section of your resume?",
            "demo": "Rewrite one supplied resume section as a sample."
        }

    def product_descriptions(self, data):
        return {
            "product_name": "E-Commerce Product Description Pack",
            "type": "Copywriting Service",
            "target_customer": "Online stores",
            "problem": "Poor product descriptions can make products harder to understand and compare.",
            "solution": "Create clear, persuasive descriptions based only on supplied product facts.",
            "deliverables": [
                "10 product descriptions",
                "SEO-friendly titles",
                "Feature-to-benefit conversion",
                "Bullet-point highlights",
                "Calls to action"
            ],
            "delivery": "Digital delivery within 48 hours",
            "starter_price": 35,
            "upsell_price": 75,
            "estimated_cost": 0,
            "gross_margin_before_fees": 100,
            "sales_pitch": (
                "Give your products clearer descriptions that explain "
                "what they are and why customers should care."
            ),
            "customer_benefit": [
                "Save writing time",
                "Consistent product pages",
                "Clearer product information"
            ],
            "call_to_action": "Want one free product description sample?",
            "demo": "Rewrite one existing product description."
        }

    def youtube_scripts(self, data):
        return {
            "product_name": "YouTube Video Script Starter",
            "type": "Scriptwriting Service",
            "target_customer": "YouTubers and businesses",
            "problem": "Creators often struggle to structure videos and maintain viewer interest.",
            "solution": "Create structured scripts based on the customer's topic and audience.",
            "deliverables": [
                "One video script",
                "Opening hook",
                "Main structure",
                "Transitions",
                "Call to action",
                "Title ideas"
            ],
            "delivery": "Digital delivery within 48 hours",
            "starter_price": 25,
            "upsell_price": 55,
            "estimated_cost": 0,
            "gross_margin_before_fees": 100,
            "sales_pitch": (
                "Give me your topic and I'll turn it into a structured "
                "YouTube script with a strong opening."
            ),
            "customer_benefit": [
                "Save writing time",
                "Better video structure",
                "More content ideas"
            ],
            "call_to_action": "Want me to write a free 30-second opening?",
            "demo": "Create a short opening based on the prospect's topic."
        }

    def short_video_scripts(self, data):
        return {
            "product_name": "30 Short-Video Script Pack",
            "type": "Short-Form Scriptwriting",
            "target_customer": "Creators and small businesses",
            "problem": "Creating fresh short-video ideas every day is difficult.",
            "solution": "Provide short scripts designed around the customer's niche and audience.",
            "deliverables": [
                "30 video ideas",
                "30 hooks",
                "30 short scripts",
                "30 calls to action",
                "Content calendar"
            ],
            "delivery": "Digital delivery within 72 hours",
            "starter_price": 35,
            "upsell_price": 75,
            "estimated_cost": 0,
            "gross_margin_before_fees": 100,
            "sales_pitch": (
                "Get 30 short-video ideas and scripts so you always "
                "know what to publish next."
            ),
            "customer_benefit": [
                "30 days of content",
                "Save brainstorming time",
                "Consistent publishing"
            ],
            "call_to_action": "Want me to create 3 free hooks for your niche?",
            "demo": "Create three hooks based on the prospect's niche."
        }

    def generic_service(self, opportunity, data):
        return {
            "product_name": opportunity.title() + " Starter",
            "type": "Digital Service",
            "target_customer": "Customers interested in " + opportunity,
            "problem": "Customers need help with " + opportunity,
            "solution": "Provide a practical digital service for " + opportunity,
            "deliverables": [
                "Initial analysis",
                "Customized recommendations",
                "Digital deliverable",
                "One revision"
            ],
            "delivery": "Digital delivery within 72 hours",
            "starter_price": 25,
            "upsell_price": 50,
            "estimated_cost": 0,
            "gross_margin_before_fees": 100,
            "sales_pitch": "Affordable help with " + opportunity,
            "customer_benefit": [
                "Save time",
                "Get a customized result",
                "Affordable service"
            ],
            "call_to_action": "Would you like a free sample?",
            "demo": "Create a small sample deliverable."
        }

    def save_product(self, product):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = self.slugify(product["product_name"])

        filename = f"{slug}_{timestamp}.json"
        path = os.path.join(self.output_folder, filename)

        with open(path, "w", encoding="utf-8") as file:
            json.dump(product, file, indent=4, ensure_ascii=False)

        return path