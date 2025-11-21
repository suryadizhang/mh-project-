#!/usr/bin/env python3
"""
Targeted Critical Bug Fixer
Fixes the top critical issues found in emergency scan
"""

from datetime import UTC, datetime
import json
from pathlib import Path
import re


class TargetedBugFixer:
    def __init__(self, root_dir="apps"):
        self.root_dir = Path(root_dir)
        self.fixes_applied = []

    def fix_timezone_naive_datetime(self):
        """Fix timezone-naive datetime.utcnow() usage"""
        print("🕐 Fixing timezone-naive datetime issues...")

        pattern = r"datetime\.utcnow\s*\(\s*\)"
        replacement = "datetime.now(timezone.utc)"

        critical_files = [
            "backend/tests/conftest.py",
            "backend/tests/test_api_cte_queries.py",
            "backend/src/models/legacy_booking_models.py",
            "backend/src/api/ai/endpoints/services/pricing_service.py",
        ]

        fixes = 0
        for file_path in critical_files:
            full_path = self.root_dir / file_path
            if not full_path.exists():
                continue

            try:
                with open(full_path, encoding="utf-8") as f:
                    content = f.read()

                # Check if timezone import exists
                has_timezone_import = (
                    "from datetime import" in content and "timezone" in content
                )

                original_content = content
                content = re.sub(pattern, replacement, content)

                if content != original_content:
                    # Add timezone import if missing
                    if not has_timezone_import:
                        if "from datetime import datetime" in content:
                            content = content.replace(
                                "from datetime import datetime",
                                "from datetime import datetime, timezone",
                            )
                        elif "import datetime" in content:
                            content = content.replace(
                                "import datetime",
                                "import datetime\nfrom datetime import timezone",
                            )

                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write(content)

                    file_fixes = len(re.findall(pattern, original_content))
                    fixes += file_fixes

                    self.fixes_applied.append(
                        {
                            "file": str(file_path),
                            "type": "timezone_naive",
                            "fixes": file_fixes,
                            "description": f"Fixed {file_fixes} timezone-naive datetime calls",
                        }
                    )

                    print(f"  ✅ Fixed {file_fixes} issues in {file_path}")

            except Exception as e:
                print(f"  ❌ Error fixing {file_path}: {e}")

        return fixes

    def fix_undefined_error_codes(self):
        """Fix undefined error codes (Bug #15 from audit)"""
        print("🚨 Fixing undefined error codes...")

        # Based on FOURTH_ROUND_DEEP_AUDIT_BUGS_13_15.md findings
        error_code_fixes = {
            "ErrorCode.INVALID_BOOKING_STATE": "ErrorCode.BAD_REQUEST",
            "ErrorCode.DATA_INTEGRITY_ERROR": "ErrorCode.INTERNAL_ERROR",
            "ErrorCode.PAYMENT_AMOUNT_INVALID": "ErrorCode.BAD_REQUEST",
        }

        booking_service_path = (
            self.root_dir / "backend/src/services/booking_service.py"
        )

        if not booking_service_path.exists():
            print(f"  ⚠️ Booking service not found: {booking_service_path}")
            return 0

        fixes = 0
        try:
            with open(booking_service_path, encoding="utf-8") as f:
                content = f.read()

            original_content = content

            for undefined_code, replacement in error_code_fixes.items():
                if undefined_code in content:
                    content = content.replace(undefined_code, replacement)
                    fixes += 1
                    print(f"  ✅ Replaced {undefined_code} with {replacement}")

            if content != original_content:
                with open(booking_service_path, "w", encoding="utf-8") as f:
                    f.write(content)

                self.fixes_applied.append(
                    {
                        "file": "backend/src/services/booking_service.py",
                        "type": "undefined_error_codes",
                        "fixes": fixes,
                        "description": f"Fixed {fixes} undefined error code references",
                    }
                )

        except Exception as e:
            print(f"  ❌ Error fixing error codes: {e}")

        return fixes

    def fix_silent_exceptions(self):
        """Fix dangerous silent exception patterns"""
        print("⚠️ Fixing silent exceptions...")

        pattern = r"except\s*:\s*(?:pass|return|continue)(?:\s*#.*)?$"

        python_files = list(self.root_dir.rglob("*.py"))
        fixes = 0

        for py_file in python_files:
            if "test" in str(py_file) or "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file, encoding="utf-8") as f:
                    lines = f.readlines()

                modified = False
                for i, line in enumerate(lines):
                    if re.search(pattern, line, re.MULTILINE):
                        # Replace silent exception with logged exception
                        if "pass" in line:
                            lines[i] = line.replace(
                                "pass",
                                'logger.warning(f"Silent exception in {py_file.name}:{i+1}: {e}")',
                            )
                        elif "return" in line and "return None" not in line:
                            lines[i] = line.replace(
                                "return",
                                'logger.error(f"Exception in {py_file.name}:{i+1}: {e}"); return',
                            )

                        modified = True
                        fixes += 1

                if modified:
                    # Add logger import if missing
                    has_logging = any(
                        "import logging" in line or "logger =" in line
                        for line in lines[:20]
                    )
                    if not has_logging:
                        lines.insert(
                            0,
                            "import logging\nlogger = logging.getLogger(__name__)\n\n",
                        )

                    with open(py_file, "w", encoding="utf-8") as f:
                        f.writelines(lines)

                    print(
                        f"  ✅ Fixed silent exceptions in {py_file.relative_to(self.root_dir)}"
                    )

            except Exception as e:
                print(f"  ❌ Error processing {py_file}: {e}")

        return fixes

    def run_targeted_fixes(self):
        """Run all targeted critical fixes"""
        print("🚀 Starting targeted critical bug fixes...")
        print("=" * 50)

        total_fixes = 0

        # Fix timezone issues (highest priority - data corruption)
        total_fixes += self.fix_timezone_naive_datetime()

        # Fix undefined error codes (production crashes)
        total_fixes += self.fix_undefined_error_codes()

        # Fix silent exceptions (debugging issues)
        total_fixes += self.fix_silent_exceptions()

        print("=" * 50)
        print("🎉 TARGETED FIXES COMPLETE!")
        print(f"📊 Total fixes applied: {total_fixes}")
        print(f"📋 Files modified: {len(self.fixes_applied)}")

        # Save fix report
        report = {
            "timestamp": datetime.now(UTC).isoformat(),
            "total_fixes": total_fixes,
            "fixes_applied": self.fixes_applied,
        }

        with open("targeted_critical_fixes.json", "w") as f:
            json.dump(report, f, indent=2)

        print("📄 Detailed report: targeted_critical_fixes.json")

        if total_fixes > 0:
            print("\n🎯 NEXT STEPS:")
            print("  1. Run tests: python -m pytest apps/backend/tests/ -v")
            print("  2. Check git diff: git diff")
            print(
                "  3. Commit fixes: git add -A && git commit -m '🚨 Fix critical timezone and error code bugs'"
            )

        return total_fixes


if __name__ == "__main__":
    fixer = TargetedBugFixer()
    fixes = fixer.run_targeted_fixes()

    if fixes > 0:
        print(f"\n✅ SUCCESS: Applied {fixes} critical fixes!")
        exit(0)
    else:
        print("\n⚠️ No fixes applied - check file paths and patterns")
        exit(1)
