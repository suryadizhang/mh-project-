#!/usr/bin/env python3
"""
Automated Model Import Migration Script
========================================

Purpose: Migrate remaining ~95 OLD model imports to NEW db.models system

Strategy:
1. Find all files with old imports (from models import X)
2. Map old imports to new locations based on model type
3. Update imports with proper NEW system paths
4. Verify no syntax errors after migration
5. Generate migration report

Safety:
- Dry-run mode by default (use --apply to actually modify files)
- Creates backup before modification
- Validates Python syntax after changes
- Detailed logging of all changes

Usage:
    # Dry run (show what would change):
    python scripts/migrate_model_imports.py

    # Apply changes:
    python scripts/migrate_model_imports.py --apply

    # Target specific directory:
    python scripts/migrate_model_imports.py --directory services --apply
"""

import argparse
import ast
import logging
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import shutil
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# ============================================================================
# MODEL MAPPING: OLD imports → NEW locations
# ============================================================================

# Maps model classes to their NEW locations in db.models
MODEL_LOCATION_MAP: Dict[str, str] = {
    # Core business models (db.models.core)
    "Booking": "db.models.core",
    "BookingReminder": "db.models.core",
    "Payment": "db.models.core",
    "Customer": "db.models.core",
    "Chef": "db.models.core",
    "MessageThread": "db.models.core",
    "CoreMessage": "db.models.core",
    "PricingTier": "db.models.core",
    "SocialThread": "db.models.core",
    "Review": "db.models.core",
    "ReviewCoupon": "db.models.core",
    # Lead/CRM models (db.models.lead)
    "Lead": "db.models.lead",
    "LeadContact": "db.models.lead",
    "LeadContext": "db.models.lead",
    "LeadEvent": "db.models.lead",
    # Newsletter/Campaign models (db.models.newsletter)
    "Campaign": "db.models.newsletter",
    "CampaignEvent": "db.models.newsletter",
    "Subscriber": "db.models.newsletter",
    # Identity models (db.models.identity)
    "User": "db.models.identity",
    "Station": "db.models.identity",
    "GoogleOAuthAccount": "db.models.identity",
    # Event models (db.models.events)
    "DomainEvent": "db.models.events",
    "Inbox": "db.models.events",
    "Outbox": "db.models.events",
    # AI models (db.models.ai)
    "AITutorPair": "db.models.ai",
    "ConversationHistory": "db.models.ai",
    "IntentClassification": "db.models.ai",
    "ResponseFeedback": "db.models.ai",
    # CRM models (db.models.crm)
    "ReferralProgram": "db.models.crm",
    "ReferralLink": "db.models.crm",
    "ReferralConversion": "db.models.crm",
    # Operations models (db.models.ops)
    "CallRecording": "db.models.ops",
    "EmailMessage": "db.models.ops",
    "NotificationGroup": "db.models.ops",
}

# Maps enums to their NEW locations
ENUM_LOCATION_MAP: Dict[str, str] = {
    # Lead enums (db.models.lead)
    "ContactChannel": "db.models.lead",
    "LeadQuality": "db.models.lead",
    "LeadSource": "db.models.lead",
    "LeadStatus": "db.models.lead",
    "SocialPlatform": "db.models.lead",
    # Campaign enums (db.models.newsletter)
    "CampaignChannel": "db.models.newsletter",
    "CampaignStatus": "db.models.newsletter",
    "CampaignEventType": "db.models.newsletter",
    # Core enums (db.models.core)
    "BookingStatus": "db.models.core",
    "ReminderStatus": "db.models.core",
    "PaymentStatus": "db.models.core",
    "ReviewStatus": "db.models.core",
    "MessageKind": "db.models.core",
    "ThreadStatus": "db.models.core",
    # Operations enums (db.models.ops)
    "RecordingStatus": "db.models.ops",
    "EmailStatus": "db.models.ops",
}


# ============================================================================
# IMPORT PATTERNS TO DETECT
# ============================================================================

