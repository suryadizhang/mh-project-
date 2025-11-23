"""
COMPREHENSIVE IMPORT FIXER
Updates all imports after duplicate model cleanup.

Handles ALL model import patterns and fixes them to use single source of truth.
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple

# Base path
BACKEND_SRC = Path(r"C:\Users\surya\projects\MH webapps\apps\backend\src")

# Import replacement rules (OLD → NEW)
IMPORT_REPLACEMENTS = {
    # User model: core/auth/models.py is source of truth
    r"from models\.user import User": "from core.auth.models import User",
    r"from models import User": "from core.auth.models import User",
    
    # Audit logs: core/auth/models.py is source of truth
    r"from models\.audit import (AuditLog|SecurityAuditLog)": "from core.auth.models import AuditLog",
    r"from models import.*AuditLog": "from core.auth.models import AuditLog",
    
    # Station models: core/auth/station_models.py is source of truth
    r"from models\.station import": "from core.auth.station_models import",
    r"from models import.*Station([^A-Za-z])": r"from core.auth.station_models import Station\1",
    
    # AI Hospitality duplicates → models/knowledge_base.py
    r"from db\.models\.ai_hospitality import": "from models.knowledge_base import",
    r"from db\.models\.ai_hospitality_training import": "from models.knowledge_base import",
    r"from api\.ai\.endpoints\.models import (BusinessRule|FAQItem|TrainingData|UpsellRule|CustomerTonePreference)": 
        r"from models.knowledge_base import \1",
    
    # Customer duplicates → models/customer.py
    r"from api\.ai\.endpoints\.models import Customer": "from models.customer import Customer",
    
    # Escalation duplicates → models/escalation.py
    r"from db\.models\.ai_hospitality import Escalation": "from models.escalation import Escalation",
    r"from api\.ai\.endpoints\.models import Escalation": "from models.escalation import Escalation",
}

# Models that should be commented out (not migrated)
UNMIGRATED_MODELS = [
    "db.models.ai_hospitality",
    "db.models.ai_hospitality_training",
]


class ImportFixer:
    def __init__(self):
        self.stats = {
            "scanned": 0,
            "fixed": 0,
            "skipped": 0,
            "errors": 0,
        }
        self.changes: List[Tuple[str, int]] = []  # (file, num_changes)
    
    def fix_imports_in_file(self, file_path: Path) -> int:
        """Fix imports in a single file. Returns number of changes."""
        try:
            content = file_path.read_text(encoding='utf-8')
            original_content = content
            changes = 0
            
            # Apply each replacement rule
            for old_pattern, new_import in IMPORT_REPLACEMENTS.items():
                matches = list(re.finditer(old_pattern, content))
                if matches:
                    # Check if import is already commented
                    for match in matches:
                        line_start = content.rfind('\n', 0, match.start()) + 1
                        line_end = content.find('\n', match.end())
                        if line_end == -1:
                            line_end = len(content)
                        line = content[line_start:line_end]
                        
                        # Skip if already commented
                        if line.strip().startswith('#'):
                            continue
                        
                        # Replace import
                        content = re.sub(old_pattern, new_import, content)
                        changes += len(matches)
            
            # Comment out unmigrated imports
            for unmigrated in UNMIGRATED_MODELS:
                pattern = f"from {unmigrated}"
                if pattern in content:
                    lines = content.split('\n')
                    new_lines = []
                    for line in lines:
                        if pattern in line and not line.strip().startswith('#'):
                            new_lines.append(f"# TODO: Unmigrated model - {line}")
                            changes += 1
                        else:
                            new_lines.append(line)
                    content = '\n'.join(new_lines)
            
            # Save if changed
            if content != original_content:
                file_path.write_text(content, encoding='utf-8')
                self.changes.append((str(file_path.relative_to(BACKEND_SRC)), changes))
                return changes
            
            return 0
            
        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
            self.stats["errors"] += 1
            return 0
    
    def process_directory(self, directory: Path):
        """Process all Python files in directory recursively."""
        for py_file in directory.rglob("*.py"):
            # Skip backups and migrations
            if "backup" in str(py_file) or "migration" in str(py_file):
                continue
            
            self.stats["scanned"] += 1
            changes = self.fix_imports_in_file(py_file)
            
            if changes > 0:
                self.stats["fixed"] += 1
                print(f"✅ Fixed {changes:>3} imports in {py_file.relative_to(BACKEND_SRC)}")
            else:
                self.stats["skipped"] += 1
    
    def print_summary(self):
        """Print summary of changes."""
        print()
        print("=" * 80)
        print("IMPORT FIX SUMMARY")
        print("=" * 80)
        print(f"Total files scanned:  {self.stats['scanned']}")
        print(f"Files fixed:          {self.stats['fixed']}")
        print(f"Files skipped:        {self.stats['skipped']}")
        print(f"Errors:               {self.stats['errors']}")
        print()
        
        if self.changes:
            print("Top changed files:")
            sorted_changes = sorted(self.changes, key=lambda x: x[1], reverse=True)
            for file, count in sorted_changes[:20]:
                print(f"  {count:>3} changes - {file}")


def main():
    print("=" * 80)
    print("COMPREHENSIVE IMPORT FIXER")
    print("=" * 80)
    print()
    
    fixer = ImportFixer()
    
    # Process all directories
    directories = [
        BACKEND_SRC / "api",
        BACKEND_SRC / "routers",
        BACKEND_SRC / "services",
        BACKEND_SRC / "workers",
        BACKEND_SRC / "cqrs",
        BACKEND_SRC / "core",
        BACKEND_SRC / "middleware",
        BACKEND_SRC / "monitoring",
    ]
    
    for directory in directories:
        if directory.exists():
            print(f"🔍 Processing {directory.relative_to(BACKEND_SRC)}/...")
            fixer.process_directory(directory)
    
    fixer.print_summary()
    print()
    print("✅ Import fixing complete!")
    print()


if __name__ == "__main__":
    main()
