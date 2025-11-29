#!/usr/bin/env python3
"""Find duplicate SQLAlchemy model classes across the codebase."""

import re
from pathlib import Path
from collections import defaultdict

# Find all class definitions
pattern = re.compile(r'^class (\w+)\(Base\):', re.MULTILINE)
duplicates = defaultdict(list)

# Search in src directory
for py_file in Path('src').rglob('*.py'):
    try:
        content = py_file.read_text(encoding='utf-8')
        for match in pattern.finditer(content):
            class_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            duplicates[class_name].append((str(py_file).replace('\\', '/'), line_num))
    except Exception as e:
        pass

# Print duplicates only
print('=' * 80)
print('DUPLICATE MODEL CLASSES (2+ definitions)')
print('=' * 80)

duplicate_count = 0
total_duplicates = 0

for class_name, locations in sorted(duplicates.items()):
    if len(locations) > 1:
        duplicate_count += 1
        total_duplicates += len(locations)
        print(f'\n{class_name}: {len(locations)} copies')
        for file_path, line in sorted(locations):
            print(f'  - {file_path}:{line}')

print('\n' + '=' * 80)
print(f'SUMMARY: {duplicate_count} classes with duplicates')
print(f'Total duplicate instances: {total_duplicates}')
print(f'Files to consolidate/remove: {total_duplicates - duplicate_count}')
print('=' * 80)
