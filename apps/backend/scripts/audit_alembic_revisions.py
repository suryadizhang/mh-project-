"""
Alembic Migration Audit Script
Analyzes all migration files to find duplicates, missing parents, and orphaned revisions.

Usage:
    cd apps/backend
    python scripts/audit_alembic_revisions.py
"""

import os
import re
from pathlib import Path
from datetime import datetime

def audit_revisions():
    """Main audit function"""
    versions_dir = Path("src/db/migrations/alembic/versions")

    if not versions_dir.exists():
        print(f"❌ ERROR: Directory not found: {versions_dir}")
        return

    revisions = {}  # revision_id -> filename
    revision_metadata = {}  # revision_id -> {file, down_revision, branch_labels, etc}
    duplicates = []
    missing_parents = []

    print(f"\n{'='*70}")
    print(f"🔍 ALEMBIC MIGRATION AUDIT")
    print(f"{'='*70}\n")
    print(f"📂 Scanning: {versions_dir.absolute()}\n")

    # Parse all migration files
    files_scanned = 0
    for file in sorted(versions_dir.glob("*.py")):
        if file.name == "__init__.py" or file.name.startswith("__pycache__"):
            continue

        files_scanned += 1

        try:
            content = file.read_text(encoding='utf-8')
        except Exception as e:
            print(f"⚠️ WARNING: Could not read {file.name}: {e}")
            continue

        # Check for empty files
        if len(content.strip()) == 0:
            print(f"❌ EMPTY FILE: {file.name} (0 bytes)")
            continue

        # Extract revision metadata
        # Support both formats: revision = 'xxx' and revision: str = 'xxx'
        rev_match = re.search(r"^revision(?:\s*:\s*\w+)?\s*=\s*['\"](.+?)['\"]", content, re.MULTILINE)
        down_match = re.search(r"^down_revision(?:\s*:\s*[\w\[\],\s]+)?\s*=\s*(.+?)$", content, re.MULTILINE)
        branch_match = re.search(r"^branch_labels\s*=\s*(.+?)$", content, re.MULTILINE)
        depends_match = re.search(r"^depends_on\s*=\s*(.+?)$", content, re.MULTILINE)

        if not rev_match:
            print(f"⚠️ WARNING: No revision ID found in {file.name}")
            continue

        revision = rev_match.group(1)
        down_revision_raw = down_match.group(1).strip() if down_match else "None"

        # Parse down_revision (can be None, string, or tuple for merges)
        down_revision = None
        if down_revision_raw not in ["None", "none", "null"]:
            # Clean up the string
            down_revision_clean = down_revision_raw.replace("'", "").replace('"', '').replace('(', '').replace(')', '').strip()
            if down_revision_clean:
                down_revision = down_revision_clean

        # Store metadata
        revision_metadata[revision] = {
            'file': file.name,
            'down_revision': down_revision,
            'branch_labels': branch_match.group(1) if branch_match else None,
            'depends_on': depends_match.group(1) if depends_match else None,
        }

        # Check for duplicates
        if revision in revisions:
            duplicates.append({
                'revision': revision,
                'file1': revisions[revision],
                'file2': file.name
            })
        else:
            revisions[revision] = file.name

    # Check for missing parents (second pass - now we have all revisions)
    for revision, metadata in revision_metadata.items():
        down_revision = metadata['down_revision']

        if not down_revision:
            continue

        # Handle merge migrations (multiple parents)
        parent_revisions = [rev.strip() for rev in down_revision.split(',')]

        for parent_rev in parent_revisions:
            if parent_rev and parent_rev not in revisions and parent_rev not in ["None", "none"]:
                missing_parents.append({
                    'child': metadata['file'],
                    'child_revision': revision,
                    'missing_parent': parent_rev
                })

    # Print results
    print(f"{'='*70}")
    print(f"📊 AUDIT RESULTS")
    print(f"{'='*70}\n")
    print(f"✅ Files scanned: {files_scanned}")
    print(f"✅ Valid revisions: {len(revisions)}")
    print(f"❌ Duplicates found: {len(duplicates)}")
    print(f"❌ Missing parents: {len(missing_parents)}\n")

    # Report duplicates
    if duplicates:
        print(f"{'='*70}")
        print(f"🔴 DUPLICATE REVISIONS (CRITICAL)")
        print(f"{'='*70}\n")
        for dup in duplicates:
            print(f"Revision: {dup['revision']}")
            print(f"  File 1: {dup['file1']}")
            print(f"  File 2: {dup['file2']}")
            print(f"  ⚠️ ACTION: Remove one of these files\n")

    # Report missing parents
    if missing_parents:
        print(f"{'='*70}")
        print(f"🔴 MISSING PARENT REVISIONS (CRITICAL)")
        print(f"{'='*70}\n")
        for miss in missing_parents:
            print(f"Child: {miss['child']} (revision: {miss['child_revision']})")
            print(f"  Missing parent: {miss['missing_parent']}")
            print(f"  ⚠️ ACTION: Restore file OR update down_revision in child\n")

    # Find potential heads (no children)
    all_parent_revisions = set()
    for metadata in revision_metadata.values():
        if metadata['down_revision']:
            parent_revs = [rev.strip() for rev in metadata['down_revision'].split(',')]
            all_parent_revisions.update(parent_revs)

    potential_heads = [
        rev for rev in revisions.keys()
        if rev not in all_parent_revisions
    ]

    print(f"{'='*70}")
    print(f"📍 POTENTIAL HEAD REVISIONS")
    print(f"{'='*70}\n")
    if len(potential_heads) == 1:
        print(f"✅ Single head found: {potential_heads[0]}")
        print(f"   File: {revisions[potential_heads[0]]}\n")
    else:
        print(f"⚠️ Multiple heads found: {len(potential_heads)}")
        for head in potential_heads:
            print(f"  - {head} ({revisions[head]})")
        print(f"\n⚠️ ACTION: May need to merge heads\n")

    # Save report
    report_path = Path("ALEMBIC_AUDIT_REPORT.txt")
    with open(report_path, 'w') as f:
        f.write(f"Alembic Migration Audit Report\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'='*70}\n\n")

        f.write(f"SUMMARY:\n")
        f.write(f"  Files scanned: {files_scanned}\n")
        f.write(f"  Valid revisions: {len(revisions)}\n")
        f.write(f"  Duplicates: {len(duplicates)}\n")
        f.write(f"  Missing parents: {len(missing_parents)}\n")
        f.write(f"  Potential heads: {len(potential_heads)}\n\n")

        if duplicates:
            f.write(f"DUPLICATE REVISIONS:\n")
            for dup in duplicates:
                f.write(f"  {dup['revision']}: {dup['file1']} AND {dup['file2']}\n")
            f.write(f"\n")

        if missing_parents:
            f.write(f"MISSING PARENT REVISIONS:\n")
            for miss in missing_parents:
                f.write(f"  {miss['child']} references {miss['missing_parent']} (NOT FOUND)\n")
            f.write(f"\n")

        f.write(f"ALL REVISIONS:\n")
        for rev, filename in sorted(revisions.items(), key=lambda x: x[1]):
            metadata = revision_metadata[rev]
            f.write(f"  {filename}\n")
            f.write(f"    revision: {rev}\n")
            f.write(f"    down_revision: {metadata['down_revision']}\n")
            if metadata['branch_labels']:
                f.write(f"    branch_labels: {metadata['branch_labels']}\n")
            f.write(f"\n")

    print(f"{'='*70}")
    print(f"💾 Report saved to: {report_path.absolute()}")
    print(f"{'='*70}\n")

    # Summary recommendations
    print(f"🎯 NEXT STEPS:\n")
    if duplicates:
        print(f"1. Fix {len(duplicates)} duplicate revision(s) - See PHASE_0_FOUNDATION.md Step 2")
    if missing_parents:
        print(f"2. Fix {len(missing_parents)} missing parent(s) - See PHASE_0_FOUNDATION.md Step 3")
    if len(potential_heads) > 1:
        print(f"3. Merge {len(potential_heads)} head(s) - Run: alembic merge heads")

    if not duplicates and not missing_parents and len(potential_heads) == 1:
        print(f"✅ No critical issues found! Proceed to Step 4: Validate Chain")
    print()

if __name__ == "__main__":
    audit_revisions()
