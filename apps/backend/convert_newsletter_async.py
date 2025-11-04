"""
Convert newsletter.py from sync SQLAlchemy to async
This script automates the conversion of all database operations
"""

import re
from pathlib import Path

# Path to newsletter.py
file_path = Path(
    "c:/Users/surya/projects/MH webapps/apps/backend/src/api/app/routers/newsletter.py"
)

# Read the file
content = file_path.read_text(encoding="utf-8")

# Replacements
replacements = [
    # Query patterns
    (
        r"db\.query\((\w+)\)\.filter\((.*?)\)\.first\(\)",
        r"(await db.execute(select(\1).where(\2))).scalars().first()",
    ),
    (
        r"db\.query\((\w+)\)\.filter\((.*?)\)\.all\(\)",
        r"(await db.execute(select(\1).where(\2))).scalars().all()",
    ),
    # Commit and refresh
    (r"(\s+)db\.commit\(\)", r"\1await db.commit()"),
    (r"(\s+)db\.refresh\((.*?)\)", r"\1await db.refresh(\2)"),
    # Simple query with all
    (r"query\.all\(\)", r"(await db.execute(query)).scalars().all()"),
    (r"query\.first\(\)", r"(await db.execute(query)).scalars().first()"),
]

# Apply replacements
for pattern, replacement in replacements:
    content = re.sub(pattern, replacement, content)

# Additional manual fixes for complex query building
complex_patterns = [
    # query = db.query(Something)
    (r"query = db\.query\((\w+)\)", r"query = select(\1)"),
    # query.filter -> query.where
    (r"query\.filter\(", r"query.where("),
    # query.order_by stays the same
]

for pattern, replacement in complex_patterns:
    content = re.sub(pattern, replacement, content)

# Write back
file_path.write_text(content, encoding="utf-8")

print("✅ Conversion complete!")
print("Converted:")
print("- db.query() → select()")
print("- .filter() → .where()")
print("- .first()/.all() → (await db.execute()).scalars().first()/all()")
print("- db.commit() → await db.commit()")
print("- db.refresh() → await db.refresh()")
