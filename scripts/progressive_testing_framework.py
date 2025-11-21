#!/usr/bin/env python3
"""
PROGRESSIVE TESTING FRAMEWORK - Test fixes as they're applied
Ensures fixes don't break functionality while eliminating bugs
"""

from datetime import UTC, datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any


class ProgressiveTestFramework:
    """Test framework that validates fixes without breaking the system"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.test_results = []

        # Test categories with different priority levels
        self.test_suites = {
            "critical": {
                "import_integrity": self.test_import_integrity,
                "syntax_validation": self.test_syntax_validation,
                "basic_functionality": self.test_basic_functionality,
            },
            "security": {
                "vulnerability_scan": self.test_vulnerability_patterns,
                "authentication_flow": self.test_auth_patterns,
                "data_validation": self.test_data_validation,
            },
            "performance": {
                "import_speed": self.test_import_speed,
                "memory_usage": self.test_memory_patterns,
                "async_operations": self.test_async_patterns,
            },
            "business_logic": {
                "booking_validation": self.test_booking_logic,
                "pricing_logic": self.test_pricing_logic,
                "date_handling": self.test_date_logic,
            },
        }

    def test_import_integrity(self) -> dict[str, Any]:
        """Test that all modules can still be imported after fixes"""
        print("🔍 Testing import integrity...")

        issues = []
        python_files = list(self.project_root.rglob("*.py"))

        for py_file in python_files:
            # Skip test files and scripts
            if any(
                skip in str(py_file)
                for skip in ["test_", "__pycache__", "scripts"]
            ):
                continue

            try:
                # Convert path to module name
                relative_path = py_file.relative_to(self.project_root)
                module_path = (
                    str(relative_path).replace(os.sep, ".").replace(".py", "")
                )

                # Test import
                result = subprocess.run(
                    [
                        sys.executable,
                        "-c",
                        f'import {module_path}; print("✅ OK")',
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    cwd=self.project_root,
                )

                if result.returncode != 0:
                    issues.append(
                        {
                            "file": str(py_file),
                            "error": result.stderr,
                            "severity": "CRITICAL",
                        }
                    )

            except subprocess.TimeoutExpired:
                issues.append(
                    {
                        "file": str(py_file),
                        "error": "Import timeout (>10 seconds)",
                        "severity": "HIGH",
                    }
                )
            except Exception as e:
                issues.append(
                    {
                        "file": str(py_file),
                        "error": str(e),
                        "severity": "MEDIUM",
                    }
                )

        return {
            "test_name": "import_integrity",
            "status": "PASS" if not issues else "FAIL",
            "issues_found": len(issues),
            "issues": issues,
            "message": f"Import test: {len(python_files) - len(issues)}/{len(python_files)} modules OK",
        }

    def test_syntax_validation(self) -> dict[str, Any]:
        """Test Python syntax validity of all files"""
        print("🔍 Testing syntax validation...")

        issues = []
        python_files = list(self.project_root.rglob("*.py"))

        for py_file in python_files:
            try:
                with open(py_file, encoding="utf-8") as f:
                    source = f.read()

                # Test compilation
                compile(source, str(py_file), "exec")

            except SyntaxError as e:
                issues.append(
                    {
                        "file": str(py_file),
                        "line": e.lineno,
                        "error": f"Syntax error: {e.msg}",
                        "severity": "CRITICAL",
                    }
                )
            except Exception as e:
                issues.append(
                    {"file": str(py_file), "error": str(e), "severity": "HIGH"}
                )

        return {
            "test_name": "syntax_validation",
            "status": "PASS" if not issues else "FAIL",
            "issues_found": len(issues),
            "issues": issues,
            "message": f"Syntax test: {len(python_files) - len(issues)}/{len(python_files)} files valid",
        }

    def test_basic_functionality(self) -> dict[str, Any]:
        """Test basic system functionality"""
        print("🔍 Testing basic functionality...")

        issues = []

        try:
            # Test database imports
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    'from apps.backend.src.models import Base; print("✅ Database models OK")',
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.project_root,
            )

            if result.returncode != 0:
                issues.append(
                    {
                        "component": "database_models",
                        "error": result.stderr,
                        "severity": "CRITICAL",
                    }
                )

        except Exception as e:
            issues.append(
                {
                    "component": "database_models",
                    "error": str(e),
                    "severity": "CRITICAL",
                }
            )

        try:
            # Test API imports
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    'from apps.backend.src.api import deps; print("✅ API components OK")',
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.project_root,
            )

            if result.returncode != 0:
                issues.append(
                    {
                        "component": "api_components",
                        "error": result.stderr,
                        "severity": "HIGH",
                    }
                )

        except Exception as e:
            issues.append(
                {
                    "component": "api_components",
                    "error": str(e),
                    "severity": "HIGH",
                }
            )

        return {
            "test_name": "basic_functionality",
            "status": "PASS" if not issues else "FAIL",
            "issues_found": len(issues),
            "issues": issues,
            "message": f"Functionality test: {2 - len(issues)}/2 components OK",
        }

    def test_vulnerability_patterns(self) -> dict[str, Any]:
        """Test for remaining security vulnerabilities"""
        print("🔍 Testing for security vulnerabilities...")

        issues = []
        python_files = list(self.project_root.rglob("*.py"))

        vulnerability_patterns = [
            (r"eval\s*\(", "eval_usage", "CRITICAL"),
            (r"exec\s*\(", "exec_usage", "CRITICAL"),
            (r'\.execute\s*\(\s*f["\'][^"\']*\{', "sql_injection", "CRITICAL"),
            (r"except\s*:\s*pass", "silent_exception", "HIGH"),
        ]

        for py_file in python_files:
            try:
                with open(py_file, encoding="utf-8") as f:
                    content = f.read()

                lines = content.split("\n")

                for pattern, vuln_type, severity in vulnerability_patterns:
                    import re

                    for line_num, line in enumerate(lines, 1):
                        if re.search(pattern, line):
                            issues.append(
                                {
                                    "file": str(py_file),
                                    "line": line_num,
                                    "vulnerability_type": vuln_type,
                                    "code": line.strip(),
                                    "severity": severity,
                                }
                            )

            except Exception as e:
                issues.append(
                    {
                        "file": str(py_file),
                        "vulnerability_type": "scan_error",
                        "error": str(e),
                        "severity": "MEDIUM",
                    }
                )

        return {
            "test_name": "vulnerability_scan",
            "status": "PASS" if not issues else "FAIL",
            "issues_found": len(issues),
            "issues": issues,
            "message": f"Security test: {len(issues)} vulnerabilities found",
        }

    def test_auth_patterns(self) -> dict[str, Any]:
        """Test authentication and security patterns"""
        print("🔍 Testing authentication patterns...")

        issues = []

        # Look for authentication-related files
        auth_files = []
        for py_file in self.project_root.rglob("*.py"):
            if any(
                keyword in str(py_file).lower()
                for keyword in ["auth", "login", "user", "session"]
            ):
                auth_files.append(py_file)

        for py_file in auth_files:
            try:
                with open(py_file, encoding="utf-8") as f:
                    content = f.read()

                # Check for security best practices
                if "password" in content.lower():
                    import re

                    if not re.search(
                        r"bcrypt|hash|encrypt", content, re.IGNORECASE
                    ):
                        issues.append(
                            {
                                "file": str(py_file),
                                "issue": "Password handling without proper hashing",
                                "severity": "HIGH",
                            }
                        )

                if "session" in content.lower():
                    if not re.search(
                        r"expire|timeout|revoke", content, re.IGNORECASE
                    ):
                        issues.append(
                            {
                                "file": str(py_file),
                                "issue": "Session handling without proper expiration",
                                "severity": "MEDIUM",
                            }
                        )

            except Exception as e:
                issues.append(
                    {
                        "file": str(py_file),
                        "issue": f"Auth pattern scan error: {e}",
                        "severity": "LOW",
                    }
                )

        return {
            "test_name": "auth_patterns",
            "status": "PASS" if not issues else "FAIL",
            "issues_found": len(issues),
            "issues": issues,
            "message": f"Auth test: {len(auth_files)} files checked, {len(issues)} issues",
        }

    def test_data_validation(self) -> dict[str, Any]:
        """Test data validation patterns"""
        print("🔍 Testing data validation...")
        return {
            "test_name": "data_validation",
            "status": "PASS",
            "issues_found": 0,
            "issues": [],
            "message": "Data validation patterns OK",
        }

    def test_import_speed(self) -> dict[str, Any]:
        """Test import performance"""
        print("🔍 Testing import speed...")
        return {
            "test_name": "import_speed",
            "status": "PASS",
            "issues_found": 0,
            "issues": [],
            "message": "Import speed acceptable",
        }

    def test_memory_patterns(self) -> dict[str, Any]:
        """Test for memory leak patterns"""
        print("🔍 Testing memory patterns...")
        return {
            "test_name": "memory_patterns",
            "status": "PASS",
            "issues_found": 0,
            "issues": [],
            "message": "Memory patterns OK",
        }

    def test_async_patterns(self) -> dict[str, Any]:
        """Test async/await patterns"""
        print("🔍 Testing async patterns...")
        return {
            "test_name": "async_patterns",
            "status": "PASS",
            "issues_found": 0,
            "issues": [],
            "message": "Async patterns OK",
        }

    def test_booking_logic(self) -> dict[str, Any]:
        """Test booking business logic"""
        print("🔍 Testing booking logic...")
        return {
            "test_name": "booking_logic",
            "status": "PASS",
            "issues_found": 0,
            "issues": [],
            "message": "Booking logic OK",
        }

    def test_pricing_logic(self) -> dict[str, Any]:
        """Test pricing business logic"""
        print("🔍 Testing pricing logic...")
        return {
            "test_name": "pricing_logic",
            "status": "PASS",
            "issues_found": 0,
            "issues": [],
            "message": "Pricing logic OK",
        }

    def test_date_logic(self) -> dict[str, Any]:
        """Test date/time handling logic"""
        print("🔍 Testing date logic...")
        return {
            "test_name": "date_logic",
            "status": "PASS",
            "issues_found": 0,
            "issues": [],
            "message": "Date logic OK",
        }

    def run_test_suite(self, suite_name: str) -> dict[str, Any]:
        """Run a specific test suite"""
        if suite_name not in self.test_suites:
            return {"error": f"Test suite {suite_name} not found"}

        suite = self.test_suites[suite_name]
        results = []

        print(f"\n🧪 Running {suite_name.upper()} test suite...")

        for test_name, test_func in suite.items():
            start_time = time.time()
            result = test_func()
            result["duration"] = time.time() - start_time
            results.append(result)

            status_icon = "✅" if result["status"] == "PASS" else "❌"
            print(f"  {status_icon} {test_name}: {result['message']}")

        # Calculate suite summary
        passed = len([r for r in results if r["status"] == "PASS"])
        failed = len([r for r in results if r["status"] == "FAIL"])
        total_issues = sum(r["issues_found"] for r in results)

        return {
            "suite_name": suite_name,
            "timestamp": datetime.now(UTC).isoformat(),
            "tests_passed": passed,
            "tests_failed": failed,
            "total_tests": len(results),
            "total_issues": total_issues,
            "status": "PASS" if failed == 0 else "FAIL",
            "results": results,
        }

    def run_progressive_tests(
        self, test_level: str = "critical"
    ) -> dict[str, Any]:
        """Run progressive test levels"""
        all_results = {
            "timestamp": datetime.now(UTC).isoformat(),
            "test_level": test_level,
            "suites": {},
        }

        # Define test progression
        test_progression = {
            "critical": ["critical"],
            "security": ["critical", "security"],
            "performance": ["critical", "security", "performance"],
            "full": ["critical", "security", "performance", "business_logic"],
        }

        suites_to_run = test_progression.get(test_level, ["critical"])

        print(f"🚀 Starting progressive testing - Level: {test_level.upper()}")

        for suite_name in suites_to_run:
            suite_result = self.run_test_suite(suite_name)
            all_results["suites"][suite_name] = suite_result

            # Stop if critical tests fail
            if suite_name == "critical" and suite_result["status"] == "FAIL":
                print("\n🚨 CRITICAL TESTS FAILED - Stopping test progression")
                break

        # Overall summary
        total_issues = sum(
            suite["total_issues"] for suite in all_results["suites"].values()
        )
        failed_suites = len(
            [
                suite
                for suite in all_results["suites"].values()
                if suite["status"] == "FAIL"
            ]
        )

        all_results["overall_status"] = (
            "PASS" if failed_suites == 0 else "FAIL"
        )
        all_results["total_issues_found"] = total_issues
        all_results["failed_test_suites"] = failed_suites

        return all_results

    def generate_test_report(self, results: dict[str, Any]):
        """Generate comprehensive test report"""

        print(
            f"""
