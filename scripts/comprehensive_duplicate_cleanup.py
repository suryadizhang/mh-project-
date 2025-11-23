"""
COMPREHENSIVE DUPLICATE MODEL CLEANUP
Removes ALL duplicate model files and consolidates to single source of truth.

Author: AI Agent Nuclear Consolidation
Date: 2024-11-20
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

# Base paths
BACKEND_SRC = Path(r"C:\Users\surya\projects\MH webapps\apps\backend\src")
BACKUP_DIR = Path(r"C:\Users\surya\projects\MH webapps\backups") / f"comprehensive-cleanup-{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Files to DELETE (duplicates)
FILES_TO_DELETE = [
    # DUPLICATE AI HOSPITALITY MODELS (2 files)
    "db/models/ai_hospitality.py",
    "db/models/ai_hospitality_training.py",
    
    # DUPLICATE AUDIT LOGS
    "models/audit.py",
    
    # DUPLICATE USER MODEL (already moved, but check)
    "models/user.py",
    
    # DUPLICATE STATION MODELS (if exists)
    "models/station.py",
    
    # OLD DB MODELS DIRECTORY (entire folder)
    "db/models/",
]

# SINGLE SOURCE OF TRUTH (keep these)
CANONICAL_MODELS = {
    "User": "core/auth/models.py",
    "UserSession": "core/auth/models.py",
    "AuditLog": "core/auth/models.py",
    "PasswordResetToken": "core/auth/models.py",
    
    "Station": "core/auth/station_models.py",
    "StationUser": "core/auth/station_models.py",
    "StationAuditLog": "core/auth/station_models.py",
    "StationAccessToken": "core/auth/station_models.py",
    
    "OAuthAccount": "core/auth/oauth_models.py",
    "AdminInvitation": "core/auth/oauth_models.py",
    "AdminAccessLog": "core/auth/oauth_models.py",
    
    "Customer": "models/customer.py",
    "Booking": "models/booking.py",
    "Payment": "models/booking.py",
    "BookingReminder": "models/booking_reminder.py",
    
    "BusinessRule": "models/knowledge_base.py",
    "FAQItem": "models/knowledge_base.py",
    "TrainingData": "models/knowledge_base.py",
    "UpsellRule": "models/knowledge_base.py",
    "SeasonalOffer": "models/knowledge_base.py",
    "AvailabilityCalendar": "models/knowledge_base.py",
    "CustomerTonePreference": "models/knowledge_base.py",
    "MenuItem": "models/knowledge_base.py",
    "PricingTier": "models/knowledge_base.py",
    "SyncHistory": "models/knowledge_base.py",
    
    "Escalation": "models/escalation.py",
    "CallRecording": "models/call_recording.py",
    "SystemEvent": "models/system_event.py",
    "TermsAcknowledgment": "models/terms_acknowledgment.py",
    "Role": "models/role.py",
    "Permission": "models/role.py",
    "Review": "models/review.py",
    "PaymentNotification": "models/payment_notification.py",
    "Business": "models/business.py",
    "Lead": "models/lead.py",
}


def backup_file(file_path: Path):
    """Backup a file before deletion."""
    if not file_path.exists():
        return False
    
    # Create backup directory structure
    relative_path = file_path.relative_to(BACKEND_SRC)
    backup_path = BACKUP_DIR / relative_path
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Copy file
    shutil.copy2(file_path, backup_path)
    print(f"✅ Backed up: {relative_path}")
    return True


def delete_file(file_path: Path):
    """Delete a file after backup."""
    if not file_path.exists():
        print(f"⏭️  Already deleted: {file_path.relative_to(BACKEND_SRC)}")
        return False
    
    # Backup first
    backup_file(file_path)
    
    # Delete
    file_path.unlink()
    print(f"🗑️  Deleted: {file_path.relative_to(BACKEND_SRC)}")
    return True


def delete_directory(dir_path: Path):
    """Delete entire directory after backup."""
    if not dir_path.exists():
        print(f"⏭️  Already deleted: {dir_path.relative_to(BACKEND_SRC)}")
        return False
    
    # Backup entire directory
    relative_path = dir_path.relative_to(BACKEND_SRC)
    backup_path = BACKUP_DIR / relative_path
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    
    shutil.copytree(dir_path, backup_path, dirs_exist_ok=True)
    print(f"✅ Backed up directory: {relative_path}")
    
    # Delete
    shutil.rmtree(dir_path)
    print(f"🗑️  Deleted directory: {relative_path}")
    return True


def main():
    """Execute comprehensive cleanup."""
    print("=" * 80)
    print("COMPREHENSIVE DUPLICATE MODEL CLEANUP")
    print("=" * 80)
    print()
    
    # Create backup directory
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📦 Backup location: {BACKUP_DIR}\n")
    
    deleted_count = 0
    
    # Process each file/directory
    print("🔍 Processing deletions...\n")
    
    for item in FILES_TO_DELETE:
        full_path = BACKEND_SRC / item
        
        if item.endswith("/"):
            # Directory
            if delete_directory(full_path):
                deleted_count += 1
        else:
            # File
            if delete_file(full_path):
                deleted_count += 1
    
    print()
    print("=" * 80)
    print(f"✅ CLEANUP COMPLETE - {deleted_count} items removed")
    print("=" * 80)
    print()
    
    print("📋 SINGLE SOURCE OF TRUTH:")
    print()
    for model, location in sorted(CANONICAL_MODELS.items()):
        print(f"  {model:<30} → {location}")
    
    print()
    print("🔐 ROLLBACK:")
    print(f"  All files backed up to: {BACKUP_DIR}")
    print()
    
    return deleted_count


if __name__ == "__main__":
    deleted = main()
    print(f"\n🎯 Next step: Run automated import fixer to update references")
    print(f"   python scripts/fix_comprehensive_imports.py")
