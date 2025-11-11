"""
Migration: Add Customer Contact Fields and Initials Option
Adds customer_name, customer_email, customer_phone, and show_initials_only to customer_review_blog_posts
"""

import sqlite3
from pathlib import Path

def apply_migration():
    db_path = Path(__file__).parent.parent / "test_myhibachi.db"
    
    print(f"📦 Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(customer_review_blog_posts)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Add customer contact fields if they don't exist
        if 'customer_name' not in columns:
            print("✓ Adding customer_name column...")
            cursor.execute("""
                ALTER TABLE customer_review_blog_posts 
                ADD COLUMN customer_name VARCHAR(255)
            """)
        
        if 'customer_email' not in columns:
            print("✓ Adding customer_email column...")
            cursor.execute("""
                ALTER TABLE customer_review_blog_posts 
                ADD COLUMN customer_email VARCHAR(255)
            """)
        
        if 'customer_phone' not in columns:
            print("✓ Adding customer_phone column...")
            cursor.execute("""
                ALTER TABLE customer_review_blog_posts 
                ADD COLUMN customer_phone VARCHAR(50)
            """)
        
        if 'show_initials_only' not in columns:
            print("✓ Adding show_initials_only column...")
            cursor.execute("""
                ALTER TABLE customer_review_blog_posts 
                ADD COLUMN show_initials_only BOOLEAN DEFAULT 0
            """)
        
        # Commit changes
        conn.commit()
        
        print("\n✅ Migration completed successfully!")
        print("\n📊 Verifying new columns...")
        
        # Verify columns exist
        cursor.execute("PRAGMA table_info(customer_review_blog_posts)")
        all_columns = cursor.fetchall()
        
        new_columns = ['customer_name', 'customer_email', 'customer_phone', 'show_initials_only']
        for col in new_columns:
            if col in [c[1] for c in all_columns]:
                print(f"   ✓ {col}: Added successfully")
            else:
                print(f"   ❌ {col}: Failed to add")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        raise
    
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Running Customer Contact Fields Migration...")
    apply_migration()
