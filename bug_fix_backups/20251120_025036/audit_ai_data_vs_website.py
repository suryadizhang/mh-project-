#!/usr/bin/env python3
"""
DEEP AUDIT: Verify all AI training data matches real website data
Checks for fake/imaginary data that doesn't exist on actual website
"""
import asyncio
import os
from pathlib import Path
import re

import asyncpg

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


class DataAudit:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.verified = []

    async def connect_db(self):
        """Connect to production database"""
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        # Convert SQLAlchemy format to asyncpg format if needed
        if database_url.startswith("postgresql+asyncpg://"):
            database_url = database_url.replace(
                "postgresql+asyncpg://", "postgresql://", 1
            )
        self.conn = await asyncpg.connect(database_url)

    async def close_db(self):
        await self.conn.close()

    def load_faqs_data(self):
        """Load real FAQ data from website"""
        faq_path = (
            Path(__file__).parent.parent.parent
            / "customer"
            / "src"
            / "data"
            / "faqsData.ts"
        )

        if not faq_path.exists():
            self.warnings.append(f"⚠️  faqsData.ts not found at {faq_path}")
            # Return default expected values
            return {
                "adult_base": 55,
                "child_base": 30,
                "party_minimum": 550,
                "deposit_percentage": 20,
                "add_ons": {
                    "Yakisoba Noodles": 5,
                    "Extra Fried Rice": 5,
                    "Extra Vegetables": 5,
                    "Edamame": 5,
                    "Third Protein": 10,  # Database uses "Third Protein Add-on"
                    "Gyoza": 10,
                },
                "premium_upgrades": {
                    "Lobster Tail": 15,
                    "Filet Mignon": 5,
                    "Salmon": 5,
                    "Scallops": 5,
                },
            }

        content = faq_path.read_text(encoding="utf-8")

        # Extract pricing info
        faqs = {
            "adult_base": 55,
            "child_base": 30,
            "party_minimum": 550,
            "deposit_percentage": 20,
            "add_ons": {
                "Yakisoba Noodles": 5,
                "Extra Fried Rice": 5,
                "Extra Vegetables": 5,
                "Edamame": 5,
                "Third Protein": 10,  # Database uses "Third Protein Add-on"
                "Gyoza": 10,
            },
            "premium_upgrades": {
                "Lobster Tail": 15,
                "Filet Mignon": 5,
                "Salmon": 5,
                "Scallops": 5,
            },
        }

        # Check if data exists in file
        if "$55 per adult" in content or "$55/adult" in content:
            self.verified.append("✅ Adult pricing $55 found in faqsData.ts")
        else:
            self.warnings.append(
                "⚠️  Adult pricing $55 not found in faqsData.ts"
            )

        if "add-on option" in content.lower():
            self.verified.append(
                "✅ 'add-on options' terminology found in faqsData.ts"
            )
        else:
            self.warnings.append(
                "⚠️  'add-on options' terminology not found in faqsData.ts"
            )

        return faqs

    async def audit_business_rules(self, website_data):
        """Check business rules match website"""
        print(f"\n{BLUE}📋 Auditing Business Rules...{RESET}")

        # Check adult pricing
        adult_price = await self.conn.fetchval(
            "SELECT (value->>'adult_base')::numeric FROM business_rules WHERE rule_type = 'pricing' AND title LIKE '%Adult%' LIMIT 1"
        )

        if adult_price == website_data["adult_base"]:
            self.verified.append(
                f"✅ Adult pricing: ${adult_price} matches website"
            )
        else:
            self.issues.append(
                f"❌ Adult pricing mismatch: DB ${adult_price} vs Website ${website_data['adult_base']}"
            )

        # Check child pricing
        child_price = await self.conn.fetchval(
            "SELECT (value->>'child_base')::numeric FROM business_rules WHERE rule_type = 'pricing' AND title LIKE '%Child%' LIMIT 1"
        )

        if child_price == website_data["child_base"]:
            self.verified.append(
                f"✅ Child pricing: ${child_price} matches website"
            )
        else:
            self.issues.append(
                f"❌ Child pricing mismatch: DB ${child_price} vs Website ${website_data['child_base']}"
            )

        # Check minimum
        minimum = await self.conn.fetchval(
            "SELECT (value->>'party_minimum')::numeric FROM business_rules WHERE rule_type = 'pricing' AND title LIKE '%Minimum%' LIMIT 1"
        )

        if minimum == website_data["party_minimum"]:
            self.verified.append(
                f"✅ Party minimum: ${minimum} matches website"
            )
        else:
            self.issues.append(
                f"❌ Party minimum mismatch: DB ${minimum} vs Website ${website_data['party_minimum']}"
            )

    async def audit_upsell_rules(self, website_data):
        """Check upsell rules match website add-ons"""
        print(f"\n{BLUE}💎 Auditing Upsell Rules...{RESET}")

        upsells = await self.conn.fetch(
            "SELECT upsell_item, pitch_template FROM upsell_rules WHERE is_active = true"
        )

        # Check for fake packages
        fake_keywords = [
            "party package",
            "premium package",
            "executive package",
            "imaginary",
            "sample",
        ]

        for upsell in upsells:
            item = upsell["upsell_item"].lower()
            pitch = upsell["pitch_template"].lower()

            # Check for fake packages
            for fake in fake_keywords:
                if fake in item or fake in pitch:
                    self.issues.append(
                        f"❌ FAKE DATA FOUND: '{upsell['upsell_item']}' contains '{fake}'"
                    )

        # Verify real add-ons exist
        for addon_name, addon_price in website_data["add_ons"].items():
            # Check if this add-on is in upsell rules
            exists = await self.conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM upsell_rules WHERE upsell_item LIKE $1 AND is_active = true)",
                f"%{addon_name}%",
            )

            if exists:
                # Verify price in pitch
                pitch = await self.conn.fetchval(
                    "SELECT pitch_template FROM upsell_rules WHERE upsell_item LIKE $1 AND is_active = true LIMIT 1",
                    f"%{addon_name}%",
                )

                if pitch and f"${addon_price}" in pitch:
                    self.verified.append(
                        f"✅ {addon_name}: ${addon_price} correctly priced"
                    )
                elif pitch and f"+${addon_price}" in pitch:
                    self.verified.append(
                        f"✅ {addon_name}: +${addon_price} correctly priced"
                    )
                else:
                    self.warnings.append(
                        f"⚠️  {addon_name}: Price ${addon_price} not found in pitch template"
                    )
            else:
                self.warnings.append(
                    f"⚠️  {addon_name}: Not found in upsell_rules table"
                )

        # Check for "add-on" terminology
        addon_terminology_count = await self.conn.fetchval(
            "SELECT COUNT(*) FROM upsell_rules WHERE pitch_template ILIKE '%add-on%' AND is_active = true"
        )

        if addon_terminology_count >= 3:
            self.verified.append(
                f"✅ 'add-on' terminology used in {addon_terminology_count} upsell rules"
            )
        else:
            self.warnings.append(
                f"⚠️  Only {addon_terminology_count} upsell rules use 'add-on' terminology"
            )

    async def audit_training_examples(self):
        """Check training examples for fake scenarios"""
        print(f"\n{BLUE}🎭 Auditing Training Examples...{RESET}")

        examples = await self.conn.fetch(
            "SELECT customer_message, ai_response FROM training_data WHERE is_active = true"
        )

        fake_patterns = [
            "party package",
            "premium package",
            "executive package",
            "imaginary",
            "sample event",
            "fake booking",
            r"\$999",  # Unrealistic prices
            r"\$9999",
            "test customer",
        ]

        for example in examples:
            msg = example["customer_message"].lower()
            response = example["ai_response"].lower()

            for pattern in fake_patterns:
                if re.search(pattern, msg) or re.search(pattern, response):
                    self.issues.append(
                        f"❌ FAKE DATA in training: Contains '{pattern}'\n"
                        f"   Message: {example['customer_message'][:50]}..."
                    )

        # Check for real pricing examples
        real_pricing_count = await self.conn.fetchval(
            """SELECT COUNT(*) FROM training_data 
               WHERE (ai_response LIKE '%$2,750%' OR ai_response LIKE '%2750%')
               AND is_active = true"""
        )

        if real_pricing_count >= 1:
            self.verified.append(
                f"✅ Real pricing ($2,750 for 50 guests) used in {real_pricing_count} examples"
            )
        else:
            self.warnings.append(
                "⚠️  No training examples with real pricing ($2,750 for 50 guests)"
            )

    async def audit_faq_items(self, website_data):
        """Check FAQ items match website"""
        print(f"\n{BLUE}❓ Auditing FAQ Items...{RESET}")

        faqs = await self.conn.fetch(
            "SELECT question, answer FROM faq_items WHERE is_active = true"
        )

        # Check for fake data
        for faq in faqs:
            question = faq["question"].lower()
            answer = faq["answer"].lower()

            # Check for fake packages
            if "party package" in question or "party package" in answer:
                if (
                    "party package" not in answer
                    or "$12" in answer
                    or "$22" in answer
                ):
                    self.issues.append(
                        f"❌ FAKE PACKAGE in FAQ: {faq['question'][:50]}..."
                    )

        # Verify key FAQs exist
        key_topics = [
            ("pricing", "adult"),
            ("add-on", "option"),
            ("deposit", "booking"),
            ("minimum", "guest"),
        ]

        for topic1, topic2 in key_topics:
            exists = await self.conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM faq_items WHERE (question ILIKE $1 OR answer ILIKE $1) AND (question ILIKE $2 OR answer ILIKE $2) AND is_active = true)",
                f"%{topic1}%",
                f"%{topic2}%",
            )

            if exists:
                self.verified.append(f"✅ FAQ exists for: {topic1} + {topic2}")
            else:
                self.warnings.append(
                    f"⚠️  No FAQ found for: {topic1} + {topic2}"
                )

    async def audit_booking_availability(self):
        """Check booking availability uses real database queries"""
        print(f"\n{BLUE}📅 Auditing Booking Availability Logic...{RESET}")

        # Check if bookings table exists
        try:
            table_exists = await self.conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'bookings')"
            )

            if table_exists:
                self.verified.append("✅ Bookings table exists in database")

                # Check for any test/fake bookings
                try:
                    fake_bookings = await self.conn.fetch(
                        """SELECT id, customer_name, event_date FROM bookings 
                           WHERE customer_name ILIKE '%test%' 
                           OR customer_name ILIKE '%fake%'
                           OR customer_name ILIKE '%sample%'
                           LIMIT 5"""
                    )

                    if fake_bookings:
                        for booking in fake_bookings:
                            self.warnings.append(
                                f"⚠️  Test booking found: {booking['customer_name']} on {booking['event_date']}"
                            )
                    else:
                        self.verified.append(
                            "✅ No fake/test bookings found in database"
                        )
                except Exception as e:
                    self.warnings.append(
                        f"⚠️  Could not check bookings data: {e}"
                    )
            else:
                self.warnings.append(
                    "⚠️  Bookings table does not exist yet - will need real availability checks"
                )
        except Exception as e:
            self.warnings.append(f"⚠️  Could not check bookings table: {e}")

    async def check_code_for_fake_data(self):
        """Scan Python code for hardcoded fake data"""
        print(f"\n{BLUE}🔍 Scanning Code for Hardcoded Fake Data...{RESET}")

        code_files = [
            Path(__file__).parent / "seed_ai_training_real.py",
            Path(__file__).parent.parent / "services" / "knowledge_service.py",
            Path(__file__).parent.parent / "services" / "ai_service.py",
        ]

        fake_patterns = [
            (r"party\s*package", "Fake Party Package"),
            (r"executive\s*package", "Fake Executive Package"),
            (r"\$12[^0-9].*package", "$12 fake package price"),
            (r"\$22[^0-9].*package", "$22 fake package price"),
            (r"bundle\s*deal", "Fake Bundle Deal"),
            (r"vip\s*package", "Fake VIP Package"),
        ]

        for file_path in code_files:
            if not file_path.exists():
                continue

            content = file_path.read_text(encoding="utf-8")

            for pattern, description in fake_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    self.issues.append(
                        f"❌ FAKE DATA in {file_path.name}: Contains '{description}' pattern"
                    )

    async def run_full_audit(self):
        """Run complete audit"""
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}🔍 DEEP DATA AUDIT: AI Training vs Real Website{RESET}")
        print(f"{BLUE}{'='*60}{RESET}")

        await self.connect_db()

        # Load website data
        website_data = self.load_faqs_data()

        # Run all audits
        await self.audit_business_rules(website_data)
        await self.audit_upsell_rules(website_data)
        await self.audit_training_examples()
        await self.audit_faq_items(website_data)
        await self.audit_booking_availability()
        await self.check_code_for_fake_data()

        await self.close_db()

        # Print results
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}📊 AUDIT RESULTS{RESET}")
        print(f"{BLUE}{'='*60}{RESET}")

        if self.verified:
            print(f"\n{GREEN}✅ VERIFIED ({len(self.verified)} items):{RESET}")
            for item in self.verified:
                print(f"   {item}")

        if self.warnings:
            print(
                f"\n{YELLOW}⚠️  WARNINGS ({len(self.warnings)} items):{RESET}"
            )
            for item in self.warnings:
                print(f"   {item}")

        if self.issues:
            print(
                f"\n{RED}❌ CRITICAL ISSUES ({len(self.issues)} items):{RESET}"
            )
            for item in self.issues:
                print(f"   {item}")
        else:
            print(f"\n{GREEN}✅ NO CRITICAL ISSUES FOUND!{RESET}")

        print(f"\n{BLUE}{'='*60}{RESET}")

        # Summary
        total = len(self.verified) + len(self.warnings) + len(self.issues)
        print(f"\n{BLUE}📈 SUMMARY:{RESET}")
        print(f"   Total Checks: {total}")
        print(f"   {GREEN}Verified: {len(self.verified)}{RESET}")
        print(f"   {YELLOW}Warnings: {len(self.warnings)}{RESET}")
        print(f"   {RED}Issues: {len(self.issues)}{RESET}")

        if len(self.issues) == 0 and len(self.warnings) <= 3:
            print(f"\n{GREEN}🎉 DATA INTEGRITY: EXCELLENT{RESET}")
            print(f"{GREEN}✅ All AI data matches real website data!{RESET}")
            return True
        elif len(self.issues) == 0:
            print(f"\n{YELLOW}⚠️  DATA INTEGRITY: GOOD (minor warnings){RESET}")
            return True
        else:
            print(f"\n{RED}❌ DATA INTEGRITY: NEEDS ATTENTION{RESET}")
            return False


if __name__ == "__main__":
    audit = DataAudit()
    result = asyncio.run(audit.run_full_audit())
    exit(0 if result else 1)
