"""Batch fix old Pydantic v1 Config to v2 ConfigDict"""
import re
import os

files_to_fix = [
    'src/api/app/cqrs/social_commands.py',
    'src/api/app/cqrs/social_queries.py',
    'src/api/app/routers/station_admin.py',
]

def fix_file(filepath):
    """Fix a single file"""
    if not os.path.exists(filepath):
        print(f"SKIP: {filepath} not found")
        return
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Pattern to match:
    #     class Config:
    #         schema_extra = {
    #             ...
    #         }
    
    # Replace with:
    #     model_config = ConfigDict(json_schema_extra={
    #         ...
    #     })
    
    pattern = r'(\s+)class Config:\s*\n\s+schema_extra = (\{(?:[^{}]|(?2))*\})'
    
    def replacement(match):
        indent = match.group(1)
        schema_dict = match.group(2)
        return f'{indent}model_config = ConfigDict(json_schema_extra={schema_dict})'
    
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"FIXED: {filepath}")
        return True
    else:
        print(f"NO CHANGES: {filepath}")
        return False

if __name__ == '__main__':
    print("Fixing Pydantic Config classes...")
    print("=" * 80)
    
    fixed_count = 0
    for filepath in files_to_fix:
        if fix_file(filepath):
            fixed_count += 1
    
    print("=" * 80)
    print(f"Fixed {fixed_count} files")
