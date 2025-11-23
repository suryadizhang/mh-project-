"""
Fix all broken TODO import patterns by commenting out orphaned import lines.
"""
import re
from pathlib import Path

backend_src = Path(r'C:\Users\surya\projects\MH webapps\apps\backend\src')

fixed_count = 0

for py_file in backend_src.rglob('*.py'):
    if 'backup' in str(py_file):
        continue
    
    try:
        lines = py_file.read_text(encoding='utf-8').split('\n')
        modified = False
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Look for TODO comments followed by orphaned imports
            if 'TODO' in line and ('not migrated' in line or 'Legacy' in line or 'REMOVED' in line):
                # Check next lines for orphaned imports
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    
                    # If it's a continuation of imports (indented or closing paren)
                    if next_line.strip():
                        # Orphaned import line pattern
                        if (next_line.startswith('    ') or next_line.strip() == ')' or 
                            next_line.strip().startswith(')  # Phase')):
                            # Not already commented
                            if not next_line.strip().startswith('#'):
                                # Comment it out
                                indent = len(next_line) - len(next_line.lstrip())
                                lines[j] = ' ' * indent + '# ' + next_line.lstrip()
                                modified = True
                                j += 1
                            else:
                                j += 1
                        else:
                            # Not an orphaned import, stop checking
                            break
                    else:
                        j += 1
            
            i += 1
        
        if modified:
            py_file.write_text('\n'.join(lines), encoding='utf-8')
            fixed_count += 1
            print(f"✅ Fixed: {py_file.relative_to(backend_src)}")
    
    except Exception as e:
        print(f"❌ Error in {py_file.relative_to(backend_src)}: {e}")

print()
print('=' * 80)
print(f'✅ FIXED {fixed_count} FILES')
print('=' * 80)
