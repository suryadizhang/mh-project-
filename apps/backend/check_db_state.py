"""
Check database state to see what tables and columns exist
"""
import psycopg2

# Connect to database (Supabase)
conn = psycopg2.connect(
    host="db.yuchqvpctookhjovvdwi.supabase.co",
    database="postgres",
    user="postgres",
    password="DkYokZB945vm3itM",
    port=5432
)
cur = conn.cursor()

print("=" * 80)
print("DATABASE STATE CHECK")
print("=" * 80)

# Check if social_accounts table exists
cur.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'lead' 
        AND table_name = 'social_accounts'
    )
""")
social_accounts_exists = cur.fetchone()[0]
print(f"\n✓ social_accounts table exists: {social_accounts_exists}")

# Check if social_identities table exists
cur.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'lead' 
        AND table_name = 'social_identities'
    )
""")
social_identities_exists = cur.fetchone()[0]
print(f"✓ social_identities table exists: {social_identities_exists}")

# Check social_threads columns
print(f"\n{'='*80}")
print("SOCIAL_THREADS COLUMNS:")
print(f"{'='*80}")
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_schema = 'lead' 
    AND table_name = 'social_threads'
    ORDER BY ordinal_position
""")
social_threads_cols = [row[0] for row in cur.fetchall()]
print(f"Total columns: {len(social_threads_cols)}")
print(f"Columns: {', '.join(social_threads_cols)}")

# Check which new columns are missing
new_cols_needed = [
    'account_id', 'social_identity_id', 'assigned_to', 'priority',
    'subject', 'context_url', 'message_count', 'last_response_at',
    'resolved_at', 'tags'
]
missing_cols = [col for col in new_cols_needed if col not in social_threads_cols]
existing_cols = [col for col in new_cols_needed if col in social_threads_cols]

print(f"\n✗ MISSING columns ({len(missing_cols)}): {', '.join(missing_cols) if missing_cols else 'NONE'}")
print(f"✓ EXISTING columns ({len(existing_cols)}): {', '.join(existing_cols) if existing_cols else 'NONE'}")

# Check social_messages columns
print(f"\n{'='*80}")
print("SOCIAL_MESSAGES COLUMNS:")
print(f"{'='*80}")
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_schema = 'lead' 
    AND table_name = 'social_messages'
    ORDER BY ordinal_position
""")
social_messages_cols = [row[0] for row in cur.fetchall()]
print(f"Total columns: {len(social_messages_cols)}")
print(f"Columns: {', '.join(social_messages_cols)}")

# Check which new columns are missing
new_msg_cols_needed = [
    'message_ref', 'direction', 'kind', 'author_handle', 'author_name',
    'media', 'sentiment_score', 'intent_tags', 'read_at', 'created_at'
]
missing_msg_cols = [col for col in new_msg_cols_needed if col not in social_messages_cols]
existing_msg_cols = [col for col in new_msg_cols_needed if col in social_messages_cols]

print(f"\n✗ MISSING columns ({len(missing_msg_cols)}): {', '.join(missing_msg_cols) if missing_msg_cols else 'NONE'}")
print(f"✓ EXISTING columns ({len(existing_msg_cols)}): {', '.join(existing_msg_cols) if existing_msg_cols else 'NONE'}")

# Check reviews table columns
print(f"\n{'='*80}")
print("REVIEWS TABLE COLUMNS:")
print(f"{'='*80}")
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_schema = 'public' 
    AND table_name = 'reviews'
    ORDER BY ordinal_position
""")
reviews_cols = [row[0] for row in cur.fetchall()]
print(f"Total columns: {len(reviews_cols)}")
print(f"Columns: {', '.join(reviews_cols)}")

# Check which new columns are missing
new_review_cols_needed = [
    'account_id', 'status', 'acknowledged_at', 'responded_at', 'platform_metadata'
]
missing_review_cols = [col for col in new_review_cols_needed if col not in reviews_cols]
existing_review_cols = [col for col in new_review_cols_needed if col in reviews_cols]

print(f"\n✗ MISSING columns ({len(missing_review_cols)}): {', '.join(missing_review_cols) if missing_review_cols else 'NONE'}")
print(f"✓ EXISTING columns ({len(existing_review_cols)}): {', '.join(existing_review_cols) if existing_review_cols else 'NONE'}")

print(f"\n{'='*80}")
print("SUMMARY:")
print(f"{'='*80}")
print(f"✓ Tables to create: {0 if social_accounts_exists else 1} social_accounts, {0 if social_identities_exists else 1} social_identities")
print(f"✓ social_threads: {len(missing_cols)} columns to add")
print(f"✓ social_messages: {len(missing_msg_cols)} columns to add")
print(f"✓ reviews: {len(missing_review_cols)} columns to add")

if not missing_cols and not missing_msg_cols and not missing_review_cols and social_accounts_exists and social_identities_exists:
    print("\n🎉 ALL CHANGES ALREADY APPLIED! Migration can be skipped or marked as applied.")
else:
    print("\n⚠️  MIGRATION NEEDED - Some changes are missing")

cur.close()
conn.close()
