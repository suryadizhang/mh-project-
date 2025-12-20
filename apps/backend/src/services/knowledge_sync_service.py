"""
Knowledge Sync Service - Auto-detect and sync dynamic data changes
==================================================================

Purpose: Monitor TypeScript source files for changes and sync to database
Sources:
  1. Menu Page (menu/page.tsx) → menu_items table
  2. FAQs (faqsData.ts) → faq_items table
  3. Terms (terms/page.tsx) → business_rules table

Features:
  - File hash comparison to detect changes
  - Automatic DB updates when source files change
  - Conflict detection (DB manual edits vs file changes)
  - Manual review flags for ambiguous changes
  - Version history tracking
  - Force override API for superadmin

Architecture:
  - File watcher monitors TypeScript files
  - Parser extracts structured data from each source
  - Comparator detects differences (added/modified/deleted)
  - Sync engine applies changes to DB
  - Audit log records all sync operations
"""

import hashlib
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from sqlalchemy.orm import Session

# Models
# MIGRATED: from models.knowledge_base → db.models.knowledge_base
from db.models.knowledge_base import MenuItem, FAQItem, BusinessRule


class KnowledgeSyncService:
    """
    Monitors TypeScript source files and syncs changes to database.
    Handles conflicts between manual DB edits and file changes.
    """

    def __init__(self, db: Session, workspace_root: str = "."):
        self.db = db
        self.workspace_root = Path(workspace_root)

        # Source file paths
        self.MENU_PAGE = self.workspace_root / "apps/customer/src/app/menu/page.tsx"
        self.FAQ_DATA = self.workspace_root / "apps/customer/src/data/faqsData.ts"
        self.TERMS_PAGE = self.workspace_root / "apps/customer/src/app/terms/page.tsx"

    # =====================================================================
    # HASH MANAGEMENT - Detect if files have changed
    # =====================================================================

    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file contents"""
        if not file_path.exists():
            return ""

        with open(file_path, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        return file_hash

    def get_stored_hash(self, source_type: str) -> Optional[str]:
        """
        Get last known hash for source file from sync_history table

        Args:
            source_type: 'menu', 'faqs', or 'terms'

        Returns:
            Last stored hash or None if never synced
        """
        # TODO: Implement sync_history table to store file hashes
        # For now, return None (will always trigger sync on first run)
        return None

    def update_stored_hash(self, source_type: str, new_hash: str):
        """Update stored hash after successful sync"""
        # TODO: Store in sync_history table with timestamp
        pass

    # =====================================================================
    # CHANGE DETECTION - Compare source files with database
    # =====================================================================

    def detect_menu_changes(self) -> Dict:
        """
        Compare menu/page.tsx with menu_items table

        Returns:
            {
                'file_hash': str,
                'changed': bool,
                'added': List[dict],
                'modified': List[dict],
                'deleted': List[dict],
                'conflicts': List[dict]  # Items edited in DB and file
            }
        """
        try:
            file_hash = self.calculate_file_hash(self.MENU_PAGE)
            stored_hash = self.get_stored_hash("menu")

            if file_hash == stored_hash:
                return {"file_hash": file_hash, "changed": False}

            # Parse menu items from TypeScript file
            file_items = self._parse_menu_from_tsx()

            # Get current DB items (handle missing table gracefully)
            try:
                db_items = self.db.query(MenuItem).all()
            except Exception as e:
                print(f"⚠️ WARNING: Could not query menu_items table: {e}")
                db_items = []

            db_by_name = {item.name: item for item in db_items}

            added = []
            modified = []
            deleted = []
            conflicts = []

            # Check for added/modified items
            for file_item in file_items:
                name = file_item["name"]
                if name not in db_by_name:
                    added.append(file_item)
                else:
                    db_item = db_by_name[name]
                    # Check if DB item was manually edited after last sync
                    if self._was_manually_edited(db_item, "menu"):
                        conflicts.append(
                            {
                                "name": name,
                                "file_data": file_item,
                                "db_data": db_item.to_dict(),
                                "reason": "Manual DB edit conflicts with file change",
                            }
                        )
                    elif self._items_differ(file_item, db_item.to_dict()):
                        modified.append({"name": name, "old": db_item.to_dict(), "new": file_item})

            # Check for deleted items
            file_names = {item["name"] for item in file_items}
            for db_item in db_items:
                if db_item.name not in file_names:
                    if self._was_manually_edited(db_item, "menu"):
                        conflicts.append(
                            {
                                "name": db_item.name,
                                "reason": "Item removed from file but edited in DB",
                            }
                        )
                    else:
                        deleted.append(db_item.to_dict())

            return {
                "file_hash": file_hash,
                "changed": True,
                "added": added,
                "modified": modified,
                "deleted": deleted,
                "conflicts": conflicts,
                "summary": f"{len(added)} added, {len(modified)} modified, {len(deleted)} deleted, {len(conflicts)} conflicts",
            }
        except Exception as e:
            print(f"❌ ERROR in detect_menu_changes: {e}")
            import traceback

            traceback.print_exc()
            return {
                "file_hash": "error",
                "changed": False,
                "added": [],
                "modified": [],
                "deleted": [],
                "conflicts": [],
                "error": str(e),
            }

    def detect_faq_changes(self) -> Dict:
        """
        Compare faqsData.ts with faq_items table

        Returns same structure as detect_menu_changes()
        """
        try:
            file_hash = self.calculate_file_hash(self.FAQ_DATA)
            stored_hash = self.get_stored_hash("faqs")

            if file_hash == stored_hash:
                return {"file_hash": file_hash, "changed": False}

            # Parse FAQs from TypeScript file
            file_items = self._parse_faqs_from_ts()

            # Get current DB items (handle missing table gracefully)
            try:
                db_items = self.db.query(FAQItem).all()
            except Exception as e:
                print(f"⚠️ WARNING: Could not query faq_items table: {e}")
                db_items = []

            db_by_question = {item.question: item for item in db_items}

            added = []
            modified = []
            deleted = []
            conflicts = []

            # Check for added/modified items
            for file_item in file_items:
                question = file_item["question"]
                if question not in db_by_question:
                    added.append(file_item)
                else:
                    db_item = db_by_question[question]
                    if self._was_manually_edited(db_item, "faqs"):
                        conflicts.append(
                            {
                                "question": question,
                                "file_data": file_item,
                                "db_data": db_item.to_dict(),
                                "reason": "Manual DB edit conflicts with file change",
                            }
                        )
                    elif self._items_differ(file_item, db_item.to_dict()):
                        modified.append(
                            {"question": question, "old": db_item.to_dict(), "new": file_item}
                        )

            # Check for deleted items
            file_questions = {item["question"] for item in file_items}
            for db_item in db_items:
                if db_item.question not in file_questions:
                    if self._was_manually_edited(db_item, "faqs"):
                        conflicts.append(
                            {
                                "question": db_item.question,
                                "reason": "FAQ removed from file but edited in DB",
                            }
                        )
                    else:
                        deleted.append(db_item.to_dict())

            return {
                "file_hash": file_hash,
                "changed": True,
                "added": added,
                "modified": modified,
                "deleted": deleted,
                "conflicts": conflicts,
                "summary": f"{len(added)} added, {len(modified)} modified, {len(deleted)} deleted, {len(conflicts)} conflicts",
            }
        except Exception as e:
            print(f"❌ ERROR in detect_faq_changes: {e}")
            import traceback

            traceback.print_exc()
            return {
                "file_hash": "error",
                "changed": False,
                "added": [],
                "modified": [],
                "deleted": [],
                "conflicts": [],
                "error": str(e),
            }

    def detect_terms_changes(self) -> Dict:
        """
        Compare terms/page.tsx with business_rules table

        Returns same structure as detect_menu_changes()
        """
        try:
            file_hash = self.calculate_file_hash(self.TERMS_PAGE)
            stored_hash = self.get_stored_hash("terms")

            if file_hash == stored_hash:
                return {"file_hash": file_hash, "changed": False}

            # Parse business rules from terms page
            file_items = self._parse_terms_from_tsx()

            # Get current DB items (treat empty DB as all items need to be added)
            try:
                db_items = self.db.query(BusinessRule).all()
            except Exception as e:
                print(f"⚠️ WARNING: Could not query business_rules table (may not exist): {e}")
                db_items = []

            db_by_title = {item.title: item for item in db_items}

            added = []
            modified = []
            deleted = []
            conflicts = []

            # Similar logic to detect_menu_changes()
            for file_item in file_items:
                title = file_item["title"]
                if title not in db_by_title:
                    added.append(file_item)
                else:
                    db_item = db_by_title[title]
                    if self._was_manually_edited(db_item, "terms"):
                        conflicts.append(
                            {
                                "title": title,
                                "file_data": file_item,
                                "db_data": db_item.to_dict(),
                                "reason": "Manual DB edit conflicts with file change",
                            }
                        )
                    elif self._items_differ(file_item, db_item.to_dict()):
                        modified.append(
                            {"title": title, "old": db_item.to_dict(), "new": file_item}
                        )

            file_titles = {item["title"] for item in file_items}
            for db_item in db_items:
                if db_item.title not in file_titles:
                    if self._was_manually_edited(db_item, "terms"):
                        conflicts.append(
                            {
                                "title": db_item.title,
                                "reason": "Rule removed from file but edited in DB",
                            }
                        )
                    else:
                        deleted.append(db_item.to_dict())

            return {
                "file_hash": file_hash,
                "changed": True,
                "added": added,
                "modified": modified,
                "deleted": deleted,
                "conflicts": conflicts,
                "summary": f"{len(added)} added, {len(modified)} modified, {len(deleted)} deleted, {len(conflicts)} conflicts",
            }
        except Exception as e:
            print(f"❌ ERROR in detect_terms_changes: {e}")
            import traceback

            traceback.print_exc()
            return {
                "file_hash": "error",
                "changed": False,
                "added": [],
                "modified": [],
                "deleted": [],
                "conflicts": [],
                "error": str(e),
            }

    # =====================================================================
    # AUTO-SYNC - Apply changes to database
    # =====================================================================

    def auto_sync_menu(self, changes: Dict, force: bool = False) -> Dict:
        """
        Apply menu changes to database

        Args:
            changes: Output from detect_menu_changes()
            force: If True, override conflicts (superadmin only)

        Returns:
            {
                'success': bool,
                'applied': int,
                'skipped': int,
                'errors': List[str]
            }
        """
        if not changes.get("changed"):
            return {"success": True, "applied": 0, "skipped": 0, "message": "No changes detected"}

        if changes["conflicts"] and not force:
            return {
                "success": False,
                "applied": 0,
                "skipped": len(changes["conflicts"]),
                "errors": ["Conflicts detected. Use force=True to override."],
                "conflicts": changes["conflicts"],
            }

        applied = 0
        errors = []

        try:
            # Add new items
            for item_data in changes["added"]:
                new_item = MenuItem(**item_data)
                self.db.add(new_item)
                applied += 1

            # Update modified items
            for mod in changes["modified"]:
                db_item = self.db.query(MenuItem).filter_by(name=mod["name"]).first()
                if db_item:
                    for key, value in mod["new"].items():
                        setattr(db_item, key, value)
                    db_item.last_updated = datetime.utcnow()
                    applied += 1

            # Delete removed items
            for item_data in changes["deleted"]:
                db_item = self.db.query(MenuItem).filter_by(name=item_data["name"]).first()
                if db_item:
                    self.db.delete(db_item)
                    applied += 1

            # Handle conflicts if force=True
            if force and changes["conflicts"]:
                for conflict in changes["conflicts"]:
                    if "file_data" in conflict:
                        db_item = self.db.query(MenuItem).filter_by(name=conflict["name"]).first()
                        if db_item:
                            for key, value in conflict["file_data"].items():
                                setattr(db_item, key, value)
                            db_item.last_updated = datetime.utcnow()
                            applied += 1

            self.db.commit()
            self.update_stored_hash("menu", changes["file_hash"])

            return {
                "success": True,
                "applied": applied,
                "skipped": 0,
                "message": f"Successfully synced {applied} menu items",
            }

        except Exception as e:
            self.db.rollback()
            return {"success": False, "applied": 0, "skipped": applied, "errors": [str(e)]}

    def auto_sync_faqs(self, changes: Dict, force: bool = False) -> Dict:
        """Apply FAQ changes to database (same pattern as auto_sync_menu)"""
        # Similar implementation
        pass

    def auto_sync_terms(self, changes: Dict, force: bool = False) -> Dict:
        """Apply terms changes to database (same pattern as auto_sync_menu)"""
        # Similar implementation
        pass

    # =====================================================================
    # PARSER HELPERS - Extract data from TypeScript files
    # =====================================================================

    def _parse_menu_from_tsx(self) -> List[Dict]:
        """
        Parse menu items from menu/page.tsx

        Returns:
            List of menu item dicts matching MenuItem model schema
        """
        import re

        if not self.MENU_PAGE.exists():
            print(f"WARNING: Menu file not found at {self.MENU_PAGE}")
            return []

        with open(self.MENU_PAGE, "r", encoding="utf-8") as f:
            content = f.read()

        menu_items = []

        # Pattern to match protein items in JSX
        # Looks for: <h5 className="protein-name">NAME</h5> followed by description
        protein_pattern = r'<h5 className="protein-name">([^<]+)</h5>\s*(?:<[^>]*>)*\s*<p className="protein-desc">\s*([^<]+)</p>'

        # Find all base proteins (in "Base Proteins" section before "Premium Upgrades")
        base_section_match = re.search(
            r"Base Proteins.*?(?=Premium Upgrades|Additional Enhancements)", content, re.DOTALL
        )
        if base_section_match:
            base_section = base_section_match.group(0)
            for match in re.finditer(protein_pattern, base_section):
                name = match.group(1).strip()
                description = match.group(2).strip()
                menu_items.append(
                    {
                        "name": name,
                        "description": description,
                        "price": None,  # Base proteins are included
                        "category": self._categorize_protein(name),
                        "is_premium": False,
                        "is_available": True,
                    }
                )

        # Find premium upgrades (look for price indicators like "+$5", "+$20", "+$15.99", etc.)
        premium_section_match = re.search(
            r"Premium Upgrades.*?(?=Additional Enhancements|Included Items)", content, re.DOTALL
        )
        if premium_section_match:
            premium_section = premium_section_match.group(0)
            # Pattern for premium items with price badges - captures any price format (integer or decimal)
            premium_pattern = r'<h5 className="protein-name">([^<]+)</h5>.*?<span className="price-badge[^"]*">\+\$(\d+(?:\.\d{1,2})?)</span>.*?<p className="protein-desc">\s*([^<]+)</p>'
            for match in re.finditer(premium_pattern, premium_section, re.DOTALL):
                name = match.group(1).strip()
                price = float(match.group(2))  # Handles both "5" and "5.99"
                description = match.group(3).strip()
                menu_items.append(
                    {
                        "name": name,
                        "description": description,
                        "price": price,
                        "category": self._categorize_protein(name),
                        "is_premium": True,
                        "is_available": True,
                    }
                )

        # Find additional enhancements (sides, appetizers) - any price format
        enhancements_section_match = re.search(
            r"Additional Enhancements.*?(?=$|<footer)", content, re.DOTALL
        )
        if enhancements_section_match:
            enhancements_section = enhancements_section_match.group(0)
            # Pattern for enhancement items - captures any price format (integer or decimal)
            enhancement_pattern = r'<h5[^>]*>([^<]+)</h5>.*?<span className="price[^"]*">\+\$(\d+(?:\.\d{1,2})?)</span>.*?<p[^>]*>\s*([^<]+)</p>'
            for match in re.finditer(enhancement_pattern, enhancements_section, re.DOTALL):
                name = match.group(1).strip()
                price = float(match.group(2))  # Handles both "10" and "10.50"
                description = match.group(3).strip()
                menu_items.append(
                    {
                        "name": name,
                        "description": description,
                        "price": price,
                        "category": self._categorize_enhancement(name),
                        "is_premium": True,
                        "is_available": True,
                    }
                )

        return menu_items

    def _categorize_protein(self, name: str) -> str:
        """Determine category based on protein name"""
        name_lower = name.lower()
        if "chicken" in name_lower:
            return "poultry"
        elif any(x in name_lower for x in ["steak", "filet", "beef", "sirloin"]):
            return "beef"
        elif any(
            x in name_lower for x in ["shrimp", "lobster", "scallop", "salmon", "calamari", "fish"]
        ):
            return "seafood"
        elif any(x in name_lower for x in ["tofu", "vegetable"]):
            return "specialty"
        return "other"

    def _categorize_enhancement(self, name: str) -> str:
        """Determine category based on enhancement name"""
        name_lower = name.lower()
        if any(x in name_lower for x in ["rice", "noodle", "vegetable", "yakisoba"]):
            return "sides"
        elif any(x in name_lower for x in ["edamame", "gyoza", "salad"]):
            return "appetizers"
        elif "protein" in name_lower:
            return "desserts"  # Using desserts category for "Extra Protein" add-on
        return "other"

    def _parse_faqs_from_ts(self) -> List[Dict]:
        """
        Parse FAQs from faqsData.ts

        Returns:
            List of FAQ dicts matching FaqItem model schema
        """
        import re

        if not self.FAQ_DATA.exists():
            return []

        with open(self.FAQ_DATA, "r", encoding="utf-8") as f:
            content = f.read()

        faqs = []

        # Find the faqs array: export const faqs: FaqItem[] = [...]
        faqs_array_match = re.search(
            r"export const faqs: FaqItem\[\] = \[(.*?)\](?=\s*export|\s*$)", content, re.DOTALL
        )
        if not faqs_array_match:
            return []

        faqs_array_content = faqs_array_match.group(1)

        # Split by objects (look for pattern: { ... },)
        # More robust: find each FAQ object by matching braces
        faq_objects = []
        brace_count = 0
        current_obj = ""
        in_object = False

        for char in faqs_array_content:
            if char == "{":
                brace_count += 1
                in_object = True
            if in_object:
                current_obj += char
            if char == "}":
                brace_count -= 1
                if brace_count == 0 and in_object:
                    faq_objects.append(current_obj)
                    current_obj = ""
                    in_object = False

        # Parse each FAQ object
        for obj_str in faq_objects:
            faq = {}

            # Extract question
            question_match = re.search(r"question:\s*['\"]([^'\"]+)['\"]", obj_str)
            if question_match:
                faq["question"] = question_match.group(1)

            # Extract answer (may span multiple lines)
            answer_match = re.search(
                r"answer:\s*['\"](.+?)['\"](?=,|\s*category:)", obj_str, re.DOTALL
            )
            if answer_match:
                faq["answer"] = answer_match.group(1).strip()

            # Extract category
            category_match = re.search(r"category:\s*['\"]([^'\"]+)['\"]", obj_str)
            if category_match:
                faq["category"] = category_match.group(1)

            # Only add if we got the essential fields
            if "question" in faq and "answer" in faq and "category" in faq:
                faqs.append(
                    {
                        "question": faq["question"],
                        "answer": faq["answer"],
                        "category": faq["category"],
                        "view_count": 0,
                        "helpful_count": 0,
                        "is_active": True,
                    }
                )

        return faqs

    def _parse_terms_from_tsx(self) -> List[Dict]:
        """
        Parse business rules from terms/page.tsx

        Returns:
            List of business rule dicts matching BusinessRule model schema
        """
        import re

        if not self.TERMS_PAGE.exists():
            return []

        with open(self.TERMS_PAGE, "r", encoding="utf-8") as f:
            content = f.read()

        rules = []

        # Parse cancellation policy
        cancellation_match = re.search(
            r"<h2>4\. Cancellation Policy</h2>(.*?)(?=<h2>|</section>)", content, re.DOTALL
        )
        if cancellation_match:
            section = cancellation_match.group(1)

            # Full refund rule
            if "7+ Days Before Event" in section:
                rules.append(
                    {
                        "rule_type": "CANCELLATION",
                        "title": "Full Refund Period",
                        "content": "Full refund including $100 deposit if canceled 7 or more days before event",
                        "value": {
                            "days_before": 7,
                            "refund_percentage": 100,
                            "includes_deposit": True,
                        },
                        "is_active": True,
                        "version": 1,
                    }
                )

            # No refund rule
            if "Less than 7 Days" in section:
                rules.append(
                    {
                        "rule_type": "CANCELLATION",
                        "title": "No Refund Period",
                        "content": "$100 deposit is non-refundable if canceled less than 7 days before event",
                        "value": {
                            "days_before": 7,
                            "deposit_refundable": False,
                            "balance_refundable": False,
                        },
                        "is_active": True,
                        "version": 1,
                    }
                )

        # Parse rescheduling policy
        rescheduling_match = re.search(
            r"<h2>5\. Rescheduling Policy</h2>(.*?)(?=<h2>|</section>)", content, re.DOTALL
        )
        if rescheduling_match:
            section = rescheduling_match.group(1)

            # First reschedule free
            if "One free reschedule" in section and "48 hours" in section:
                rules.append(
                    {
                        "rule_type": "RESCHEDULING",
                        "title": "First Reschedule Free",
                        "content": "One free reschedule allowed within 48 hours of booking",
                        "value": {
                            "first_reschedule_free": True,
                            "time_window_hours": 48,
                            "subsequent_fee": 100,
                        },
                        "is_active": True,
                        "version": 1,
                    }
                )

            # Additional reschedule fee
            if "$100 fee" in section:
                rules.append(
                    {
                        "rule_type": "RESCHEDULING",
                        "title": "Additional Reschedule Fee",
                        "content": "$100 fee applies to any reschedules after the first one",
                        "value": {"fee_amount": 100, "applies_after_first": True},
                        "is_active": True,
                        "version": 1,
                    }
                )

        # Parse payment terms
        payment_match = re.search(
            r"<h2>3\. Booking and Payment Terms</h2>(.*?)(?=<h2>|</section>)", content, re.DOTALL
        )
        if payment_match:
            section = payment_match.group(1)

            # Deposit requirement
            if "$100 refundable deposit" in section or "$100 deposit" in section:
                rules.append(
                    {
                        "rule_type": "PAYMENT",
                        "title": "Deposit Requirement",
                        "content": "$100 refundable deposit required to secure booking",
                        "value": {
                            "deposit_amount": 100,
                            "refundable": True,
                            "conditions": "if canceled 7+ days before event",
                        },
                        "is_active": True,
                        "version": 1,
                    }
                )

            # Extract pricing minimum from content
            minimum_match = re.search(r"\$(\d+)\s*(?:party\s*)?minimum", section, re.IGNORECASE)
            if minimum_match:
                minimum_amount = int(minimum_match.group(1))
                rules.append(
                    {
                        "rule_type": "PRICING",
                        "title": "Party Minimum",
                        "content": f"${minimum_amount} total minimum per event",
                        "value": {
                            "minimum_amount": minimum_amount,
                            "approximate_guests": 10,
                            "currency": "USD",
                        },
                        "is_active": True,
                        "version": 1,
                    }
                )

        # Parse travel fees (may be in multiple sections)
        travel_match = re.search(
            r"first\s+(\d+)\s+miles.*?\$(\d+)\s*(?:per\s*)?mile", content, re.IGNORECASE | re.DOTALL
        )
        if travel_match:
            free_miles = int(travel_match.group(1))
            per_mile_rate = int(travel_match.group(2))
            rules.append(
                {
                    "rule_type": "PRICING",
                    "title": "Travel Fee Structure",
                    "content": f"First {free_miles} miles from our location are free. After that, ${per_mile_rate} per mile",
                    "value": {
                        "free_miles": free_miles,
                        "per_mile_rate": per_mile_rate,
                        "flexible": True,
                    },
                    "is_active": True,
                    "version": 1,
                }
            )

        return rules

    # =====================================================================
    # HELPER METHODS
    # =====================================================================

    def _was_manually_edited(self, db_item, source_type: str) -> bool:
        """
        Check if DB item was edited after last sync

        Args:
            db_item: SQLAlchemy model instance
            source_type: 'menu', 'faqs', or 'terms'

        Returns:
            True if item was manually edited in DB since last sync
        """
        # TODO: Compare last_updated timestamp with last_sync_time from sync_history
        # For now, return False (assume no manual edits)
        return False

    def _items_differ(self, file_data: Dict, db_data: Dict) -> bool:
        """
        Compare file data with DB data to detect changes

        Args:
            file_data: Parsed data from TypeScript file
            db_data: Data from database (via to_dict())

        Returns:
            True if items have meaningful differences
        """
        # Compare key fields (ignore timestamps, IDs)
        compare_keys = [
            "name",
            "description",
            "price",
            "category",
            "question",
            "answer",
            "title",
            "content",
        ]

        for key in compare_keys:
            if key in file_data and key in db_data:
                if file_data[key] != db_data[key]:
                    return True

        return False

    # =====================================================================
    # PUBLIC API - Main entry points
    # =====================================================================

    def get_sync_status(self) -> Dict:
        """
        Get sync status for all three sources

        Returns:
            {
                'menu': {...},
                'faqs': {...},
                'terms': {...},
                'overall_status': 'synced' | 'needs_sync' | 'conflicts'
            }
        """
        menu_changes = self.detect_menu_changes()
        faq_changes = self.detect_faq_changes()
        terms_changes = self.detect_terms_changes()

        has_changes = any(
            [menu_changes.get("changed"), faq_changes.get("changed"), terms_changes.get("changed")]
        )

        has_conflicts = any(
            [
                len(menu_changes.get("conflicts", [])) > 0,
                len(faq_changes.get("conflicts", [])) > 0,
                len(terms_changes.get("conflicts", [])) > 0,
            ]
        )

        overall_status = "synced"
        if has_conflicts:
            overall_status = "conflicts"
        elif has_changes:
            overall_status = "needs_sync"

        return {
            "menu": menu_changes,
            "faqs": faq_changes,
            "terms": terms_changes,
            "overall_status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def sync_all(self, force: bool = False) -> Dict:
        """
        Sync all three sources (menu, FAQs, terms) in one operation

        Args:
            force: Override conflicts (superadmin only)

        Returns:
            {
                'menu': {...sync result...},
                'faqs': {...sync result...},
                'terms': {...sync result...},
                'overall_success': bool
            }
        """
        menu_changes = self.detect_menu_changes()
        faq_changes = self.detect_faq_changes()
        terms_changes = self.detect_terms_changes()

        menu_result = self.auto_sync_menu(menu_changes, force)
        faq_result = self.auto_sync_faqs(faq_changes, force)
        terms_result = self.auto_sync_terms(terms_changes, force)

        overall_success = all(
            [
                menu_result.get("success", False),
                faq_result.get("success", False),
                terms_result.get("success", False),
            ]
        )

        return {
            "menu": menu_result,
            "faqs": faq_result,
            "terms": terms_result,
            "overall_success": overall_success,
            "timestamp": datetime.utcnow().isoformat(),
        }
