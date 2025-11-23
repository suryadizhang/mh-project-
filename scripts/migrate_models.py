"""
Automated model migration script - Extract models from legacy file and create modular files
"""

import re
from pathlib import Path

# Source and destination
legacy_file = Path(r"c:\Users\surya\projects\MH webapps\backups\pre-nuclear-cleanup-20251120_220938\legacy_lead_newsletter.py")
dest_dir = Path(r"c:\Users\surya\projects\MH webapps\apps\backend\src\models")

# Read legacy file
with open(legacy_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Extract all class definitions with their full content
def extract_classes(content):
    """Extract all class definitions from Python file"""
    classes = {}
    lines = content.split('\n')
    current_class = None
    current_content = []
    current_indent = 0
    
    for i, line in enumerate(lines):
        # Check if this is a class definition
        class_match = re.match(r'^class (\w+)\([^)]*\):', line)
        if class_match:
            # Save previous class if exists
            if current_class:
                classes[current_class] = '\n'.join(current_content)
            
            # Start new class
            current_class = class_match.group(1)
            current_content = [line]
            current_indent = len(line) - len(line.lstrip())
        elif current_class:
            # Check if we're still in the class (indented)
            if line.strip() == '':
                current_content.append(line)
            elif line.startswith(' ') or line.startswith('\t'):
                current_content.append(line)
            else:
                # End of class
                classes[current_class] = '\n'.join(current_content)
                current_class = None
                current_content = []
    
    # Save last class
    if current_class:
        classes[current_class] = '\n'.join(current_content)
    
    return classes

classes = extract_classes(content)

print(f"Found {len(classes)} classes")
print("\nClasses:")
for name in sorted(classes.keys()):
    lines = classes[name].count('\n') + 1
    print(f"  - {name:30} ({lines:3} lines)")

# Categorize classes
lead_models = ['Lead', 'LeadContact', 'LeadContext', 'LeadEvent']
campaign_models = ['Campaign', 'CampaignEvent', 'Subscriber', 'SMSDeliveryEvent']
social_models = ['SocialThread', 'SocialMessage', 'Review']

print("\n" + "="*80)
print("LEAD MODELS")
print("="*80)
for name in lead_models:
    if name in classes:
        print(f"\n{name}:")
        print(classes[name][:200] + "...")

print("\n" + "="*80)
print("CAMPAIGN MODELS")
print("="*80)
for name in campaign_models:
    if name in classes:
        print(f"\n{name}:")
        print(classes[name][:200] + "...")
