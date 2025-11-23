"""
Find all broken TODO import comments that are missing the actual import statement.
"""
import re
from pathlib import Path

backend_src = Path(r'C:\Users\surya\projects\MH webapps\apps\backend\src')

broken_imports = []

for py_file in backend_src.rglob('*.py'):
    if 'backup' in str(py_file):
        continue
    
    try:
        lines = py_file.read_text(encoding='utf-8').split('\n')
        
        for i, line in enumerate(lines, 1):
            # Look for TODO comments followed by indented lines
            if 'TODO' in line and ('not migrated' in line or 'Legacy' in line):
                # Check if next few lines are orphaned imports (start with whitespace or close paren)
                next_lines = lines[i:min(i+5, len(lines))]
                for j, next_line in enumerate(next_lines):
                    if next_line.strip() and (next_line.startswith('    ') or next_line.strip() == ')'):
                        if not next_line.strip().startswith('#'):
                            broken_imports.append({
                                'file': py_file.relative_to(backend_src),
                                'line': i,
                                'context': lines[max(0, i-2):min(i+5, len(lines))]
                            })
                            break
    except:
        pass

print('=' * 80)
print(f'BROKEN TODO IMPORT PATTERNS ({len(broken_imports)} found)')
print('=' * 80)
print()

for item in broken_imports:
    print(f"File: {item['file']}")
    print(f"Line: {item['line']}")
    print("Context:")
    for line in item['context']:
        print(f"  {line}")
    print()
