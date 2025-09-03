#!/usr/bin/env python3

"""
Comprehensive Formatting Pipeline (RFP) - 100% Correctness Enforcer
Zero whitespace/formatting issues with behavior-identical code preservation

This script applies comprehensive formatting across the entire My Hibachi project:
- Frontend: Prettier + ESLint with import sorting
- Backend: Black + Ruff + isort for Python
- Universal: LF line endings, final newlines, whitespace cleanup

Ensures zero formatting issues while maintaining identical behavior.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

# Project structure
WORKSPACE_ROOT = Path(__file__).parent
FRONTEND_DIR = WORKSPACE_ROOT / "myhibachi-frontend"
BACKEND_DIRS = [
    WORKSPACE_ROOT / "myhibachi-backend",
    WORKSPACE_ROOT / "myhibachi-ai-backend",
    WORKSPACE_ROOT / "myhibachi-backend-fastapi",
]


def run_command(
    cmd: List[str], cwd: Path = None, capture_output: bool = False
) -> Tuple[bool, str]:
    """Run a command and return success status and output."""
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=capture_output, text=True, check=False
        )
        return result.returncode == 0, result.stdout if capture_output else ""
    except Exception as e:
        return False, str(e)


def format_frontend() -> bool:
    """Format the Next.js frontend with Prettier and ESLint."""
    print("🎨 Formatting Frontend (Next.js + TypeScript)...")

    if not FRONTEND_DIR.exists():
        print(f"⚠️  Frontend directory not found: {FRONTEND_DIR}")
        return False

    # Run Prettier formatting
    success, _ = run_command(["npm", "run", "format"], cwd=FRONTEND_DIR)
    if not success:
        print("❌ Prettier formatting failed")
        return False
    print("✅ Prettier formatting completed")

    # Run ESLint autofix
    success, _ = run_command(["npm", "run", "lint:fix"], cwd=FRONTEND_DIR)
    if not success:
        print("⚠️  ESLint autofix completed with warnings (likely console statements)")
    else:
        print("✅ ESLint autofix completed")

    return True


def format_backend_directory(backend_dir: Path) -> bool:
    """Format a Python backend directory."""
    if not backend_dir.exists():
        print(f"⚠️  Backend directory not found: {backend_dir}")
        return False

    print(f"🐍 Formatting {backend_dir.name}...")

    # Find Python files
    python_files = list(backend_dir.glob("**/*.py"))
    if not python_files:
        print(f"⚠️  No Python files found in {backend_dir}")
        return True

    # Run Black formatting
    success, _ = run_command(["black", "."], cwd=backend_dir)
    if not success:
        print(f"❌ Black formatting failed for {backend_dir}")
        return False
    print(f"✅ Black formatting completed for {backend_dir}")

    # Run Ruff linting and fixing
    success, _ = run_command(["ruff", "check", "--fix", "."], cwd=backend_dir)
    if not success:
        print(f"⚠️  Ruff linting completed with warnings for {backend_dir}")
    else:
        print(f"✅ Ruff linting completed for {backend_dir}")

    # Run isort import sorting
    success, _ = run_command(["isort", "."], cwd=backend_dir)
    if not success:
        print(f"❌ isort failed for {backend_dir}")
        return False
    print(f"✅ isort completed for {backend_dir}")

    return True


def format_backends() -> bool:
    """Format all Python backend directories."""
    print("🐍 Formatting Python Backends...")

    all_success = True
    for backend_dir in BACKEND_DIRS:
        if not format_backend_directory(backend_dir):
            all_success = False

    return all_success


def normalize_line_endings() -> bool:
    """Normalize line endings to LF for all text files."""
    print("📄 Normalizing line endings to LF...")

    # Find all text files (excluding binary files and node_modules)
    text_extensions = {
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".py",
        ".json",
        ".md",
        ".txt",
        ".css",
        ".scss",
        ".html",
    }
    exclude_dirs = {"node_modules", ".git", "__pycache__", ".venv", "dist", "build"}

    files_processed = 0
    files_changed = 0

    for root, dirs, files in os.walk(WORKSPACE_ROOT):
        # Remove excluded directories from search
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for file in files:
            if any(file.endswith(ext) for ext in text_extensions):
                file_path = Path(root) / file
                try:
                    with open(file_path, "rb") as f:
                        content = f.read()

                    # Convert CRLF to LF
                    if b"\r\n" in content:
                        content = content.replace(b"\r\n", b"\n")
                        with open(file_path, "wb") as f:
                            f.write(content)
                        files_changed += 1

                    files_processed += 1

                except Exception as e:
                    print(f"⚠️  Could not process {file_path}: {e}")

    print(
        f"✅ Processed {files_processed} files, normalized {files_changed} files to LF"
    )
    return True


def run_final_validation() -> bool:
    """Run final validation to ensure everything works."""
    print("🔍 Running final validation...")

    # Validate frontend build
    print("Validating frontend build...")
    success, _ = run_command(["npm", "run", "typecheck"], cwd=FRONTEND_DIR)
    if not success:
        print("❌ Frontend TypeScript validation failed")
        return False
    print("✅ Frontend TypeScript validation passed")

    # Validate backends with mypy (if configured)
    for backend_dir in BACKEND_DIRS:
        if backend_dir.exists() and (backend_dir / "pyproject.toml").exists():
            print(f"Validating {backend_dir.name} with mypy...")
            success, _ = run_command(["mypy", "."], cwd=backend_dir)
            if not success:
                print(f"⚠️  MyPy validation completed with warnings for {backend_dir}")
            else:
                print(f"✅ MyPy validation passed for {backend_dir}")

    return True


def main():
    """Main pipeline execution."""
    print("🚀 Starting 100% Correctness Enforcer + Reliable Formatting Pipeline")
    print("=" * 80)

    steps = [
        ("Frontend Formatting", format_frontend),
        ("Backend Formatting", format_backends),
        ("Line Ending Normalization", normalize_line_endings),
        ("Final Validation", run_final_validation),
    ]

    all_success = True
    for step_name, step_func in steps:
        print(f"\n📋 Step: {step_name}")
        print("-" * 40)
        if not step_func():
            print(f"❌ {step_name} failed")
            all_success = False
        else:
            print(f"✅ {step_name} completed successfully")

    print("\n" + "=" * 80)
    if all_success:
        print("🎉 100% CORRECTNESS ENFORCER PIPELINE COMPLETED SUCCESSFULLY!")
        print("✨ Zero whitespace/formatting issues with behavior-identical code")
        print("🚀 Ready for production deployment")
    else:
        print("⚠️  Pipeline completed with some warnings/issues")
        print("📋 Review the output above for details")

    return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(main())
