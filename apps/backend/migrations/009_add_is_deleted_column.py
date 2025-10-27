"""
Migration: Add is_deleted Column to Customer Review Blog Posts
Adds is_deleted boolean column to match BaseModel structure
"""

import sqlite3
from pathlib import Path

def apply_migration():
    db_path = Path(__file__).parent.parent / "test_myhibachi.db"
    
    print(f"[INFO] Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(customer_review_blog_posts)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Add is_deleted field if it doesn't exist
        if 'is_deleted' not in columns:
            print("[INFO] Adding is_deleted column...")
            cursor.execute("""
                ALTER TABLE customer_review_blog_posts 
                ADD COLUMN is_deleted BOOLEAN DEFAULT 0 NOT NULL
            """)
            print("[PASS] is_deleted column added successfully!")
        else:
            print("[INFO] is_deleted column already exists")
        
        # Commit changes
        conn.commit()
        
        print("\n[SUCCESS] Migration completed successfully!")
        print("\n[INFO] Verifying column...")
        
        # Verify column exists
        cursor.execute("PRAGMA table_info(customer_review_blog_posts)")
        all_columns = cursor.fetchall()
        
        if 'is_deleted' in [c[1] for c in all_columns]:
            print("   [PASS] is_deleted: Column exists")
        else:
            print("   [FAIL] is_deleted: Column missing")
        
    except Exception as e:
        print(f"\n[FAIL] Migration failed: {e}")
        conn.rollback()
        raise
    
    finally:
        conn.close()

if __name__ == "__main__":
    print("[START] Running is_deleted Column Migration...")
    apply_migration()
