#!/usr/bin/env python3
"""
Safety guard script for My Hibachi project.
Fails build if violations are found.
"""

import os
import re
import sys
from pathlib import Path


class GuardViolation:
    def __init__(self, file_path: str, violation_type: str, details: str):
        self.file_path = file_path
        self.violation_type = violation_type
        self.details = details


class ProjectGuard:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.violations: list[GuardViolation] = []

        # Files to skip in checks
        self.skip_patterns = [
            r"\.git/",
            r"node_modules/",
            r"__pycache__/",
            r"\.next/",
            r"\.venv/",
            r"\.env\.local$",
            r"\.env$",
            r"BUILD_ID$",
            r"\.lock$",
            r"\.log$",
            r"\.pyc$",
            r"\.jpg$",
            r"\.png$",
            r"\.ico$",
            r"\.svg$",
            r"\.md$",  # Skip markdown files for placeholder checks
        ]

        # Dangerous patterns
        self.secret_patterns = [
            (r"sk_live_[a-zA-Z0-9]{99,}", "Live Stripe Secret Key"),
            (r"sk_test_[a-zA-Z0-9]{99,}", "Test Stripe Secret Key"),
            (r"whsec_[a-zA-Z0-9]{32,}", "Stripe Webhook Secret"),
            (r"pk_live_[a-zA-Z0-9]{99,}", "Live Stripe Publishable Key"),
        ]

        # Placeholder patterns (skip in .md files)
        self.placeholder_patterns = [
            r"TODO(?:\s|:)",
            r"FIXME(?:\s|:)",
            r"your[_-]?key[_-]?here",
            r"your[_-]?key[_-]?here",
            r"lorem\s+ipsum",
            r"placeholder[_-]?text",
        ]

        # Frontend server-only env vars
        self.server_only_env_vars = [
            "STRIPE_SECRET_KEY",
            "STRIPE_WEBHOOK_SECRET",
            "DATABASE_URL",
            "SECRET_KEY",
            "POSTGRES_PASSWORD",
        ]

    def should_skip_file(self, file_path: str) -> bool:
        """Check if file should be skipped based on patterns."""
        relative_path = os.path.relpath(file_path, self.project_root)
        for pattern in self.skip_patterns:
            if re.search(pattern, relative_path):
                return True
        return False

    def check_empty_files(self) -> None:
        """Check for empty files or files with only whitespace."""
        print("🔍 Checking for empty files...")

        for root, dirs, files in os.walk(self.project_root):
            for file in files:
                file_path = os.path.join(root, file)

                if self.should_skip_file(file_path):
                    continue

                try:
                    with open(
                        file_path, encoding="utf-8", errors="ignore"
                    ) as f:
                        content = f.read()

                    if len(content.strip()) == 0:
                        self.violations.append(
                            GuardViolation(
                                file_path,
                                "EMPTY_FILE",
                                "File is empty or contains only whitespace",
                            )
                        )
                except Exception:
                    # Skip binary files or files that can't be read
                    continue

    def check_secrets(self) -> None:
        """Check for exposed secrets."""
        print("🔍 Checking for exposed secrets...")

        for root, dirs, files in os.walk(self.project_root):
            for file in files:
                file_path = os.path.join(root, file)

                if self.should_skip_file(file_path):
                    continue

                try:
                    with open(
                        file_path, encoding="utf-8", errors="ignore"
                    ) as f:
                        content = f.read()

                    for pattern, secret_type in self.secret_patterns:
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            # Get line number
                            line_num = content[: match.start()].count("\n") + 1
                            self.violations.append(
                                GuardViolation(
                                    file_path,
                                    "SECRET_EXPOSED",
                                    f"{secret_type} found at line {line_num}: {match.group()[:20]}...",
                                )
                            )
                except Exception:
                    continue

    def check_placeholders(self) -> None:
        """Check for placeholder content."""
        print("🔍 Checking for placeholder content...")

        for root, dirs, files in os.walk(self.project_root):
            for file in files:
                file_path = os.path.join(root, file)

                if self.should_skip_file(file_path) or file_path.endswith(
                    ".md"
                ):
                    continue

                try:
                    with open(
                        file_path, encoding="utf-8", errors="ignore"
                    ) as f:
                        content = f.read()

                    for pattern in self.placeholder_patterns:
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            line_num = content[: match.start()].count("\n") + 1
                            self.violations.append(
                                GuardViolation(
                                    file_path,
                                    "PLACEHOLDER",
                                    f"Placeholder found at line {line_num}: {match.group()}",
                                )
                            )
                except Exception:
                    continue

    def check_frontend_backend_separation(self) -> None:
        """Check for improper frontend/backend imports."""
        print("🔍 Checking frontend/backend separation...")

        frontend_path = self.project_root / "myhibachi-frontend"
        backend_path = self.project_root / "myhibachi-backend-fastapi"

        if not frontend_path.exists() or not backend_path.exists():
            return

        # Check frontend files
        for root, dirs, files in os.walk(frontend_path):
            for file in files:
                if not file.endswith((".ts", ".tsx", ".js", ".jsx")):
                    continue

                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, self.project_root)

                # Skip Next.js API routes - they're server-side
                if (
                    "/api/" in relative_path
                    or file_path.endswith("route.ts")
                    or file_path.endswith("route.js")
                ):
                    continue

                # Skip server-only services that are only used by API routes
                if (
                    "/services/" in relative_path
                    and (
                        "stripe" in file.lower() or "customer" in file.lower()
                    )
                ) or "/lib/server/" in relative_path:
                    continue

                try:
                    with open(file_path, encoding="utf-8") as f:
                        content = f.read()

                    # Check for backend imports
                    if re.search(r'from\s+["\']\.\.\/.*backend', content):
                        self.violations.append(
                            GuardViolation(
                                file_path,
                                "CROSS_BOUNDARY_IMPORT",
                                "Frontend importing from backend",
                            )
                        )

                    # Check for server-only env vars
                    for env_var in self.server_only_env_vars:
                        if f"process.env.{env_var}" in content:
                            self.violations.append(
                                GuardViolation(
                                    file_path,
                                    "SERVER_ENV_IN_FRONTEND",
                                    f"Server-only env var {env_var} used in frontend",
                                )
                            )
                except Exception:
                    continue

    def run_all_checks(self) -> bool:
        """Run all guard checks and return True if passed."""
        print("🛡️  Running Project Guard Checks...")

        self.check_empty_files()
        self.check_secrets()
        self.check_placeholders()
        self.check_frontend_backend_separation()

        return len(self.violations) == 0

    def print_report(self) -> None:
        """Print violations report."""
        if not self.violations:
            print("✅ All guard checks passed!")
            return

        print(f"\n❌ Found {len(self.violations)} violations:")
        print("=" * 60)

        by_type = {}
        for violation in self.violations:
            if violation.violation_type not in by_type:
                by_type[violation.violation_type] = []
            by_type[violation.violation_type].append(violation)

        for violation_type, violations in by_type.items():
            print(f"\n{violation_type} ({len(violations)} issues):")
            for violation in violations:
                rel_path = os.path.relpath(
                    violation.file_path, self.project_root
                )
                print(f"  📁 {rel_path}")
                print(f"     {violation.details}")


def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    guard = ProjectGuard(project_root)

    passed = guard.run_all_checks()
    guard.print_report()

    if not passed:
        sys.exit(1)

    print("\n🎉 Project guard checks completed successfully!")


if __name__ == "__main__":
    main()