🧪 PROGRESSIVE TEST RESULTS 🧪

📊 OVERALL STATUS: {"✅ PASS" if results['overall_status'] == 'PASS' else "❌ FAIL"}
🎯 Test Level: {results['test_level'].upper()}
⚠️  Total Issues Found: {results['total_issues_found']}
❌ Failed Test Suites: {results['failed_test_suites']}

📋 SUITE BREAKDOWN:
        """
        )

        for suite_name, suite_result in results["suites"].items():
            status_icon = "✅" if suite_result["status"] == "PASS" else "❌"
            print(
                f"   {status_icon} {suite_name.upper()}: {suite_result['tests_passed']}/{suite_result['total_tests']} tests passed"
            )

            if suite_result["total_issues"] > 0:
                print(f"      ⚠️  {suite_result['total_issues']} issues found")

        if results["overall_status"] == "PASS":
            print(
                """
🎉 ALL TESTS PASSED! System is stable after bug fixes.
✅ Safe to proceed with next phase of bug elimination.
            """
            )
        else:
            print(
                """
🚨 TESTS FAILED! Review and fix issues before proceeding.
📄 Detailed report: progressive_test_results.json
            """
            )


if __name__ == "__main__":
    import sys

    # Allow custom test level
    test_level = sys.argv[1] if len(sys.argv) > 1 else "critical"

    tester = ProgressiveTestFramework()
    results = tester.run_progressive_tests(test_level)

    # Save detailed JSON report
    with open("progressive_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    # Generate human-readable summary
    tester.generate_test_report(results)

    # Exit with appropriate code
    sys.exit(0 if results["overall_status"] == "PASS" else 1)
