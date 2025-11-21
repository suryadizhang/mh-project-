#!/usr/bin/env python3
"""
🚨 MY HIBACHI BUG ELIMINATION LAUNCHER 🚨

ONE-CLICK solution to start fixing critical bugs RIGHT NOW!
No external dependencies required - pure Python implementation
"""

from pathlib import Path
import subprocess
import sys


def main():
    print(
        """
🚨 MY HIBACHI CRITICAL BUG ELIMINATION 🚨

This will:
✅ Scan for critical security vulnerabilities  
✅ Apply automated fixes for eval(), SQL injection, timezone issues
✅ Test system stability after fixes
✅ Create backups before any changes
✅ Rollback if anything breaks

Choose your action:
    """
    )

    print("1. 🔍 EMERGENCY SCAN ONLY (find critical bugs)")
    print("2. 🛠️ FULL ELIMINATION PROCESS (scan + fix + test)")
    print("3. 🧪 TEST SYSTEM ONLY (verify current state)")
    print("4. ❌ EXIT")

    while True:
        try:
            choice = input("\n👉 Enter your choice (1-4): ").strip()

            if choice == "1":
                run_emergency_scan()
                break
            elif choice == "2":
                run_full_elimination()
                break
            elif choice == "3":
                run_system_test()
                break
            elif choice == "4":
                print("👋 Exiting - no changes made")
                sys.exit(0)
            else:
                print("❌ Invalid choice. Please enter 1, 2, 3, or 4")

        except KeyboardInterrupt:
            print("\n👋 Cancelled by user")
            sys.exit(0)


def run_emergency_scan():
    """Run immediate bug scan without making changes"""
    print("\n🔍 Running emergency bug scan...")

    script_path = Path("scripts/immediate_bug_scan.py")
    if not script_path.exists():
        print(
            "❌ Scanner script not found. Please run this from the project root directory."
        )
        return

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            check=False,
            capture_output=False,
            text=True,
        )

        if result.returncode == 0:
            print("\n✅ Emergency scan completed successfully!")
        else:
            print(f"\n🚨 Critical bugs found! Exit code: {result.returncode}")
            print("👉 Run option 2 to automatically fix these issues")

    except Exception as e:
        print(f"❌ Failed to run emergency scan: {e}")


def run_full_elimination():
    """Run complete bug elimination process"""
    print("\n🛠️ Starting full bug elimination process...")
    print("⚠️  This will modify your code files (with backups)")

    confirm = input("👉 Continue? (yes/no): ").strip().lower()
    if confirm not in ["yes", "y"]:
        print("👋 Cancelled - no changes made")
        return

    script_path = Path("scripts/bug_elimination_orchestrator.py")
    if not script_path.exists():
        print(
            "❌ Orchestrator script not found. Please run this from the project root directory."
        )
        return

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            check=False,
            capture_output=False,
            text=True,
        )

        if result.returncode == 0:
            print("\n🎉 Bug elimination process completed successfully!")
            print("📋 Check the results directory for detailed reports")
        else:
            print(
                f"\n🚨 Bug elimination process failed! Exit code: {result.returncode}"
            )
            print("📋 Check execution log for details")

    except Exception as e:
        print(f"❌ Failed to run bug elimination process: {e}")


def run_system_test():
    """Run system testing to verify current state"""
    print("\n🧪 Running system tests...")

    script_path = Path("scripts/progressive_testing_framework.py")
    if not script_path.exists():
        print(
            "❌ Testing script not found. Please run this from the project root directory."
        )
        return

    try:
        result = subprocess.run(
            [sys.executable, str(script_path), "critical"],
            check=False,
            capture_output=False,
            text=True,
        )

        if result.returncode == 0:
            print("\n✅ System tests passed!")
        else:
            print(f"\n🚨 System tests failed! Exit code: {result.returncode}")
            print("👉 Run option 2 to fix identified issues")

    except Exception as e:
        print(f"❌ Failed to run system tests: {e}")


if __name__ == "__main__":
    main()
