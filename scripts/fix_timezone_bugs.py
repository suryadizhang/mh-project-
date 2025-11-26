#!/usr/bin/env python3
"""
Automated Timezone Bug Fix Script
==================================

This script fixes Bug #XX: timezone-naive datetime.now() usage across the codebase.

Problem:
- datetime.now() returns timezone-naive datetime
- Database stores timezone-aware datetime
- Comparison crashes: "can't compare offset-naive and offset-aware datetimes"

Solution:
- Replace: datetime.now()
- With: datetime.now(timezone.utc)
- Add import: from datetime import timezone

Usage:
    python scripts/fix_timezone_bugs.py [--dry-run] [--auto-commit]

Options:
    --dry-run: Show changes without applying them
    --auto-commit: Automatically commit changes to git
"""

import argparse
from pathlib import Path
import re


class TimezoneFixer:
    """Automated timezone bug fixer"""

    def __init__(self, workspace_root: Path, dry_run: bool = False):
        self.workspace_root = workspace_root
        self.backend_src = workspace_root / "apps" / "backend" / "src"
        self.dry_run = dry_run
        self.files_modified = []
        self.lines_modified = 0

    def find_affected_files(self) -> list[Path]:
        """Find all Python files with datetime.now()"""

        print("🔍 Scanning for datetime.now() usage...")

        affected_files = []

        for py_file in self.backend_src.rglob("*.py"):
            # Skip __pycache__ and test files for now
            if "__pycache__" in str(py_file):
                continue

            content = py_file.read_text(encoding="utf-8")

            # Check if file uses datetime.now()
            if re.search(r"\bdatetime\.now\(\)", content):
                affected_files.append(py_file)

        print(f"📊 Found {len(affected_files)} files with datetime.now()")
        return affected_files

    def check_imports(self, content: str) -> dict[str, bool]:
        """Check which datetime imports exist"""

        has_datetime = bool(
            re.search(r"from datetime import.*\bdatetime\b", content)
        )
        has_timezone = bool(
            re.search(r"from datetime import.*\btimezone\b", content)
        )
        has_timedelta = bool(
            re.search(r"from datetime import.*\btimedelta\b", content)
        )
        has_date = bool(re.search(r"from datetime import.*\bdate\b", content))
        has_time = bool(re.search(r"from datetime import.*\btime\b", content))

        return {
            "datetime": has_datetime,
            "timezone": has_timezone,
            "timedelta": has_timedelta,
            "date": has_date,
            "time": has_time,
        }

    def fix_file(self, file_path: Path) -> tuple[bool, int]:
        """Fix datetime.now() in a single file"""

        content = file_path.read_text(encoding="utf-8")
        original_content = content

        # Check current imports
        imports = self.check_imports(content)

        # Fix imports (add timezone if missing)
        if not imports["timezone"]:
            # Find the datetime import line and add timezone
            import_pattern = r"from datetime import ([^\n]+)"

            def add_timezone_to_import(match):
                existing_imports = match.group(1).strip()

                # Don't add if already present
                if "timezone" in existing_imports:
                    return match.group(0)

                # Add timezone to imports
                return f"from datetime import {existing_imports}, timezone"

            content = re.sub(
                import_pattern, add_timezone_to_import, content, count=1
            )

        # Fix datetime.now() → datetime.now(timezone.utc)
        # But preserve datetime.now().astimezone() patterns (already handling timezone)

        # Count occurrences before replacement
        occurrences_before = len(re.findall(r"\bdatetime\.now\(\)", content))

        # Replace datetime.now() with datetime.now(timezone.utc)
        # BUT skip if it's already followed by .astimezone() or already has timezone parameter
        content = re.sub(
            r"\bdatetime\.now\(\)(?!\.astimezone\(\)|datetime\.now\(timezone)",
            "datetime.now(timezone.utc)",
            content,
        )

        # Count changes
        changes_made = len(
            re.findall(r"datetime\.now\(timezone\.utc\)", content)
        ) - len(
            re.findall(r"datetime\.now\(timezone\.utc\)", original_content)
        )

        if content != original_content:
            if not self.dry_run:
                file_path.write_text(content, encoding="utf-8")
                self.files_modified.append(file_path)
                self.lines_modified += changes_made
                print(
                    f"  ✅ Fixed: {file_path.relative_to(self.workspace_root)} ({changes_made} changes)"
                )
            else:
                print(
                    f"  📝 Would fix: {file_path.relative_to(self.workspace_root)} ({changes_made} changes)"
                )
            return True, changes_made
        else:
            return False, 0

    def run(self) -> None:
        """Run the timezone fixer"""

        print("=" * 80)
        print("🕐 TIMEZONE BUG FIXER")
        print("=" * 80)
        print()

        if self.dry_run:
            print("⚠️  DRY RUN MODE - No files will be modified")
            print()

        # Find affected files
        affected_files = self.find_affected_files()

        if not affected_files:
            print("✅ No timezone bugs found!")
            return

        print()
        print("🔧 Fixing files...")
        print()

        total_modified = 0
        total_changes = 0

        for file_path in affected_files:
            modified, changes = self.fix_file(file_path)
            if modified:
                total_modified += 1
                total_changes += changes

        print()
        print("=" * 80)
        print("📊 SUMMARY")
        print("=" * 80)
        print(f"Files scanned: {len(affected_files)}")
        print(f"Files modified: {total_modified}")
        print(f"Total changes: {total_changes}")

        if self.dry_run:
            print()
            print(
                "ℹ️  This was a dry run. Run without --dry-run to apply changes."
            )
        else:
            print()
            print("✅ All timezone bugs fixed!")
            print()
            print("Next steps:")
            print("1. Review changes: git diff")
            print(
                "2. Test critical paths (booking, payment, AI conversations)"
            )
            print(
                "3. Run validation: python scripts/validate_phases_vs_reality.py"
            )
            print(
                "4. Commit changes: git add -A && git commit -m 'fix: timezone bugs (datetime.now → datetime.now(timezone.utc))'"
            )


def main():
    parser = argparse.ArgumentParser(
        description="Fix timezone bugs in codebase"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without applying them",
    )
    parser.add_argument(
        "--auto-commit",
        action="store_true",
        help="Automatically commit changes",
    )

    args = parser.parse_args()

    workspace_root = Path(__file__).parent.parent

    fixer = TimezoneFixer(workspace_root, dry_run=args.dry_run)
    fixer.run()

    # Auto-commit if requested
    if args.auto_commit and not args.dry_run and fixer.files_modified:
        import subprocess

        print()
        print("🚀 Auto-committing changes...")

        subprocess.run(["git", "add", "-A"], check=False, cwd=workspace_root)
        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                f"fix: timezone bugs - replace datetime.now() with datetime.now(timezone.utc)\n\nFixed {len(fixer.files_modified)} files with {fixer.lines_modified} changes",
            ],
            check=False,
            cwd=workspace_root,
        )

        print("✅ Changes committed!")


if __name__ == "__main__":
    main()
