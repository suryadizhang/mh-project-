#!/usr/bin/env python3
"""
IMMEDIATE BUG SCANNER - Start bug elimination RIGHT NOW
Can run without any external tools - pure Python analysis
"""

from datetime import UTC, datetime
import json
from pathlib import Path
import re
import sys
from typing import Any


class ImmediateBugScanner:
    """Emergency bug scanner - finds critical issues without external dependencies"""

    def __init__(self, root_dir: str = "apps"):
        self.root_dir = Path(root_dir)
        self.critical_bugs = []
        self.high_bugs = []
        self.medium_bugs = []

        # CRITICAL: Production-breaking patterns (based on our A-H audit findings)
        self.critical_patterns = {
            "eval_execution": [
                r"eval\s*\(",
                r"exec\s*\(",
            ],
            "sql_injection": [
                r'\.execute\s*\(\s*f["\'][^"\']*\{[^}]*\}',
                r'\.filter\s*\(\s*.*\s*==\s*f["\'][^"\']*\{[^}]*\}',
                r'\.where\s*\(\s*.*text\s*\(\s*f["\']',
            ],
            "silent_exceptions": [
                r"except\s*:\s*(?:pass|return|continue)",
                r"except\s+Exception\s*:\s*(?:pass|return\s+(?:False|None|\[\]|\{\}))",
            ],
            "timezone_naive": [
                r"datetime\.now\s*\(\s*\)",
                r"datetime\.utcnow\s*\(\s*\)",
                r"default\s*=\s*datetime\.utcnow",
            ],
            "race_conditions": [
                r"(?<!async\s)def\s+.*(?:add|update|delete).*:.*(?!async\s).*(?:commit|execute)",
                r"global\s+\w+.*=",
            ],
        }

        # HIGH: Major functionality issues
        self.high_patterns = {
            "missing_await": [
                r"async\s+def\s+[^:]+:(?:[^}]|{[^}]*})*?(?!await)",
            ],
            "variable_shadowing": [
                r"(\w+)\s*=.*\.scalar_one_or_none\(\).*\1\s*=",
                r"class\s+(\w+).*\1\s*=",
            ],
            "blocking_in_async": [
                r"async\s+def.*time\.sleep\s*\(",
                r"async\s+def.*requests\.",
            ],
            "missing_validation": [
                r"def\s+.*(?:create|update).*amount.*:(?!.*amount.*>)",
                r"def\s+.*booking.*:(?!.*guest.*>)",
            ],
        }

    def scan_file(self, file_path: Path) -> list[dict[str, Any]]:
        """Scan single Python file for critical bugs"""
        bugs_found = []

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            lines = content.split("\n")

            # Check critical patterns
            for category, patterns in self.critical_patterns.items():
                for pattern in patterns:
                    for line_num, line in enumerate(lines, 1):
                        if re.search(pattern, line, re.IGNORECASE):
                            bugs_found.append(
                                {
                                    "file": str(file_path),
                                    "line": line_num,
                                    "category": category,
                                    "severity": "CRITICAL",
                                    "code": line.strip(),
                                    "pattern": pattern,
                                    "fix_urgency": "IMMEDIATE",
                                    "description": self._get_critical_description(
                                        category
                                    ),
                                }
                            )

            # Check high patterns
            for category, patterns in self.high_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(
                        pattern, content, re.MULTILINE | re.DOTALL
                    )
                    for match in matches:
                        line_num = content[: match.start()].count("\n") + 1
                        bugs_found.append(
                            {
                                "file": str(file_path),
                                "line": line_num,
                                "category": category,
                                "severity": "HIGH",
                                "code": match.group()[:100],
                                "pattern": pattern,
                                "fix_urgency": "24_HOURS",
                                "description": self._get_high_description(
                                    category
                                ),
                            }
                        )

        except Exception as e:
            bugs_found.append(
                {
                    "file": str(file_path),
                    "line": 0,
                    "category": "scan_error",
                    "severity": "ERROR",
                    "code": "",
                    "pattern": "file_error",
                    "fix_urgency": "INVESTIGATE",
                    "description": f"Failed to scan file: {e}",
                }
            )

        return bugs_found

    def _get_critical_description(self, category: str) -> str:
        """Get description for critical bugs"""
        descriptions = {
            "eval_execution": "🚨 CRITICAL: eval() enables arbitrary code execution - SECURITY BREACH",
            "sql_injection": "🚨 CRITICAL: SQL injection vulnerability via f-string - DATABASE BREACH",
            "silent_exceptions": "🚨 CRITICAL: Silent exception hiding production failures",
            "timezone_naive": "🚨 CRITICAL: Timezone-naive datetime causing data corruption",
            "race_conditions": "🚨 CRITICAL: Race condition causing data inconsistency",
        }
        return descriptions.get(category, "Critical issue found")

    def _get_high_description(self, category: str) -> str:
        """Get description for high-impact bugs"""
        descriptions = {
            "missing_await": "⚠️ HIGH: Async function missing await - blocking event loop",
            "variable_shadowing": "⚠️ HIGH: Variable shadowing causing reference confusion",
            "blocking_in_async": "⚠️ HIGH: Blocking operation in async context",
            "missing_validation": "⚠️ HIGH: Missing business logic validation",
        }
        return descriptions.get(category, "High impact issue found")

    def scan_all(self) -> dict[str, Any]:
        """Scan entire codebase and categorize results"""
        print(f"🔍 Starting emergency bug scan in: {self.root_dir}")

        if not self.root_dir.exists():
            print(f"❌ Directory not found: {self.root_dir}")
            return {}

        python_files = list(self.root_dir.rglob("*.py"))
        print(f"📁 Found {len(python_files)} Python files")

        all_bugs = []

        for i, file_path in enumerate(python_files):
            if i % 50 == 0:
                print(f"📊 Progress: {i}/{len(python_files)} files scanned")

            file_bugs = self.scan_file(file_path)
            all_bugs.extend(file_bugs)

        # Categorize by severity
        critical = [b for b in all_bugs if b["severity"] == "CRITICAL"]
        high = [b for b in all_bugs if b["severity"] == "HIGH"]
        medium = [b for b in all_bugs if b["severity"] == "MEDIUM"]
        errors = [b for b in all_bugs if b["severity"] == "ERROR"]

        # Generate immediate action plan
        immediate_fixes = [
            b for b in critical if b["fix_urgency"] == "IMMEDIATE"
        ]
        urgent_fixes = [b for b in all_bugs if b["fix_urgency"] == "24_HOURS"]

        results = {
            "scan_timestamp": datetime.now(UTC).isoformat(),
            "files_scanned": len(python_files),
            "total_bugs": len(all_bugs),
            "summary": {
                "critical": len(critical),
                "high": len(high),
                "medium": len(medium),
                "errors": len(errors),
            },
            "immediate_action_required": len(immediate_fixes),
            "urgent_24h_fixes": len(urgent_fixes),
            "bugs": {
                "critical": critical,
                "high": high,
                "medium": medium,
                "errors": errors,
            },
            "action_plan": {
                "immediate": immediate_fixes,
                "urgent_24h": urgent_fixes,
            },
        }

        return results

    def generate_report(self, results: dict[str, Any]):
        """Generate human-readable emergency report"""

        print(
            f"""
🚨 EMERGENCY BUG SCAN COMPLETE 🚨

📊 SCAN RESULTS:
   Files Scanned: {results['files_scanned']:,}
   Total Bugs: {results['total_bugs']:,}
   
🔥 SEVERITY BREAKDOWN:
   🚨 CRITICAL: {results['summary']['critical']:,} (PRODUCTION BREAKING)
   ⚠️  HIGH: {results['summary']['high']:,} (MAJOR FUNCTIONALITY)
   ⚡ MEDIUM: {results['summary']['medium']:,} (FUNCTIONAL ISSUES)
   ❌ ERRORS: {results['summary']['errors']:,} (SCAN ISSUES)

⏰ IMMEDIATE ACTION REQUIRED:
   🆘 Fix RIGHT NOW: {results['immediate_action_required']} critical bugs
   ⏰ Fix in 24h: {results['urgent_24h_fixes']} urgent bugs
   
📋 TOP CRITICAL ISSUES:
        """
        )

        # Show top 5 critical issues
        for i, bug in enumerate(results["bugs"]["critical"][:5], 1):
            print(
                f"""   {i}. {bug['category']} in {bug['file']}:{bug['line']}
      📝 {bug['description']}
      💻 Code: {bug['code'][:80]}...
      """
            )

        print(
            """
📄 DETAILED REPORT: emergency_bug_report.json
🎯 NEXT STEPS: Run immediate fix scripts for critical issues
        """
        )


if __name__ == "__main__":
    scanner = ImmediateBugScanner()
    results = scanner.scan_all()

    # Save detailed JSON report
    with open("emergency_bug_report.json", "w") as f:
        json.dump(results, f, indent=2)

    # Generate human-readable summary
    scanner.generate_report(results)

    # Exit with error code if critical bugs found
    if results["summary"]["critical"] > 0:
        print("🚨 CRITICAL BUGS FOUND - SYSTEM NEEDS IMMEDIATE ATTENTION")
        sys.exit(1)
    else:
        print("✅ No critical bugs found in emergency scan")
        sys.exit(0)
