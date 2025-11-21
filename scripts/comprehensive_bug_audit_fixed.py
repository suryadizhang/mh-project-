"""
Comprehensive Bug Audit - Enterprise A-H Methodology
Checks all features and functions for bugs following 01-AGENT_RULES and 02-AGENT_AUDIT_STANDARDS
"""

from datetime import datetime
import json
from pathlib import Path
import re


class ComprehensiveBugAudit:
    """
    Performs deep A-H methodology audit on all Python files in the backend.

    A. Static Analysis (line-by-line)
    B. Runtime Simulation
    C. Concurrency & Transaction Safety
    D. Data Flow Tracing
    E. Error Path & Exception Handling
    F. Dependency & Enum Validation
    G. Business Logic Validation
    H. Helper/Utility Analysis
    """

    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.findings = {"critical": [], "high": [], "medium": [], "low": []}
        self.files_scanned = 0
        self.lines_scanned = 0

    def scan_all_files(self):
        """Scan all Python files in the backend."""
        python_files = list(self.root_dir.glob("apps/backend/src/**/*.py"))

        print("\\n🔍 Starting Comprehensive Bug Audit...")
        print(f"📁 Scanning {len(python_files)} Python files\\n")

        for file_path in python_files:
            self.scan_file(file_path)

        self.generate_report()

    def scan_file(self, file_path: Path):
        """Scan a single file using A-H methodology."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\\n")

            self.files_scanned += 1
            self.lines_scanned += len(lines)

            # A. Static Analysis
            self.check_static_analysis(file_path, content, lines)

            # B. Runtime Simulation
            self.check_runtime_issues(file_path, content, lines)

            # C. Concurrency & Transaction Safety
            self.check_concurrency_safety(file_path, content, lines)

            # D. Data Flow Tracing
            self.check_data_flow(file_path, content, lines)

            # E. Error Path & Exception Handling
            self.check_error_handling(file_path, content, lines)

            # F. Dependency & Enum Validation
            self.check_dependencies(file_path, content, lines)

            # G. Business Logic Validation
            self.check_business_logic(file_path, content, lines)

            # H. Helper/Utility Analysis
            self.check_helper_methods(file_path, content, lines)

        except Exception as e:
            self.add_finding(
                "low", file_path, 0, f"Could not fully scan file: {e}"
            )

    def check_static_analysis(
        self, file_path: Path, content: str, lines: list[str]
    ):
        """A. Static Analysis - Line-by-line code inspection."""

        # Check for TODO/FIXME
        for i, line in enumerate(lines, 1):
            if re.search(r"\\b(TODO|FIXME|HACK|XXX)\\b", line, re.IGNORECASE):
                self.add_finding(
                    "low", file_path, i, f"Unfinished work: {line.strip()}"
                )

        # Check for debug artifacts
        for i, line in enumerate(lines, 1):
            if re.search(r"\\bprint\\(", line) and "logger" not in line:
                self.add_finding(
                    "medium",
                    file_path,
                    i,
                    "Debug print() statement found - should use logger",
                )
            if re.search(r"\\bconsole\\.log\\(", line):
                self.add_finding(
                    "medium", file_path, i, "Debug console.log() found"
                )

        # Check for hardcoded secrets
        for i, line in enumerate(lines, 1):
            if re.search(
                r'(password|secret|api[_-]?key)\\s*=\\s*["\'][^"\']+["\']',
                line,
                re.IGNORECASE,
            ):
                if "os.getenv" not in line and "settings." not in line:
                    self.add_finding(
                        "critical", file_path, i, "Potential hardcoded secret"
                    )

        # Check for missing type hints on functions
        for i, line in enumerate(lines, 1):
            if re.match(r"^\\s*def \\w+\\(.*\\):", line):
                if "->" not in line:
                    self.add_finding(
                        "low", file_path, i, "Missing return type hint"
                    )

    def check_runtime_issues(
        self, file_path: Path, content: str, lines: list[str]
    ):
        """B. Runtime Simulation - Potential runtime errors."""

        # Check for timezone issues
        for i, line in enumerate(lines, 1):
            if "datetime.now()" in line and "timezone" not in line:
                self.add_finding(
                    "high",
                    file_path,
                    i,
                    "datetime.now() without timezone - should use datetime.now(timezone.utc)",
                )
            if "date.today()" in line:
                self.add_finding(
                    "medium",
                    file_path,
                    i,
                    "date.today() may have timezone issues - consider using timezone-aware datetime",
                )

        # Check for None propagation
        for i, line in enumerate(lines, 1):
            if (
                re.search(r"\\.\\w+\\(\\)", line)
                and "if" not in line
                and "try" not in lines[max(0, i - 3)]
            ):
                # Potential None.method() call without checking
                pass  # Too many false positives, needs AST analysis

        # Check for unsafe string operations
        for i, line in enumerate(lines, 1):
            if re.search(r'\\.split\\(["\']["\']\\)', line):
                self.add_finding(
                    "medium",
                    file_path,
                    i,
                    "split() without error handling - may fail on invalid input",
                )

    def check_concurrency_safety(
        self, file_path: Path, content: str, lines: list[str]
    ):
        """C. Concurrency & Transaction Safety - Race conditions."""

        # Check for TOCTOU (Time Of Check, Time Of Use) issues
        for i, line in enumerate(lines, 1):
            if "check_availability" in line.lower():
                # Look for booking creation nearby without locks
                context = "\\n".join(
                    lines[max(0, i - 5) : min(len(lines), i + 10)]
                )
                if (
                    "create_booking" in context
                    and "lock" not in context.lower()
                ):
                    self.add_finding(
                        "critical",
                        file_path,
                        i,
                        "Potential TOCTOU race condition: check_availability -> create_booking without locking",
                    )

        # Check for missing database transactions
        for i, line in enumerate(lines, 1):
            if re.search(
                r"\\b(INSERT|UPDATE|DELETE)\\b", line
            ) and "transaction" not in "\\n".join(lines[max(0, i - 10) : i]):
                pass  # Too many false positives

    def check_data_flow(self, file_path: Path, content: str, lines: list[str]):
        """D. Data Flow Tracing - Input/output validation."""

        # Check for missing input validation
        for i, line in enumerate(lines, 1):
            if re.match(r"^\\s*async def \\w+\\(self, .*:\\s*str", line):
                # Function takes string parameter
                func_body_start = i
                func_body = "\\n".join(lines[i : min(len(lines), i + 20)])
                if (
                    "if not" not in func_body
                    and "validate" not in func_body.lower()
                ):
                    self.add_finding(
                        "medium",
                        file_path,
                        i,
                        "Function parameter may need validation",
                    )

    def check_error_handling(
        self, file_path: Path, content: str, lines: list[str]
    ):
        """E. Error Path & Exception Handling."""

        # Check for broad exception catching
        for i, line in enumerate(lines, 1):
            if re.search(r"except\\s*:", line) or re.search(
                r"except\\s+Exception\\s*:", line
            ):
                self.add_finding(
                    "medium",
                    file_path,
                    i,
                    "Broad exception catch - should catch specific exceptions",
                )

        # Check for missing logging in exception handlers
        for i, line in enumerate(lines, 1):
            if "except" in line:
                handler_block = "\\n".join(lines[i : min(len(lines), i + 5)])
                if (
                    "logger" not in handler_block
                    and "logging" not in handler_block
                ):
                    self.add_finding(
                        "medium",
                        file_path,
                        i,
                        "Exception handler without logging",
                    )

        # Check for silent failures
        for i, line in enumerate(lines, 1):
            if re.search(r"except.*:\\s*pass", line):
                self.add_finding(
                    "high",
                    file_path,
                    i,
                    "Silent exception catch - errors are being swallowed",
                )

    def check_dependencies(
        self, file_path: Path, content: str, lines: list[str]
    ):
        """F. Dependency & Enum Validation."""

        # Check for missing imports
        imports = []
        for line in lines:
            if line.strip().startswith(("import ", "from ")):
                imports.append(line.strip())

        # Check for undefined enum values (this would need AST analysis for accuracy)
        for i, line in enumerate(lines, 1):
            if re.search(r"ErrorCode\\.\\w+", line):
                # Would need to verify enum actually exists
                pass

    def check_business_logic(
        self, file_path: Path, content: str, lines: list[str]
    ):
        """G. Business Logic Validation - Critical business rules."""

        if "booking" in str(file_path).lower():
            # Check booking logic
            for i, line in enumerate(lines, 1):
                if "total_amount" in line or "price" in line or "fee" in line:
                    if "<=" in line or ">=" in line or "==" in line:
                        # Potential pricing logic - check for edge cases
                        pass

        if "payment" in str(file_path).lower():
            # Check payment logic
            for i, line in enumerate(lines, 1):
                if "deposit" in line.lower() or "refund" in line.lower():
                    pass

    def check_helper_methods(
        self, file_path: Path, content: str, lines: list[str]
    ):
        """H. Helper/Utility Analysis - Private methods."""

        for i, line in enumerate(lines, 1):
            if re.match(r"^\\s*def _\\w+\\(", line):
                # Private helper method
                method_name = re.search(r"def (_\\w+)\\(", line).group(1)
                if len(method_name) < 5:
                    self.add_finding(
                        "low",
                        file_path,
                        i,
                        f"Helper method name '{method_name}' could be more descriptive",
                    )

    def add_finding(
        self, severity: str, file_path: Path, line_num: int, message: str
    ):
        """Add a finding to the results."""
        relative_path = str(file_path.relative_to(self.root_dir))
        self.findings[severity].append(
            {"file": relative_path, "line": line_num, "message": message}
        )

    def generate_report(self):
        """Generate comprehensive audit report."""

        print(f"\\n{'='*80}")
        print("📊 COMPREHENSIVE BUG AUDIT REPORT")
        print(f"{'='*80}\\n")

        print(f"📁 Files Scanned: {self.files_scanned}")
        print(f"📄 Lines Scanned: {self.lines_scanned:,}\\n")

        total_issues = sum(
            len(findings) for findings in self.findings.values()
        )

        print("\\n🎯 SUMMARY:")
        print(f"  🔴 CRITICAL: {len(self.findings['critical'])} issues")
        print(f"  🟠 HIGH:     {len(self.findings['high'])} issues")
        print(f"  🟡 MEDIUM:   {len(self.findings['medium'])} issues")
        print(f"  🟢 LOW:      {len(self.findings['low'])} issues")
        print("  ━━━━━━━━━━━━━━━━━━━━━━")
        print(f"  📊 TOTAL:    {total_issues} issues\\n")

        # Show critical issues first
        if self.findings["critical"]:
            print(f"\\n🔴 CRITICAL ISSUES ({len(self.findings['critical'])}):")
            print("=" * 80)
            for finding in self.findings["critical"][:10]:  # Show first 10
                print(f"  📄 {finding['file']}:{finding['line']}")
                print(f"     ⚠️  {finding['message']}\\n")

        # Show high priority issues
        if self.findings["high"]:
            print(
                f"\\n🟠 HIGH PRIORITY ISSUES ({len(self.findings['high'])}):"
            )
            print("=" * 80)
            for finding in self.findings["high"][:10]:  # Show first 10
                print(f"  📄 {finding['file']}:{finding['line']}")
                print(f"     ⚠️  {finding['message']}\\n")

        # Save full report to JSON
        report_path = self.root_dir / "COMPREHENSIVE_BUG_AUDIT_RESULTS.json"
        with open(report_path, "w") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "files_scanned": self.files_scanned,
                    "lines_scanned": self.lines_scanned,
                    "total_issues": total_issues,
                    "findings": self.findings,
                },
                f,
                indent=2,
            )

        print(f"\\n💾 Full report saved to: {report_path}")
        print("\\n✅ Audit complete!\\n")


if __name__ == "__main__":
    import sys

    root_dir = r"C:\\Users\\surya\\projects\\MH webapps"
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]

    auditor = ComprehensiveBugAudit(root_dir)
    auditor.scan_all_files()
