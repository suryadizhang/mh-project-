"""
Script to fix imports in AI modules after reorganization
Updates 'from app.' to 'from api.ai.endpoints.' in AI files
"""
import os
import re
from pathlib import Path

def update_ai_imports_in_file(file_path):
    """Update import statements in AI files"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Track if any changes were made
        original_content = content
        
        # Pattern 1: from app.something import ...
        content = re.sub(r'^from app\.', 'from api.ai.endpoints.', content, flags=re.MULTILINE)
        
        # Pattern 2: import app.something
        content = re.sub(r'^import app\.', 'import api.ai.endpoints.', content, flags=re.MULTILINE)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Updated AI imports in: {file_path}")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")
        return False

def main():
    """Update all import paths in the moved AI files"""
    base_path = Path("apps/backend/src/api/ai")
    
    if not base_path.exists():
        print(f"❌ Path not found: {base_path}")
        return
    
    updated_files = 0
    total_files = 0
    
    # Find all Python files
    for py_file in base_path.rglob("*.py"):
        total_files += 1
        if update_ai_imports_in_file(py_file):
            updated_files += 1
    
    print(f"\n📊 Summary:")
    print(f"Total Python files: {total_files}")
    print(f"Files updated: {updated_files}")
    print(f"Files unchanged: {total_files - updated_files}")

if __name__ == "__main__":
    main()