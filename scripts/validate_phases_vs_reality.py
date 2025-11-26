#!/usr/bin/env python3
"""
Phase Documentation vs Reality Validator

Compares actual codebase state against phase documentation to identify:
- Completed work that should be documented as done
- Documentation claiming work is done but code doesn't exist
- Mismatches in file paths, function names, class names
- Missing prerequisites for upcoming phases
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import re
import sys

# Add backend src to path
sys.path.insert(
    0, str(Path(__file__).parent.parent / "apps" / "backend" / "src")
)


class ValidationStatus(Enum):
    MATCH = "✅ MATCH"
    MISMATCH = "❌ MISMATCH"
    MISSING = "⚠️ MISSING"
    EXTRA = "ℹ️ EXTRA"


@dataclass
class ValidationResult:
    phase: str
    category: str
    item: str
    status: ValidationStatus
    expected: str
    actual: str
    details: str


class PhaseValidator:
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.backend_src = workspace_root / "apps" / "backend" / "src"
        # Fix: alembic is in src/db/migrations/alembic, not apps/backend/alembic
        self.alembic_versions = (
            self.backend_src / "db" / "migrations" / "alembic" / "versions"
        )
        self.results: list[ValidationResult] = []

    def validate_all_phases(self) -> dict[str, list[ValidationResult]]:
        """Run all phase validations"""
        print("🔍 Starting Phase Validation...")
        print("=" * 80)

        self.validate_phase_0()
        self.validate_phase_1a()
        self.validate_phase_1b()
        self.validate_phase_2()
        self.validate_customer_encryption()

        return self.group_results_by_phase()

    def validate_phase_0(self):
        """Phase 0: Database & Alembic Cleanup"""

        # Check migration file count
        if self.alembic_versions.exists():
            migration_files = list(self.alembic_versions.glob("*.py"))
            migration_count = len(migration_files)

            self.results.append(
                ValidationResult(
                    phase="Phase 0",
                    category="Alembic Migrations",
                    item="Migration files exist",
                    status=ValidationStatus.MATCH,
                    expected="50+ migration files",
                    actual=f"{migration_count} migration files",
                    details=f"Found {migration_count} migrations in {self.alembic_versions}",
                )
            )

            # Check for merge migration (phase_0_merge)
            merge_migrations = [
                f
                for f in migration_files
                if "phase_0_merge" in f.stem.lower()
                or "merge" in f.stem.lower()
            ]
            if merge_migrations:
                self.results.append(
                    ValidationResult(
                        phase="Phase 0",
                        category="Alembic Migrations",
                        item="Merge migration exists",
                        status=ValidationStatus.MATCH,
                        expected="At least 1 merge migration",
                        actual=f"{len(merge_migrations)} merge migration(s)",
                        details=f"Merge migrations: {[m.name for m in merge_migrations]}",
                    )
                )
            else:
                self.results.append(
                    ValidationResult(
                        phase="Phase 0",
                        category="Alembic Migrations",
                        item="Merge migration exists",
                        status=ValidationStatus.MISSING,
                        expected="At least 1 merge migration",
                        actual="No merge migrations found",
                        details="Phase 0 docs mention merge migration should exist",
                    )
                )
        else:
            self.results.append(
                ValidationResult(
                    phase="Phase 0",
                    category="Alembic Migrations",
                    item="Alembic versions directory",
                    status=ValidationStatus.MISSING,
                    expected="Alembic versions directory exists",
                    actual="Directory not found",
                    details=f"Expected at {self.alembic_versions}",
                )
            )

    def validate_phase_1a(self):
        """Validate Phase 1A: Production Critical Fixes"""
        print("\n🔥 Phase 1A: Production Critical Fixes")

        # Check for Bug #13 fix in booking service
        booking_service = self.backend_src / "services" / "booking_service.py"
        if booking_service.exists():
            content = booking_service.read_text(encoding="utf-8")

            # Check for SELECT FOR UPDATE
            if "SELECT FOR UPDATE" in content or "for_update()" in content:
                self.results.append(
                    ValidationResult(
                        phase="Phase 1A",
                        category="Bug #13 Fix",
                        item="SELECT FOR UPDATE in booking",
                        status=ValidationStatus.MATCH,
                        expected="for_update() or SELECT FOR UPDATE",
                        actual="Found in booking_service.py",
                        details="Pessimistic locking implemented",
                    )
                )
            else:
                self.results.append(
                    ValidationResult(
                        phase="Phase 1A",
                        category="Bug #13 Fix",
                        item="SELECT FOR UPDATE in booking",
                        status=ValidationStatus.MISSING,
                        expected="for_update() or SELECT FOR UPDATE",
                        actual="Not found in booking_service.py",
                        details="Phase 1A requires pessimistic locking",
                    )
                )

        # Check for timezone fixes
        self.check_timezone_usage()

        # Check for GSM integration
        self.check_gsm_integration()

    def validate_phase_1b(self):
        """Validate Phase 1B: Multi-Schema Foundation"""
        print("\n🏗️ Phase 1B: Multi-Schema Foundation")

        # Check for multi-schema models
        db_models_dir = self.backend_src / "db" / "models"
        if db_models_dir.exists():
            schema_files = {
                "core.py": "Core business models",
                "ai.py": "AI domain models",
                "identity.py": "Identity/auth models",
                "crm.py": "CRM models",
                "ops.py": "Operations models",
            }

            for filename, description in schema_files.items():
                filepath = db_models_dir / filename
                if filepath.exists():
                    content = filepath.read_text(encoding="utf-8")
                    # Check for schema declaration
                    if "__table_args__" in content and "schema" in content:
                        self.results.append(
                            ValidationResult(
                                phase="Phase 1B",
                                category="Multi-Schema Models",
                                item=f"{filename} schema",
                                status=ValidationStatus.MATCH,
                                expected=f"{description} with schema declaration",
                                actual="Found with __table_args__ schema",
                                details=f"File exists at {filepath}",
                            )
                        )
                    else:
                        self.results.append(
                            ValidationResult(
                                phase="Phase 1B",
                                category="Multi-Schema Models",
                                item=f"{filename} schema",
                                status=ValidationStatus.MISMATCH,
                                expected=f"{description} with schema declaration",
                                actual="File exists but no schema found",
                                details="Missing __table_args__ with schema",
                            )
                        )
                else:
                    self.results.append(
                        ValidationResult(
                            phase="Phase 1B",
                            category="Multi-Schema Models",
                            item=f"{filename}",
                            status=ValidationStatus.MISSING,
                            expected=f"{description}",
                            actual="File not found",
                            details=f"Expected at {filepath}",
                        )
                    )

    def validate_phase_2(self):
        """Validate Phase 2: AI Agents"""
        print("\n🤖 Phase 2: AI Multi-Agent System")

        # Check for AI agent implementations
        ai_agents_dir = self.backend_src / "api" / "ai" / "agents"
        if ai_agents_dir.exists():
            expected_agents = {
                "distance_agent.py": "Distance & Travel Fee Agent",
                "menu_agent.py": "Menu Advisor Agent",
                "pricing_agent.py": "Pricing Calculator Agent",
                "booking_agent.py": "Booking Coordinator Agent",
                "availability_agent.py": "Availability Checker Agent",
            }

            for filename, description in expected_agents.items():
                filepath = ai_agents_dir / filename
                if filepath.exists():
                    self.results.append(
                        ValidationResult(
                            phase="Phase 2",
                            category="AI Agents",
                            item=description,
                            status=ValidationStatus.MATCH,
                            expected=filename,
                            actual="File exists",
                            details=f"Found at {filepath}",
                        )
                    )
                else:
                    self.results.append(
                        ValidationResult(
                            phase="Phase 2",
                            category="AI Agents",
                            item=description,
                            status=ValidationStatus.MISSING,
                            expected=filename,
                            actual="File not found",
                            details=f"Expected at {filepath}",
                        )
                    )

        # Check for PricingService dynamic configuration
        pricing_service = (
            self.backend_src
            / "api"
            / "ai"
            / "endpoints"
            / "services"
            / "pricing_service.py"
        )
        if pricing_service.exists():
            content = pricing_service.read_text(encoding="utf-8")

            # Check for hardcoded values (FORBIDDEN)
            hardcoded_patterns = [
                (r"=\s*50\b", "Hardcoded $50"),
                (r"=\s*55\b", "Hardcoded $55"),
                (r"=\s*30\b", "Hardcoded 30 miles"),
                (r"=\s*2\.00\b", "Hardcoded $2.00"),
            ]

            for pattern, desc in hardcoded_patterns:
                if re.search(pattern, content):
                    self.results.append(
                        ValidationResult(
                            phase="Phase 2",
                            category="Dynamic Configuration",
                            item=f"No hardcoded values: {desc}",
                            status=ValidationStatus.MISMATCH,
                            expected="Dynamic configuration from database",
                            actual=f"Found {desc} in pricing_service.py",
                            details="Phase 2 requires all values be dynamic",
                        )
                    )

    def validate_customer_encryption(self):
        """Validate Customer Encryption Integration (Recent Work)"""
        print("\n🔐 Customer Encryption Integration")

        # Check Customer model
        core_models = self.backend_src / "db" / "models" / "core.py"
        if core_models.exists():
            content = core_models.read_text(encoding="utf-8")

            # Check for encryption fields
            if "email_encrypted" in content and "phone_encrypted" in content:
                self.results.append(
                    ValidationResult(
                        phase="Recent Work",
                        category="Customer Encryption",
                        item="Encrypted fields in Customer model",
                        status=ValidationStatus.MATCH,
                        expected="email_encrypted, phone_encrypted",
                        actual="Found both fields",
                        details="Customer model has encrypted PII fields",
                    )
                )
            else:
                self.results.append(
                    ValidationResult(
                        phase="Recent Work",
                        category="Customer Encryption",
                        item="Encrypted fields in Customer model",
                        status=ValidationStatus.MISSING,
                        expected="email_encrypted, phone_encrypted",
                        actual="Fields not found",
                        details="Missing encrypted fields in Customer model",
                    )
                )

            # Check for @property decorators
            if "@property" in content and "def email(self)" in content:
                self.results.append(
                    ValidationResult(
                        phase="Recent Work",
                        category="Customer Encryption",
                        item="@property decorators for encryption",
                        status=ValidationStatus.MATCH,
                        expected="@property email/phone getters/setters",
                        actual="Found @property decorators",
                        details="Customer model has property decorators",
                    )
                )
            else:
                self.results.append(
                    ValidationResult(
                        phase="Recent Work",
                        category="Customer Encryption",
                        item="@property decorators for encryption",
                        status=ValidationStatus.MISSING,
                        expected="@property email/phone getters/setters",
                        actual="Property decorators not found",
                        details="Missing backward compatibility properties",
                    )
                )

        # Check encryption module
        encryption_module = self.backend_src / "core" / "encryption.py"
        if encryption_module.exists():
            content = encryption_module.read_text(encoding="utf-8")

            required_functions = [
                "encrypt_email",
                "decrypt_email",
                "encrypt_phone",
                "decrypt_phone",
            ]

            missing_funcs = []
            for func in required_functions:
                if f"def {func}" not in content:
                    missing_funcs.append(func)

            if not missing_funcs:
                self.results.append(
                    ValidationResult(
                        phase="Recent Work",
                        category="Customer Encryption",
                        item="Encryption module functions",
                        status=ValidationStatus.MATCH,
                        expected=", ".join(required_functions),
                        actual="All functions found",
                        details="core/encryption.py has all required functions",
                    )
                )
            else:
                self.results.append(
                    ValidationResult(
                        phase="Recent Work",
                        category="Customer Encryption",
                        item="Encryption module functions",
                        status=ValidationStatus.MISSING,
                        expected=", ".join(required_functions),
                        actual=f"Missing: {', '.join(missing_funcs)}",
                        details="Some encryption functions not implemented",
                    )
                )
        else:
            self.results.append(
                ValidationResult(
                    phase="Recent Work",
                    category="Customer Encryption",
                    item="Encryption module exists",
                    status=ValidationStatus.MISSING,
                    expected="core/encryption.py",
                    actual="File not found",
                    details="Encryption module not implemented",
                )
            )

    def check_timezone_usage(self):
        """Check for timezone-naive datetime usage"""
        problematic_files = []

        # Search for datetime.now() without timezone
        for py_file in self.backend_src.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                # Check for datetime.now() without timezone.utc
                if re.search(r"datetime\.now\(\)(?!\s*\.replace)", content):
                    problematic_files.append(
                        py_file.relative_to(self.workspace_root)
                    )
            except:
                pass

        if problematic_files:
            self.results.append(
                ValidationResult(
                    phase="Phase 1A",
                    category="Timezone Fixes",
                    item="timezone-naive datetime.now()",
                    status=ValidationStatus.MISMATCH,
                    expected="datetime.now(timezone.utc)",
                    actual=f"{len(problematic_files)} files with datetime.now()",
                    details=f"Files: {[str(f) for f in problematic_files[:5]]}",
                )
            )
        else:
            self.results.append(
                ValidationResult(
                    phase="Phase 1A",
                    category="Timezone Fixes",
                    item="timezone-naive datetime.now()",
                    status=ValidationStatus.MATCH,
                    expected="datetime.now(timezone.utc)",
                    actual="No timezone-naive usage found",
                    details="All datetime.now() calls use timezone",
                )
            )

    def check_gsm_integration(self):
        """Check for Google Secrets Manager integration"""
        config_file = self.backend_src / "core" / "config.py"
        if config_file.exists():
            content = config_file.read_text(encoding="utf-8")

            if "google" in content.lower() and "secret" in content.lower():
                self.results.append(
                    ValidationResult(
                        phase="Phase 1A",
                        category="GSM Integration",
                        item="Google Secrets Manager",
                        status=ValidationStatus.MATCH,
                        expected="GSM integration in config",
                        actual="Found GSM references",
                        details="core/config.py has GSM integration",
                    )
                )
            else:
                self.results.append(
                    ValidationResult(
                        phase="Phase 1A",
                        category="GSM Integration",
                        item="Google Secrets Manager",
                        status=ValidationStatus.MISSING,
                        expected="GSM integration in config",
                        actual="No GSM references found",
                        details="API keys may still be hardcoded",
                    )
                )

    def group_results_by_phase(self) -> dict[str, list[ValidationResult]]:
        """Group results by phase"""
        grouped = {}
        for result in self.results:
            if result.phase not in grouped:
                grouped[result.phase] = []
            grouped[result.phase].append(result)
        return grouped

    def print_results(
        self, grouped_results: dict[str, list[ValidationResult]]
    ):
        """Print formatted validation results"""
        print("\n" + "=" * 80)
        print("📊 VALIDATION RESULTS")
        print("=" * 80)

        total_items = len(self.results)
        matches = len(
            [r for r in self.results if r.status == ValidationStatus.MATCH]
        )
        mismatches = len(
            [r for r in self.results if r.status == ValidationStatus.MISMATCH]
        )
        missing = len(
            [r for r in self.results if r.status == ValidationStatus.MISSING]
        )

        print("\n📈 Summary:")
        print(f"  Total Checks: {total_items}")
        print(f"  ✅ Matches: {matches} ({matches/total_items*100:.1f}%)")
        print(
            f"  ❌ Mismatches: {mismatches} ({mismatches/total_items*100:.1f}%)"
        )
        print(f"  ⚠️ Missing: {missing} ({missing/total_items*100:.1f}%)")

        for phase, results in sorted(grouped_results.items()):
            print(f"\n{'='*80}")
            print(f"📋 {phase}")
            print(f"{'='*80}")

            # Group by category within phase
            by_category = {}
            for result in results:
                if result.category not in by_category:
                    by_category[result.category] = []
                by_category[result.category].append(result)

            for category, cat_results in sorted(by_category.items()):
                print(f"\n  📂 {category}")
                for result in cat_results:
                    print(f"    {result.status.value}: {result.item}")
                    print(f"       Expected: {result.expected}")
                    print(f"       Actual:   {result.actual}")
                    if result.details:
                        print(f"       Details:  {result.details}")

        # Print action items
        print(f"\n{'='*80}")
        print("🎯 ACTION ITEMS")
        print(f"{'='*80}")

        critical_issues = [
            r
            for r in self.results
            if r.status
            in (ValidationStatus.MISMATCH, ValidationStatus.MISSING)
        ]
        if critical_issues:
            print("\n⚠️ Issues Requiring Attention:")
            for i, result in enumerate(critical_issues[:10], 1):
                print(f"\n{i}. {result.phase} - {result.category}")
                print(f"   Item: {result.item}")
                print(f"   Expected: {result.expected}")
                print(f"   Actual: {result.actual}")

            if len(critical_issues) > 10:
                print(f"\n   ... and {len(critical_issues) - 10} more issues")
        else:
            print("\n✅ All validation checks passed!")


def main():
    workspace_root = Path(__file__).parent.parent
    validator = PhaseValidator(workspace_root)

    grouped_results = validator.validate_all_phases()
    validator.print_results(grouped_results)

    # Return exit code based on results
    critical_issues = len(
        [
            r
            for r in validator.results
            if r.status
            in (ValidationStatus.MISMATCH, ValidationStatus.MISSING)
        ]
    )

    if critical_issues > 0:
        print(f"\n⚠️ Validation completed with {critical_issues} issues")
        return 1
    else:
        print("\n✅ Validation completed successfully")
        return 0


if __name__ == "__main__":
    sys.exit(main())
