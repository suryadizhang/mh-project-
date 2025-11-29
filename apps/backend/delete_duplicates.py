"""Script to delete duplicate model files"""
import os

BASE = r"c:\Users\surya\projects\MH webapps\apps\backend\src"

FILES_TO_DELETE = [
    "models/knowledge_base.py",
    "monitoring/alert_rule_model.py",
    "api/ai/endpoints/models.py",
    "core/auth/station_models.py",
    "db/models/identity.py",
    "db/models/role.py",
    "db/models/escalation.py",
    "db/models/call_recording.py",
]

deleted = []
not_found = []
errors = []

for file_path in FILES_TO_DELETE:
    full_path = os.path.join(BASE, file_path)
    try:
        if os.path.exists(full_path):
            os.remove(full_path)
            deleted.append(file_path)
            print(f"✅ Deleted: {file_path}")
        else:
            not_found.append(file_path)
            print(f"⚠️ Not found: {file_path}")
    except Exception as e:
        errors.append((file_path, str(e)))
        print(f"❌ Error deleting {file_path}: {e}")

print(f"\n{'='*60}")
print(f"Summary:")
print(f"  Deleted: {len(deleted)}")
print(f"  Not found: {len(not_found)}")
print(f"  Errors: {len(errors)}")
print(f"{'='*60}")