# Pattern: from models import X, Y, Z
OLD_IMPORT_PATTERN = re.compile(r"^from models import (.+)$", re.MULTILINE)

# Pattern: from models.X import Y
OLD_MODULE_IMPORT_PATTERN = re.compile(r"^from models\.(\w+) import (.+)$", re.MULTILINE)

# Pattern: from models.enums import X, Y, Z
OLD_ENUM_IMPORT_PATTERN = re.compile(r"^from models\.enums import (.+)$", re.MULTILINE)


# ============================================================================
# MIGRATION LOGIC
# ============================================================================


class ImportMigrator:
    """Handles migration of model imports from OLD to NEW system"""

    def __init__(self, dry_run: bool = True, backup: bool = True):
        self.dry_run = dry_run
        self.backup = backup
        self.files_modified: List[str] = []
        self.files_skipped: List[str] = []
        self.errors: List[Tuple[str, str]] = []

    def migrate_file(self, file_path: Path) -> bool:
        """
        Migrate imports in a single file

        Returns:
            True if file was modified, False otherwise
        """
        try:
            content = file_path.read_text(encoding="utf-8")
            original_content = content

            # Check if file has old imports
            if not self._has_old_imports(content):
                logger.debug(f"Skipping {file_path.relative_to(Path.cwd())} (no old imports)")
                self.files_skipped.append(str(file_path))
                return False

            # Migrate imports
            new_content = self._migrate_imports(content, file_path)

            if new_content == original_content:
                logger.debug(f"No changes needed for {file_path.relative_to(Path.cwd())}")
                self.files_skipped.append(str(file_path))
                return False

            # Validate syntax
            try:
                ast.parse(new_content)
            except SyntaxError as e:
                error_msg = f"Syntax error after migration: {e}"
                logger.error(f"❌ {file_path.relative_to(Path.cwd())}: {error_msg}")
                self.errors.append((str(file_path), error_msg))
                return False

            if self.dry_run:
                logger.info(f"🔍 Would migrate: {file_path.relative_to(Path.cwd())}")
                self._show_diff(original_content, new_content, file_path)
            else:
                # Backup original file
                if self.backup:
                    backup_path = file_path.with_suffix(
                        f'.py.bak.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
                    )
                    shutil.copy2(file_path, backup_path)
                    logger.debug(f"  Backed up to: {backup_path.name}")

                # Write new content
                file_path.write_text(new_content, encoding="utf-8")
                logger.info(f"✅ Migrated: {file_path.relative_to(Path.cwd())}")

            self.files_modified.append(str(file_path))
            return True

        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            logger.error(f"❌ {file_path.relative_to(Path.cwd())}: {error_msg}")
            self.errors.append((str(file_path), error_msg))
            return False

    def _has_old_imports(self, content: str) -> bool:
        """Check if file has old model imports"""
        return bool(
            OLD_IMPORT_PATTERN.search(content)
            or OLD_MODULE_IMPORT_PATTERN.search(content)
            or OLD_ENUM_IMPORT_PATTERN.search(content)
        )

    def _migrate_imports(self, content: str, file_path: Path) -> str:
        """Migrate all old imports to new system"""
        lines = content.split("\n")
        new_lines = []

        i = 0
        while i < len(lines):
            line = lines[i]

            # Pattern 1: from models import X, Y, Z
            match = OLD_IMPORT_PATTERN.match(line)
            if match:
                imports = match.group(1)
                new_lines.extend(self._convert_models_import(imports))
                i += 1
                continue

            # Pattern 2: from models.enums import X, Y, Z
            match = OLD_ENUM_IMPORT_PATTERN.match(line)
            if match:
                imports = match.group(1)
                new_lines.extend(self._convert_enum_import(imports))
                i += 1
                continue

            # Pattern 3: from models.X import Y
            match = OLD_MODULE_IMPORT_PATTERN.match(line)
            if match:
                module = match.group(1)
                imports = match.group(2)
                new_lines.extend(self._convert_module_import(module, imports))
                i += 1
                continue

            # No match - keep line as is
            new_lines.append(line)
            i += 1

        return "\n".join(new_lines)

    def _convert_models_import(self, imports_str: str) -> List[str]:
        """
        Convert: from models import X, Y, Z
        To: Multiple imports grouped by destination module
        """
        # Parse imported names (handle multiline imports)
        import_names = [name.strip() for name in imports_str.split(",")]

        # Group by destination module
        imports_by_module: Dict[str, List[str]] = {}
        unknown_imports: List[str] = []

        for name in import_names:
            # Clean up name (remove parentheses, newlines)
            name = name.strip("() \n")
            if not name:
                continue

            # Find destination module
            dest_module = MODEL_LOCATION_MAP.get(name) or ENUM_LOCATION_MAP.get(name)

            if dest_module:
                imports_by_module.setdefault(dest_module, []).append(name)
            else:
                unknown_imports.append(name)

        # Generate new import lines
        result = []
        result.append("# MIGRATED: Imports moved from OLD models to NEW db.models system")

        for module, names in sorted(imports_by_module.items()):
            result.append(f"from {module} import {', '.join(sorted(names))}")

        if unknown_imports:
            # Keep unknown imports as comment for manual review
            result.append(f"# TODO: Manual migration needed for: {', '.join(unknown_imports)}")
            result.append(f"# from models import {', '.join(unknown_imports)}")

        return result

    def _convert_enum_import(self, imports_str: str) -> List[str]:
        """
        Convert: from models.enums import X, Y, Z
        To: Imports from appropriate db.models modules
        """
        import_names = [name.strip() for name in imports_str.split(",")]

        imports_by_module: Dict[str, List[str]] = {}
        unknown_imports: List[str] = []

        for name in import_names:
            name = name.strip("() \n")
            if not name:
                continue

            dest_module = ENUM_LOCATION_MAP.get(name)

            if dest_module:
                imports_by_module.setdefault(dest_module, []).append(name)
            else:
                unknown_imports.append(name)

        result = []
        result.append("# MIGRATED: Enum imports moved from models.enums to NEW db.models system")

        for module, names in sorted(imports_by_module.items()):
            result.append(f"from {module} import {', '.join(sorted(names))}")

        if unknown_imports:
            result.append(
                f"# TODO: Manual migration needed for enums: {', '.join(unknown_imports)}"
            )
            result.append(f"# from models.enums import {', '.join(unknown_imports)}")

        return result

    def _convert_module_import(self, module: str, imports_str: str) -> List[str]:
        """
        Convert: from models.X import Y
        To: from db.models.X import Y (or appropriate NEW location)
        """
        # Map old module names to new ones
        module_map = {
            "booking": "db.models.core",
            "customer": "db.models.core",
            "lead": "db.models.lead",
            "newsletter": "db.models.newsletter",
            "campaign": "db.models.newsletter",
            "enums": "SPLIT",  # Enums are split across modules
        }

        new_module = module_map.get(module, f"db.models.{module}")

        if new_module == "SPLIT":
            # Need to split by enum type
            return self._convert_enum_import(imports_str)

        result = []
        result.append(f"# MIGRATED: from models.{module} → {new_module}")
        result.append(f"from {new_module} import {imports_str}")
        return result

    def _show_diff(self, old: str, new: str, file_path: Path):
        """Show diff preview for dry-run mode"""
        old_imports = [line for line in old.split("\n") if line.startswith("from models")]
        new_imports = [
            line
            for line in new.split("\n")
            if "MIGRATED" in line or line.startswith("from db.models")
        ]

        if old_imports or new_imports:
            logger.info(f"\n  === {file_path.name} ===")
            logger.info("  OLD:")
            for line in old_imports[:5]:  # Show first 5
                logger.info(f"    - {line}")
            logger.info("  NEW:")
            for line in new_imports[:5]:  # Show first 5
                logger.info(f"    + {line}")
            if len(new_imports) > 5:
                logger.info(f"    ... ({len(new_imports) - 5} more)")


