#!/usr/bin/env python3
"""
Repository Guard Script - Comprehensive Security & Quality Enforcement

This script enforces repository hygiene, separation rules, and security
policies. Fails build on violations. Designed for CI/CD integration.

Author: Release Management Team
Date: September 1, 2025
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from colorama import Fore, Style, init

# Initialize colorama for cross-platform colored output
init()


@dataclass
class Violation:
    """Represents a single policy violation"""

    file_path: str
    violation_type: str
    description: str
    line_number: int = 0
    content: str = ""


class RepositoryGuard:
    """Main guard class for repository policy enforcement"""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.violations: list[Violation] = []
        self.stats = {
            "files_scanned": 0,
            "empty_files": 0,
            "placeholder_violations": 0,
            "security_violations": 0,
            "separation_violations": 0,
            "cross_import_violations": 0,
        }

        # Define folder structure and rules
        self.folders = {
            "myhibachi-frontend": {
                "type": "Next.js Frontend",
                "allowed_env_pattern": r"NEXT_PUBLIC_",
                "forbidden_imports": [
                    r"\.\.\/myhibachi-.*backend",
                    r"stripe.*server",
                    r"process\.env\.(?!NEXT_PUBLIC_)",
                ],
                "dev_port": 3000,
            },
            "myhibachi-backend-fastapi": {
                "type": "FastAPI Backend",
                "allowed_stripe": True,
                "dev_port": 8000,
            },
            "myhibachi-backend": {
                "type": "Legacy Backend (DEPRECATED)",
                "deprecated": True,
                "forbidden_routes": [r"/api/stripe/"],
                "dev_port": 8001,
            },
            "myhibachi-ai-backend": {
                "type": "AI Backend",
                "forbidden_env": [
                    "STRIPE_SECRET_KEY",
                    "STRIPE_WEBHOOK_SECRET",
                ],
                "dev_port": 8002,
            },
        }

        # Security patterns
        self.secret_patterns = [
            (r"sk_live_[a-zA-Z0-9]{99,}", "Live Stripe Secret Key"),
            (r"sk_test_[a-zA-Z0-9]{99,}", "Test Stripe Secret Key"),
            (r"whsec_[a-zA-Z0-9]{32,}", "Stripe Webhook Secret"),
            (
                r"pk_live_[a-zA-Z0-9]{99,}",
                "Live Stripe Publishable Key (should be in env)",
            ),
            (r"rk_live_[a-zA-Z0-9]{99,}", "Live Stripe Restricted Key"),
        ]

        # Placeholder patterns
        self.placeholder_patterns = [
            (r"\bTODO\b(?!\s*:?\s*\w)", "TODO placeholder"),
            (r"\bFIXME\b(?!\s*:?\s*\w)", "FIXME placeholder"),
            (r"\blorem\s+ipsum\b", "Lorem ipsum placeholder"),
            (r"\bREPLACEME\b", "REPLACEME placeholder"),
            (r"\byour[_-]?key[_-]?here\b", "Your key here placeholder"),
            (r"\bplaceholder[_-]?text\b", "Placeholder text"),
        ]

        # File patterns to skip
        self.skip_patterns = [
            r"\.git/",
            r"node_modules/",
            r"__pycache__/",
            r"\.next/",
            r"\.venv/",
            r"\.env\.local$",
            r"\.env$",
            r"BUILD_ID$",
            r"\.(lock|log|pyc|jpg|png|ico|svg|woff|woff2|ttf|eot)$",
            r"package-lock\.json$",
            r"yarn\.lock$",
            r"\.git",
            r"CHANGELOG",
            r"LICENSE",
        ]

    def should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped based on patterns"""
        relative_path = str(file_path.relative_to(self.repo_root))
        for pattern in self.skip_patterns:
            if re.search(pattern, relative_path, re.IGNORECASE):
                return True
        return False

    def scan_file_for_violations(self, file_path: Path) -> None:
        """Scan a single file for all types of violations"""
        if self.should_skip_file(file_path):
            return

        relative_path = str(file_path.relative_to(self.repo_root))
        self.stats["files_scanned"] += 1

        try:
            # Check for empty files
            if file_path.stat().st_size == 0:
                if file_path.name != ".gitkeep":
                    self.violations.append(
                        Violation(
                            relative_path,
                            "EMPTY_FILE",
                            "Zero-byte file detected",
                        )
                    )
                    self.stats["empty_files"] += 1
                return

            # Read file content
            try:
                content = file_path.read_text(
                    encoding="utf-8", errors="ignore"
                )
            except Exception:
                return  # Skip binary files

            # Check for whitespace-only files
            if content.strip() == "":
                self.violations.append(
                    Violation(
                        relative_path,
                        "WHITESPACE_ONLY",
                        "File contains only whitespace",
                    )
                )
                self.stats["empty_files"] += 1
                return

            lines = content.split("\n")

            # Check for secrets
            self.check_secrets(file_path, content, lines)

            # Check for placeholders (skip README files)
            if not file_path.name.upper().startswith("README"):
                self.check_placeholders(file_path, content, lines)

            # Check folder-specific rules
            self.check_folder_rules(file_path, content, lines)

        except Exception as e:
            # Log but don't fail on file access issues
            print(f"Warning: Could not scan {relative_path}: {e}")

    def check_secrets(
        self, file_path: Path, content: str, lines: list[str]
    ) -> None:
        """Check for hardcoded secrets"""
        relative_path = str(file_path.relative_to(self.repo_root))

        for pattern, description in self.secret_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_num = content[: match.start()].count("\n") + 1
                self.violations.append(
                    Violation(
                        relative_path,
                        "HARDCODED_SECRET",
                        f"{description} found in code",
                        line_num,
                        match.group(),
                    )
                )
                self.stats["security_violations"] += 1

    def check_placeholders(
        self, file_path: Path, content: str, lines: list[str]
    ) -> None:
        """Check for placeholder content"""
        relative_path = str(file_path.relative_to(self.repo_root))

        for pattern, description in self.placeholder_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_num = content[: match.start()].count("\n") + 1
                self.violations.append(
                    Violation(
                        relative_path,
                        "PLACEHOLDER_CONTENT",
                        f"{description} found",
                        line_num,
                        match.group(),
                    )
                )
                self.stats["placeholder_violations"] += 1

    def check_folder_rules(
        self, file_path: Path, content: str, lines: list[str]
    ) -> None:
        """Check folder-specific rules"""
        relative_path = str(file_path.relative_to(self.repo_root))

        # Determine which folder this file belongs to
        folder_name = None
        for folder in self.folders.keys():
            if relative_path.startswith(folder + "/"):
                folder_name = folder
                break

        if not folder_name:
            return

        # Frontend-specific checks
        if folder_name == "myhibachi-frontend":
            self.check_frontend_rules(file_path, content, lines)

        # Legacy backend checks
        elif folder_name == "myhibachi-backend":
            self.check_legacy_backend_rules(file_path, content, lines)

        # AI backend checks
        elif folder_name == "myhibachi-ai-backend":
            self.check_ai_backend_rules(file_path, content, lines)

    def check_frontend_rules(
        self, file_path: Path, content: str, lines: list[str]
    ) -> None:
        """Check frontend-specific rules"""
        relative_path = str(file_path.relative_to(self.repo_root))

        # Check for server-only imports in non-API routes
        if "/api/" not in relative_path and file_path.suffix in [
            ".ts",
            ".tsx",
            ".js",
            ".jsx",
        ]:
            # Check for forbidden imports
            forbidden_patterns = [
                (
                    r'import.*from.*["\']stripe["\']',
                    "Server-side Stripe import in frontend",
                ),
                (
                    r"process\.env\.(?!NEXT_PUBLIC_)",
                    "Non-public environment variable",
                ),
                (
                    r'import.*from.*["\']\.\.\/.*backend',
                    "Cross-boundary import to backend",
                ),
            ]

            for pattern, description in forbidden_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    line_num = content[: match.start()].count("\n") + 1
                    self.violations.append(
                        Violation(
                            relative_path,
                            "FRONTEND_VIOLATION",
                            description,
                            line_num,
                            match.group(),
                        )
                    )
                    self.stats["separation_violations"] += 1

    def check_legacy_backend_rules(
        self, file_path: Path, content: str, lines: list[str]
    ) -> None:
        """Check legacy backend rules"""
        relative_path = str(file_path.relative_to(self.repo_root))

        # Check for forbidden Stripe routes
        if "/api/stripe/" in content:
            self.violations.append(
                Violation(
                    relative_path,
                    "LEGACY_VIOLATION",
                    "Stripe routes forbidden in legacy backend",
                    0,
                    "/api/stripe/ routes detected",
                )
            )
            self.stats["separation_violations"] += 1

    def check_ai_backend_rules(
        self, file_path: Path, content: str, lines: list[str]
    ) -> None:
        """Check AI backend rules"""
        relative_path = str(file_path.relative_to(self.repo_root))

        # Check for forbidden Stripe environment variables
        forbidden_env_vars = ["STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET"]
        for env_var in forbidden_env_vars:
            if env_var in content:
                line_num = next(
                    (i + 1 for i, line in enumerate(lines) if env_var in line),
                    0,
                )
                self.violations.append(
                    Violation(
                        relative_path,
                        "AI_BACKEND_VIOLATION",
                        f"Forbidden Stripe environment variable: {env_var}",
                        line_num,
                        env_var,
                    )
                )
                self.stats["separation_violations"] += 1

    def check_cross_imports(self) -> None:
        """Check for cross-folder imports"""
        for folder_name in self.folders.keys():
            folder_path = self.repo_root / folder_name
            if not folder_path.exists():
                continue

            for file_path in folder_path.rglob("*"):
                if file_path.is_file() and file_path.suffix in [
                    ".ts",
                    ".tsx",
                    ".js",
                    ".jsx",
                    ".py",
                ]:
                    if self.should_skip_file(file_path):
                        continue

                    try:
                        content = file_path.read_text(
                            encoding="utf-8", errors="ignore"
                        )
                        self.check_file_cross_imports(
                            file_path, content, folder_name
                        )
                    except Exception:
                        continue

    def check_file_cross_imports(
        self, file_path: Path, content: str, current_folder: str
    ) -> None:
        """Check a single file for cross-folder imports"""
        relative_path = str(file_path.relative_to(self.repo_root))

        # Look for imports to other project folders
        for other_folder in self.folders.keys():
            if other_folder != current_folder:
                # Pattern to match imports to other folders
                patterns = [
                    rf'import.*from.*["\']\.\.\/.*{other_folder}',
                    rf'import.*["\']\.\.\/.*{other_folder}',
                    rf'require\(["\']\.\.\/.*{other_folder}',
                ]

                for pattern in patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        line_num = content[: match.start()].count("\n") + 1
                        self.violations.append(
                            Violation(
                                relative_path,
                                "CROSS_IMPORT_VIOLATION",
                                f"Cross-folder import from {current_folder} "
                                f"to {other_folder}",
                                line_num,
                                match.group(),
                            )
                        )
                        self.stats["cross_import_violations"] += 1

    def check_port_collisions(self) -> None:
        """Check for port collisions in configuration files"""
        expected_ports = {
            folder: config["dev_port"]
            for folder, config in self.folders.items()
            if "dev_port" in config
        }

        for folder_name, expected_port in expected_ports.items():
            folder_path = self.repo_root / folder_name
            if not folder_path.exists():
                continue

            # Check common config files for port definitions
            config_files = [
                "package.json",
                "next.config.js",
                "next.config.ts",
                "main.py",
                "app.py",
                "server.py",
                ".env.example",
            ]

            for config_file in config_files:
                config_path = folder_path / config_file
                if config_path.exists():
                    try:
                        content = config_path.read_text(encoding="utf-8")
                        self.check_port_in_file(
                            config_path, content, expected_port, folder_name
                        )
                    except Exception:
                        continue

    def check_port_in_file(
        self,
        file_path: Path,
        content: str,
        expected_port: int,
        folder_name: str,
    ) -> None:
        """Check for incorrect port assignments in a file"""
        relative_path = str(file_path.relative_to(self.repo_root))

        # Look for port assignments that don't match expected
        port_patterns = [
            r'PORT["\']?\s*[:=]\s*(\d+)',
            r'port["\']?\s*[:=]\s*(\d+)',
            r"listen\s*\(\s*(\d+)",
            r"--port\s+(\d+)",
        ]

        for pattern in port_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                found_port = int(match.group(1))
                if found_port != expected_port and found_port in [
                    3000,
                    8000,
                    8001,
                    8002,
                ]:
                    line_num = content[: match.start()].count("\n") + 1
                    self.violations.append(
                        Violation(
                            relative_path,
                            "PORT_COLLISION",
                            f"Port {found_port} conflicts with expected "
                            f"{expected_port} for {folder_name}",
                            line_num,
                            match.group(),
                        )
                    )

    def scan_repository(self) -> None:
        """Main scanning method"""
        print(
            f"{Fore.CYAN}🛡️ Repository Guard - Scanning "
            f"{self.repo_root}{Style.RESET_ALL}"
        )

        # Scan all files in the repository
        for folder_name in self.folders.keys():
            folder_path = self.repo_root / folder_name
            if folder_path.exists():
                print(f"  📁 Scanning {folder_name}...")
                for file_path in folder_path.rglob("*"):
                    if file_path.is_file():
                        self.scan_file_for_violations(file_path)

        # Perform cross-cutting checks
        print("  🔗 Checking cross-imports...")
        self.check_cross_imports()

        print("  🔌 Checking port assignments...")
        self.check_port_collisions()

    def print_violations_table(self) -> None:
        """Print violations in a formatted table"""
        if not self.violations:
            print(f"{Fore.GREEN}✅ No violations found!{Style.RESET_ALL}")
            return

        print(f"\n{Fore.RED}❌ VIOLATIONS DETECTED:{Style.RESET_ALL}")
        print("=" * 100)

        # Group violations by type
        violations_by_type = {}
        for violation in self.violations:
            if violation.violation_type not in violations_by_type:
                violations_by_type[violation.violation_type] = []
            violations_by_type[violation.violation_type].append(violation)

        # Print each type
        for violation_type, type_violations in violations_by_type.items():
            print(
                f"\n{Fore.YELLOW}{violation_type} "
                f"({len(type_violations)} issues):{Style.RESET_ALL}"
            )
            for violation in type_violations[
                :10
            ]:  # Limit to first 10 per type
                line_info = (
                    f" (line {violation.line_number})"
                    if violation.line_number
                    else ""
                )
                print(f"  📁 {violation.file_path}{line_info}")
                print(f"     {violation.description}")
                if violation.content:
                    print(f"     Content: {violation.content[:100]}...")

            if len(type_violations) > 10:
                print(f"     ... and {len(type_violations) - 10} more")

    def print_statistics(self) -> None:
        """Print scanning statistics"""
        print(f"\n{Fore.CYAN}📊 SCAN STATISTICS:{Style.RESET_ALL}")
        print(f"Files scanned: {self.stats['files_scanned']}")
        print(f"Empty files: {self.stats['empty_files']}")
        print(
            f"Placeholder violations: {self.stats['placeholder_violations']}"
        )
        print(f"Security violations: {self.stats['security_violations']}")
        print(f"Separation violations: {self.stats['separation_violations']}")
        print(
            f"Cross-import violations: {self.stats['cross_import_violations']}"
        )
        print(f"Total violations: {len(self.violations)}")

    def generate_json_report(self, output_path: Path) -> None:
        """Generate JSON report for CI integration"""
        report = {
            "timestamp": "2025-09-01",
            "repository": str(self.repo_root),
            "statistics": self.stats,
            "violations": [
                {
                    "file": v.file_path,
                    "type": v.violation_type,
                    "description": v.description,
                    "line": v.line_number,
                    "content": v.content,
                }
                for v in self.violations
            ],
            "folders_scanned": list(self.folders.keys()),
            "passed": len(self.violations) == 0,
        }

        output_path.write_text(json.dumps(report, indent=2))
        print(f"📄 JSON report written to: {output_path}")

    def run(self, json_output: Path = None) -> bool:
        """Run the complete guard check"""
        self.scan_repository()
        self.print_violations_table()
        self.print_statistics()

        if json_output:
            self.generate_json_report(json_output)

        # Return success/failure
        if self.violations:
            print(
                f"\n{Fore.RED}💥 GUARD CHECK FAILED - "
                f"{len(self.violations)} violations found{Style.RESET_ALL}"
            )
            return False
        else:
            print(
                f"\n{Fore.GREEN}✅ GUARD CHECK PASSED - "
                f"Repository is clean{Style.RESET_ALL}"
            )
            return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Repository Guard - Security & Quality Enforcement"
    )
    parser.add_argument(
        "--json-output", type=Path, help="Output JSON report to file"
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root path",
    )

    args = parser.parse_args()

    # Ensure we're in a valid repository
    repo_root = args.repo_root.resolve()
    if not any(
        (repo_root / folder).exists()
        for folder in ["myhibachi-frontend", "myhibachi-backend-fastapi"]
    ):
        print(
            f"{Fore.RED}❌ Not a valid My Hibachi repository "
            f"root{Style.RESET_ALL}"
        )
        sys.exit(1)

    # Run the guard
    guard = RepositoryGuard(repo_root)
    success = guard.run(args.json_output)

    # Exit with appropriate code for CI
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
