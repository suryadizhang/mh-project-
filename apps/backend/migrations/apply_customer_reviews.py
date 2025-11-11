"""
Migration: Add Customer Review Blog System Tables
Run this to create customer review tables with approval workflow
"""

import sqlite3
from pathlib import Path

def apply_migration():
    db_path = Path(__file__).parent.parent / "test_myhibachi.db"
    
    print(f"📦 Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Customer review blog posts (SQLite compatible)
        print("\n✓ Creating customer_review_blog_posts table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customer_review_blog_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER REFERENCES customers(id) ON DELETE CASCADE,
                booking_id INTEGER REFERENCES bookings(id) ON DELETE SET NULL,
                
                -- Content
                title VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                
                -- Images (stored as JSON array)
                images TEXT DEFAULT '[]',
                
                -- Status (admin approval workflow)
                status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
                approved_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                approved_at TIMESTAMP,
                rejection_reason TEXT,
                
                -- External reviews
                reviewed_on_google BOOLEAN DEFAULT 0,
                reviewed_on_yelp BOOLEAN DEFAULT 0,
                google_review_link TEXT,
                yelp_review_link TEXT,
                
                -- Metadata
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- SEO
                slug VARCHAR(255) UNIQUE,
                keywords TEXT,
                
                -- Engagement
                likes_count INTEGER DEFAULT 0,
                helpful_count INTEGER DEFAULT 0
            )
        """)
        
        # Indexes for performance
        print("✓ Creating indexes for customer_review_blog_posts...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_reviews_status ON customer_review_blog_posts(status)",
            "CREATE INDEX IF NOT EXISTS idx_reviews_customer ON customer_review_blog_posts(customer_id)",
            "CREATE INDEX IF NOT EXISTS idx_reviews_created ON customer_review_blog_posts(created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_reviews_rating ON customer_review_blog_posts(rating)",
            "CREATE INDEX IF NOT EXISTS idx_reviews_slug ON customer_review_blog_posts(slug)",
        ]
        
        for index in indexes:
            cursor.execute(index)
        
        # Admin approval log
        print("✓ Creating review_approval_log table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS review_approval_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                review_id INTEGER REFERENCES customer_review_blog_posts(id) ON DELETE CASCADE,
                admin_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                action VARCHAR(20) NOT NULL CHECK (action IN ('pending_review', 'approved', 'rejected')),
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Indexes for approval log
        print("✓ Creating indexes for review_approval_log...")
        approval_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_approval_log_review ON review_approval_log(review_id)",
            "CREATE INDEX IF NOT EXISTS idx_approval_log_admin ON review_approval_log(admin_id)",
            "CREATE INDEX IF NOT EXISTS idx_approval_log_created ON review_approval_log(created_at DESC)",
        ]
        
        for index in approval_indexes:
            cursor.execute(index)
        
        # Commit changes
        conn.commit()
        
        print("\n✅ Migration completed successfully!")
        print("\n📊 Verifying tables...")
        
        # Verify tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%review%'")
        tables = cursor.fetchall()
        
        print(f"   - Found {len(tables)} review-related tables:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"     • {table[0]}: {count} rows")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        raise
    
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Running Customer Review Migration...")
    apply_migration()
