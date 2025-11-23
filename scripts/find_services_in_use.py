"""
Find which services with TODO imports are actually being used by routers loaded in main.py
"""

import os
import re
from pathlib import Path

# Services with TODO imports (from grep results)
TODO_SERVICES = [
    "services/qr_tracking_service.py",
    "repositories/newsletter_analytics.py",
    "workers/campaign_metrics_tasks.py",
    "workers/outbox_processors.py",
    "workers/review_worker.py",
    "services/coupon_reminder_service.py",
    "services/station_notification_sync.py",  # ← THIS ONE IS THE PROBLEM
    "services/stripe_service.py",
    "services/webhook_service.py",
    "services/social/social_ai_generator.py",
    "services/social/social_service.py",
    "services/social/social_ai_tools.py",
    "services/review_service.py",
    "services/referral_service.py",
    "services/newsletter/sms_service.py",
    "services/nurture_campaign_service.py",
    "services/notification_group_service.py",
    "services/newsletter_service.py",
    "services/newsletter_analytics_service.py",
    "services/lead_service.py",
]

# Extract service names
SERVICE_NAMES = [Path(s).stem for s in TODO_SERVICES]

def find_imports_in_file(filepath):
    """Find all 'from X import Y' statements in a file"""
    imports = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            # Find all import statements
            pattern = r'from\s+([\w.]+)\s+import'
            matches = re.findall(pattern, content)
            imports.extend(matches)
    except Exception as e:
        pass
    return imports

def check_if_service_imported(filepath, service_names):
    """Check if any of the problematic services are imported"""
    imports = find_imports_in_file(filepath)
    found = []
    for imp in imports:
        for service in service_names:
            if service in imp:
                found.append((service, imp))
    return found

# Scan all Python files in src/
src_dir = Path(r"c:\Users\surya\projects\MH webapps\apps\backend\src")

print("=" * 80)
print("SERVICES WITH TODO IMPORTS THAT ARE ACTIVELY LOADED")
print("=" * 80)
print()

# First, find what routers are included in main.py
main_py = src_dir / "main.py"
with open(main_py, 'r', encoding='utf-8') as f:
    main_content = f.read()

# Find all router includes
router_pattern = r'from\s+(routers\.[\w.]+|api\.[\w.]+\.endpoints\.[\w]+)\s+import.*router'
loaded_routers = re.findall(router_pattern, main_content)

print(f"Found {len(loaded_routers)} routers loaded in main.py:")
for router in sorted(set(loaded_routers)):
    print(f"  - {router}")
print()

# Now check each loaded router for problematic service imports
problematic = {}

for router_path in set(loaded_routers):
    # Convert module path to file path
    file_path = src_dir / router_path.replace('.', os.sep)
    
    # Try with .py extension
    if not file_path.exists():
        file_path = Path(str(file_path) + ".py")
    
    if file_path.exists():
        found = check_if_service_imported(file_path, SERVICE_NAMES)
        if found:
            problematic[router_path] = found

print("=" * 80)
print(f"ROUTERS THAT IMPORT PROBLEMATIC SERVICES: {len(problematic)}")
print("=" * 80)
print()

for router, services in sorted(problematic.items()):
    print(f"🔴 {router}")
    for service, import_stmt in services:
        print(f"   └─ imports {service} (from {import_stmt})")
    print()

# Now check the services themselves for type annotation usage
print("=" * 80)
print("CHECKING TYPE ANNOTATIONS IN SERVICES")
print("=" * 80)
print()

for service_path in TODO_SERVICES:
    full_path = src_dir / service_path
    if full_path.exists():
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for type annotations with commented-out models
        # Pattern: look for -> SomeModel or : SomeModel where SomeModel might be undefined
        lines = content.split('\n')
        has_todo = False
        type_hints_after_todo = []
        
        for i, line in enumerate(lines, 1):
            if 'TODO:' in line and 'not migrated' in line:
                has_todo = True
            
            # Look for type hints (common patterns)
            if has_todo and ('->' in line or 'List[' in line or 'dict[' in line):
                # Extract potential model names
                type_pattern = r'->\s*([A-Z]\w+)|List\[([A-Z]\w+)\]|dict\[.*,\s*([A-Z]\w+)\]'
                matches = re.findall(type_pattern, line)
                if matches:
                    # Flatten tuple results
                    models = [m for match in matches for m in match if m]
                    if models:
                        type_hints_after_todo.append((i, line.strip(), models))
        
        if type_hints_after_todo:
            print(f"⚠️  {service_path}")
            print(f"   Has TODO comment AND type hints using potentially undefined models:")
            for line_num, line, models in type_hints_after_todo[:5]:  # Show first 5
                print(f"   Line {line_num}: {models} in: {line[:80]}")
            if len(type_hints_after_todo) > 5:
                print(f"   ... and {len(type_hints_after_todo) - 5} more")
            print()

print("=" * 80)
print("RECOMMENDATION")
print("=" * 80)
print()
print("For each service that:")
print("  1. Has TODO imports commented out")
print("  2. Uses type hints with those models")
print("  3. Is imported by a router loaded in main.py")
print()
print("ACTION: Comment out the import in the router OR disable the router in main.py")
print()
