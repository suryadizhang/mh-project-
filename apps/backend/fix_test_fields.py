"""Fix test file - remove contact fields, add required production fields"""

test_file = r"c:\Users\surya\projects\MH webapps\apps\backend\tests\test_race_condition_fix.py"

with open(test_file, "r", encoding="utf-8") as f:
    content = f.read()

# Remove contact_email and contact_phone lines
content = content.replace('            contact_email=customer.email,\n', '')
content = content.replace('            contact_phone=customer.phone,\n', '')
content = content.replace('                    contact_email=customer.email,\n', '')
content = content.replace('                    contact_phone=customer.phone,\n', '')

# Add required fields after status= lines
old_pattern1 = '            status="pending",\n        )'
new_pattern1 = '''            status="pending",
            address_encrypted="test_encrypted",
            zone="test_zone",
            station_id="00000000-0000-0000-0000-000000000001",
            deposit_due_cents=5000,
            total_due_cents=10000,
            source="test",
        )'''
content = content.replace(old_pattern1, new_pattern1)

old_pattern2 = '            status="cancelled",  # Cancelled status\n        )'
new_pattern2 = '''            status="cancelled",  # Cancelled status
            address_encrypted="test_encrypted",
            zone="test_zone",
            station_id="00000000-0000-0000-0000-000000000001",
            deposit_due_cents=5000,
            total_due_cents=10000,
            source="test",
        )'''
content = content.replace(old_pattern2, new_pattern2)

old_pattern3 = '                    status="pending",\n                )'
new_pattern3 = '''                    status="pending",
                    address_encrypted="test_encrypted",
                    zone="test_zone",
                    station_id="00000000-0000-0000-0000-000000000001",
                    deposit_due_cents=5000,
                    total_due_cents=10000,
                    source="test",
                )'''
content = content.replace(old_pattern3, new_pattern3)

with open(test_file, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ Test file fixed successfully!")
