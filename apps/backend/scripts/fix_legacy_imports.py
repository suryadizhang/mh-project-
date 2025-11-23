"""
Automated Legacy Import Fixer
Replaces all legacy model imports with modern equivalents.
"""

import os
import re
from pathlib import Path

# Define replacement mappings
REPLACEMENTS = {
    # Customer imports
    r'from models\.legacy_core import Customer': 'from models import Customer',
    r'from models\.legacy_stripe_models import StripeCustomer': '# REMOVED: StripeCustomer - use models.Customer instead',
    
    # Booking imports  
    r'from models\.legacy_core import Booking': 'from models import Booking',
    r'from models\.legacy_booking_models import Booking': 'from models import Booking',
    
    # Payment imports
    r'from models\.legacy_core import Payment': 'from models import Payment',
    r'from models\.legacy_stripe_models import StripePayment': '# REMOVED: StripePayment - use models.Payment instead',
    
    # These models don't exist in modern schema - mark for deletion
    r'from models\.legacy_lead_newsletter import .*': '# TODO: Legacy lead/newsletter models not migrated yet - needs refactor',
    r'from models\.legacy_social import .*': '# TODO: Legacy social models not migrated yet - needs refactor',
    r'from models\.legacy_events import .*': '# TODO: Legacy event sourcing not migrated yet - needs refactor',
    r'from models\.legacy_feedback import .*': '# TODO: Legacy feedback models not migrated yet - needs refactor',
    r'from models\.legacy_notification_groups import .*': '# TODO: Legacy notification models not migrated yet - needs refactor',
    r'from models\.legacy_qr_tracking import .*': '# TODO: Legacy QR tracking not migrated yet - needs refactor',
    r'from models\.legacy_booking_models import .*': '# TODO: Legacy booking models not migrated yet - needs refactor',
    r'from models\.legacy_declarative_base import .*': '# REMOVED: Use models.base.BaseModel instead',
    r'from models\.legacy_base import .*': '# REMOVED: Use models.base.BaseModel instead',
    r'from models\.legacy_encryption import .*': '# REMOVED: Encryption not needed in modern architecture',
}

def fix_file(filepath: Path) -> tuple[bool, str]:
    """Fix a single file's imports. Returns (changed, message)"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes = []
        
        for pattern, replacement in REPLACEMENTS.items():
            regex = re.compile(pattern)
            matches = list(regex.finditer(content))
            if matches:
                content = regex.sub(replacement, content)
                changes.append(f"  - Replaced {len(matches)} instance(s) of {pattern[:50]}...")
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, "\n".join(changes)
        
        return False, "No changes needed"
    
    except Exception as e:
        return False, f"ERROR: {e}"


def main():
    """Fix all Python files in src/"""
    root = Path(__file__).parent.parent / "src"
    
    print("=" * 80)
    print("🔧 AUTOMATED LEGACY IMPORT FIXER")
    print("=" * 80)
    print(f"\nScanning: {root}")
    print()
    
    stats = {
        'total': 0,
        'fixed': 0,
        'errors': 0,
        'skipped': 0
    }
    
    # Find all Python files
    for filepath in root.rglob("*.py"):
        stats['total'] += 1
        
        # Skip __pycache__
        if '__pycache__' in str(filepath):
            stats['skipped'] += 1
            continue
        
        # Fix the file
        changed, message = fix_file(filepath)
        
        if changed:
            stats['fixed'] += 1
            rel_path = filepath.relative_to(root)
            print(f"✅ FIXED: {rel_path}")
            print(message)
            print()
        elif "ERROR" in message:
            stats['errors'] += 1
            rel_path = filepath.relative_to(root)
            print(f"❌ ERROR: {rel_path}")
            print(f"   {message}")
            print()
    
    # Summary
    print("=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"Total files scanned: {stats['total']}")
    print(f"Files fixed: {stats['fixed']}")
    print(f"Files skipped: {stats['skipped']}")
    print(f"Errors: {stats['errors']}")
    print()
    
    if stats['fixed'] > 0:
        print("✅ Import fixes applied successfully!")
        print()
        print("⚠️  NEXT STEPS:")
        print("1. Review files marked with '# TODO' comments")
        print("2. Refactor code that used deleted legacy models")
        print("3. Test server startup: python run_backend.py")
        print("4. Run tests: pytest")
    else:
        print("✅ All files already clean!")
    
    print("=" * 80)


if __name__ == "__main__":
    main()
