"""Analyze Alembic migration chain to find issues"""

import re
from pathlib import Path
from collections import defaultdict

versions_dir = Path(__file__).parent / "src/db/migrations/alembic/versions"

migrations = []
revision_map = {}
duplicates = defaultdict(list)

# Parse all migration files
for file in versions_dir.glob("*.py"):
    if file.stem == "__pycache__":
        continue

    content = file.read_text(encoding="utf-8")

    # Extract revision ID
    revision_match = re.search(r"revision\s*=\s*['\"]([^'\"]+)['\"]", content)
    down_revision_match = re.search(
        r"down_revision\s*=\s*['\"]([^'\"]+)['\"]", content
    )
    branch_labels_match = re.search(r"branch_labels\s*=\s*(.+)", content)

    if revision_match:
        revision = revision_match.group(1)
        down_revision = (
            down_revision_match.group(1) if down_revision_match else None
        )

        migration_info = {
            "file": file.name,
            "revision": revision,
            "down_revision": down_revision,
            "path": str(file),
        }

        migrations.append(migration_info)

        # Track duplicates
        if revision in revision_map:
            duplicates[revision].append(file.name)
        else:
            revision_map[revision] = migration_info

        # Also track if this revision is referenced
        if down_revision:
            duplicates[revision].append(file.name)

print("=" * 80)
print("ALEMBIC MIGRATION ANALYSIS")
print("=" * 80)

print(f"\nTotal migration files: {len(migrations)}")
print(f"Unique revisions: {len(revision_map)}")

# Find duplicates
print("\n" + "=" * 80)
print("DUPLICATE REVISION IDS")
print("=" * 80)

actual_duplicates = {k: v for k, v in duplicates.items() if len(v) > 1}
if actual_duplicates:
    for rev_id, files in actual_duplicates.items():
        print(f"\n❌ Revision '{rev_id}' appears in:")
        for f in files:
            print(f"   - {f}")
else:
    print("✅ No duplicate revision IDs found")

# Find broken references
print("\n" + "=" * 80)
print("BROKEN DOWN_REVISION REFERENCES")
print("=" * 80)

broken_refs = []
for mig in migrations:
    if mig["down_revision"] and mig["down_revision"] != "None":
        if mig["down_revision"] not in revision_map:
            broken_refs.append(mig)
            print(f"\n❌ {mig['file']}")
            print(f"   References: {mig['down_revision']} (NOT FOUND)")

if not broken_refs:
    print("✅ All down_revision references are valid")

# Find merge migrations
print("\n" + "=" * 80)
print("MERGE MIGRATIONS")
print("=" * 80)

merge_migrations = [m for m in migrations if "merge" in m["file"].lower()]
for mig in merge_migrations:
    print(f"\n📋 {mig['file']}")
    print(f"   Revision: {mig['revision']}")
    print(f"   Down: {mig['down_revision']}")

# Find heads (migrations with no children)
print("\n" + "=" * 80)
print("MIGRATION HEADS (No children pointing to them)")
print("=" * 80)

children_count = defaultdict(int)
for mig in migrations:
    if mig["down_revision"] and mig["down_revision"] != "None":
        children_count[mig["down_revision"]] += 1

heads = [m for m in migrations if children_count[m["revision"]] == 0]
print(f"\nFound {len(heads)} head(s):")
for head in heads:
    print(f"\n🔝 {head['file']}")
    print(f"   Revision: {head['revision']}")

# Trace migration chain from each head
print("\n" + "=" * 80)
print("MIGRATION CHAINS")
print("=" * 80)

for head in heads:
    print(f"\n📜 Chain from {head['file']}:")
    current = head
    chain = [current["revision"]]
    seen = set()

    while current["down_revision"] and current["down_revision"] != "None":
        if current["down_revision"] in seen:
            print("   ⚠️ CIRCULAR REFERENCE DETECTED!")
            break
        seen.add(current["down_revision"])

        if current["down_revision"] in revision_map:
            current = revision_map[current["down_revision"]]
            chain.append(current["revision"])
        else:
            print(f"   ❌ BROKEN: Missing revision {current['down_revision']}")
            break

    print(f"   Length: {len(chain)} migrations")
    if len(chain) <= 10:
        for rev in chain:
            file = revision_map.get(rev, {}).get("file", "UNKNOWN")
            print(f"   → {rev[:12]}... ({file})")

print("\n" + "=" * 80)
print("RECOMMENDATIONS")
print("=" * 80)
print(
    """
1. Fix duplicate revision IDs
2. Fix broken down_revision references  
3. Determine the correct HEAD migration
4. Update alembic_version table with correct HEAD
5. Test migrations on clean database
"""
)
