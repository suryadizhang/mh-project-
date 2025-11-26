"""Quick check - print all revisions"""
import re
from pathlib import Path

versions_dir = Path("src/db/migrations/alembic/versions")
revisions = {}

for file in sorted(versions_dir.glob("*.py")):
    if file.name.startswith("__"):
        continue

    try:
        content = file.read_text(encoding='utf-8')
    except:
        continue

    rev_match = re.search(r"^revision(?:\s*:\s*\w+)?\s*=\s*['\"](.+?)['\"]", content, re.MULTILINE)

    if rev_match:
        revisions[rev_match.group(1)] = file.name

# Check specific ones
check_list = [
    "000_create_base_users",
    "008_add_user_roles",
    "0e81266c9503",
    "a1b2c3d4e5f6",
    "e636a2d56d82",
    "a7b8c9d0e1f2",
    "009_payment_notifications"
]

print("Checking revisions:")
for rev in check_list:
    if rev in revisions:
        print(f"✅ {rev} -> {revisions[rev]}")
    else:
        print(f"❌ {rev} NOT FOUND")

print(f"\nTotal revisions: {len(revisions)}")
