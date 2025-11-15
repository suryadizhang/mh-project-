"""Fix smart quotes in compliance.py"""

compliance_file = "apps/backend/src/core/compliance.py"

with open(compliance_file, encoding="utf-8") as f:
    content = f.read()

# Replace smart quotes with regular quotes
replacements = {
    "'": "'",  # Left single quote
    "'": "'",  # Right single quote
    """: '"',  # Left double quote
    """: '"',  # Right double quote
    "—": "-",  # Em dash
    "–": "-",  # En dash
}

for old, new in replacements.items():
    content = content.replace(old, new)

with open(compliance_file, "w", encoding="utf-8") as f:
    f.write(content)

print(f"✅ Fixed smart quotes in {compliance_file}")