# ============================================================================
# DIRECTORY SCANNER
# ============================================================================


def find_python_files(directory: Path, exclude_patterns: List[str] = None) -> List[Path]:
    """
    Find all Python files in directory (recursive)

    Args:
        directory: Root directory to search
        exclude_patterns: List of glob patterns to exclude

    Returns:
        List of Python file paths
    """
    if exclude_patterns is None:
        exclude_patterns = [
            "**/migrations/**",
            "**/alembic/**",
            "**/__pycache__/**",
            "**/venv/**",
            "**/env/**",
            "**/*.bak.*",
            "**/backups_*/**",
            "**/models/**",  # Don't modify OLD models directory
            "**/tests/test_*",  # Skip tests for now (manual review)
        ]

    python_files = []

    for py_file in directory.rglob("*.py"):
        # Check if file matches any exclude pattern
        if any(py_file.match(pattern) for pattern in exclude_patterns):
            continue

        python_files.append(py_file)

    return python_files


# ============================================================================
# MAIN SCRIPT
# ============================================================================


def main():
    """Main script entry point"""
    parser = argparse.ArgumentParser(
        description="Migrate model imports from OLD models.* to NEW db.models.*"
    )
    parser.add_argument("--apply", action="store_true", help="Apply changes (default: dry-run)")
    parser.add_argument(
        "--directory", type=str, default="src", help="Directory to process (default: src)"
    )
    parser.add_argument("--no-backup", action="store_true", help="Skip backup creation")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Determine mode
    dry_run = not args.apply
    mode = "DRY-RUN" if dry_run else "APPLY CHANGES"

    logger.info("=" * 80)
    logger.info(f"Model Import Migration Script - {mode}")
    logger.info("=" * 80)

    if dry_run:
        logger.info("ℹ️  Running in DRY-RUN mode (no files will be modified)")
        logger.info("ℹ️  Use --apply to actually modify files")
    else:
        logger.warning("⚠️  APPLY mode - files will be modified!")
        if not args.no_backup:
            logger.info("✅ Backups will be created (.bak files)")

    logger.info("")

    # Find Python files
    root_dir = Path(__file__).parent.parent / args.directory
    if not root_dir.exists():
        logger.error(f"❌ Directory not found: {root_dir}")
        sys.exit(1)

    logger.info(f"📂 Scanning directory: {root_dir.relative_to(Path.cwd())}")
    python_files = find_python_files(root_dir)
    logger.info(f"📄 Found {len(python_files)} Python files")
    logger.info("")

    # Migrate files
    migrator = ImportMigrator(dry_run=dry_run, backup=not args.no_backup)

    for file_path in python_files:
        migrator.migrate_file(file_path)

    # Summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("MIGRATION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"✅ Files modified: {len(migrator.files_modified)}")
    logger.info(f"⏭️  Files skipped: {len(migrator.files_skipped)}")
    logger.info(f"❌ Errors: {len(migrator.errors)}")

    if migrator.files_modified:
        logger.info("")
        logger.info("Modified files:")
        for file_path in migrator.files_modified[:10]:  # Show first 10
            logger.info(f"  - {Path(file_path).relative_to(Path.cwd())}")
        if len(migrator.files_modified) > 10:
            logger.info(f"  ... and {len(migrator.files_modified) - 10} more")

    if migrator.errors:
        logger.info("")
        logger.error("Errors encountered:")
        for file_path, error in migrator.errors:
            logger.error(f"  - {Path(file_path).relative_to(Path.cwd())}: {error}")

    if dry_run:
        logger.info("")
        logger.info("ℹ️  This was a DRY-RUN. Use --apply to make actual changes.")
    else:
        logger.info("")
        logger.info("✅ Migration complete!")
        if migrator.errors:
            logger.warning("⚠️  Some files had errors - please review manually")
            sys.exit(1)

    return 0 if not migrator.errors else 1


if __name__ == "__main__":
    sys.exit(main())
