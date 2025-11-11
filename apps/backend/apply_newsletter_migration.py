"""Apply newsletter migration to allow phone-only subscriptions."""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def apply_migration():
    """Apply migration to newsletter.subscribers table."""
    db_url = os.getenv('DATABASE_URL_SYNC')
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        try:
            # Step 1: Drop NOT NULL constraint
            print("Removing NOT NULL constraint from email_enc...")
            conn.execute(text(
                "ALTER TABLE newsletter.subscribers ALTER COLUMN email_enc DROP NOT NULL"
            ))
            conn.commit()
            print("✓ email_enc is now nullable")
            
            # Step 2: Add check constraint (may already exist, ignore if so)
            try:
                print("\nAdding check constraint to ensure at least one contact method...")
                conn.execute(text(
                    """ALTER TABLE newsletter.subscribers 
                    ADD CONSTRAINT email_or_phone_required 
                    CHECK (email_enc IS NOT NULL OR phone_enc IS NOT NULL)"""
                ))
                conn.commit()
                print("✓ Check constraint added")
            except Exception as e:
                if "already exists" in str(e):
                    print("✓ Check constraint already exists")
                else:
                    raise
            
            # Verify changes
            print("\nVerifying migration...")
            result = conn.execute(text(
                """SELECT column_name, is_nullable 
                FROM information_schema.columns 
                WHERE table_schema = 'newsletter' 
                AND table_name = 'subscribers' 
                AND column_name IN ('email_enc', 'phone_enc')
                ORDER BY column_name"""
            ))
            
            print("\nColumn constraints:")
            for row in result:
                nullable = "NULL" if row[1] == "YES" else "NOT NULL"
                print(f"  {row[0]}: {nullable}")
            
            print("\n✅ Migration completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            conn.rollback()
            raise
    
    engine.dispose()

if __name__ == "__main__":
    apply_migration()
