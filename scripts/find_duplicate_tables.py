"""
Find ALL duplicate table definitions across the codebase.
"""
import re
from pathlib import Path
from collections import defaultdict

# Find all __tablename__ definitions
backend_src = Path(r'C:\Users\surya\projects\MH webapps\apps\backend\src')
tables = defaultdict(list)

for py_file in backend_src.rglob('*.py'):
    if 'backup' in str(py_file) or 'migration' in str(py_file):
        continue
    
    try:
        content = py_file.read_text(encoding='utf-8')
        matches = re.finditer(r'__tablename__\s*=\s*["\'](\w+)["\']', content)
        for match in matches:
            table_name = match.group(1)
            rel_path = py_file.relative_to(backend_src)
            tables[table_name].append(str(rel_path))
    except Exception as e:
        pass

# Print duplicates (tables defined in multiple files)
print('=' * 80)
print('DUPLICATE TABLE DEFINITIONS')
print('=' * 80)
print()

duplicates_found = False
duplicate_count = 0

for table, files in sorted(tables.items()):
    if len(files) > 1:
        duplicates_found = True
        duplicate_count += 1
        print(f'🚨 {table} ({len(files)} definitions):')
        for f in sorted(set(files)):
            print(f'   - {f}')
        print()

if not duplicates_found:
    print('✅ No duplicate table definitions found!')
    print()
else:
    print(f'❌ Found {duplicate_count} duplicate tables!')
    print()

# Print all tables (single source of truth)
print('=' * 80)
print(f'ALL TABLES - SINGLE SOURCE OF TRUTH ({len([t for t, f in tables.items() if len(f) == 1])} tables)')
print('=' * 80)
print()

for table, files in sorted(tables.items()):
    if len(files) == 1:
        print(f'{table:<35} → {files[0]}')

print()
print(f'Total tables: {len(tables)}')
print(f'Duplicates: {duplicate_count}')
print(f'Unique: {len([t for t, f in tables.items() if len(f) == 1])}')
