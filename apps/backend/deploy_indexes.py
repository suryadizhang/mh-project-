"""
Deploy Performance Indexes to Supabase Database
Automated deployment script for 001_create_performance_indexes.sql
"""
import asyncio
import sys
from pathlib import Path

# Add backend src to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir / "src"))

from dotenv import load_dotenv
load_dotenv(backend_dir / ".env")

from sqlalchemy import text
from core.database import AsyncSessionLocal


async def deploy_indexes():
    """Deploy all performance indexes from SQL file."""
    
    print("=" * 80)
    print("DEPLOYING DATABASE PERFORMANCE INDEXES")
    print("=" * 80)
    print()
    
    # Read SQL file
    sql_file = Path(__file__).parent.parent.parent / "database" / "migrations" / "001_create_performance_indexes.sql"
    
    if not sql_file.exists():
        print(f"❌ ERROR: SQL file not found: {sql_file}")
        return False
    
    print(f"📄 Reading SQL file: {sql_file.name}")
    sql_content = sql_file.read_text(encoding='utf-8')
    
    # Split into individual statements (separated by semicolons)
    statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]
    
    print(f"📊 Found {len(statements)} SQL statements to execute")
    print()
    
    # Execute statements
    success_count = 0
    error_count = 0
    errors = []
    
    async with AsyncSessionLocal() as session:
        for i, statement in enumerate(statements, 1):
            # Extract index name for progress display
            index_name = "Unknown"
            if "CREATE INDEX" in statement:
                parts = statement.split("CREATE INDEX")[1].split("ON")
                if len(parts) >= 2:
                    index_name = parts[0].replace("IF NOT EXISTS", "").strip()
            
            try:
                print(f"[{i}/{len(statements)}] Creating index: {index_name}...", end=" ")
                await session.execute(text(statement))
                await session.commit()
                print("✅")
                success_count += 1
                
            except Exception as e:
                error_msg = str(e)
                # Ignore "already exists" errors
                if "already exists" in error_msg.lower():
                    print("⏭️  (already exists)")
                    success_count += 1
                else:
                    print(f"❌ ERROR")
                    print(f"   {error_msg}")
                    error_count += 1
                    errors.append({
                        "index": index_name,
                        "statement": statement[:100] + "...",
                        "error": error_msg
                    })
    
    print()
    print("=" * 80)
    print("DEPLOYMENT SUMMARY")
    print("=" * 80)
    print(f"✅ Successful: {success_count}")
    print(f"❌ Failed: {error_count}")
    print(f"📊 Total: {len(statements)}")
    print()
    
    if errors:
        print("ERRORS:")
        for err in errors:
            print(f"  - {err['index']}: {err['error']}")
        print()
    
    # Verify indexes
    print("VERIFYING INDEXES...")
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("""
            SELECT COUNT(*) 
            FROM pg_indexes 
            WHERE indexname LIKE 'idx_%'
            AND schemaname IN ('core', 'identity', 'lead', 'newsletter', 'integra', 'feedback')
        """))
        index_count = result.scalar()
        print(f"✅ Found {index_count} performance indexes in database")
    
    print()
    print("=" * 80)
    
    if error_count == 0:
        print("🎉 DEPLOYMENT SUCCESSFUL!")
        print("   All indexes deployed successfully.")
        print("   Expected performance improvement: 10x-100x faster queries")
        return True
    else:
        print("⚠️  DEPLOYMENT COMPLETED WITH ERRORS")
        print(f"   {success_count} indexes deployed, {error_count} failed")
        print("   Review errors above and retry failed indexes manually")
        return False


async def show_index_stats():
    """Show statistics about deployed indexes."""
    print()
    print("=" * 80)
    print("INDEX STATISTICS")
    print("=" * 80)
    
    async with AsyncSessionLocal() as session:
        # Count by schema
        result = await session.execute(text("""
            SELECT 
                schemaname,
                COUNT(*) as index_count
            FROM pg_indexes
            WHERE indexname LIKE 'idx_%'
            AND schemaname IN ('core', 'identity', 'lead', 'newsletter', 'integra', 'feedback')
            GROUP BY schemaname
            ORDER BY schemaname
        """))
        
        print("\nIndexes by Schema:")
        for row in result.fetchall():
            print(f"  {row[0]:<20} {row[1]:>3} indexes")
        
        # Show top tables with most indexes
        result = await session.execute(text("""
            SELECT 
                schemaname || '.' || tablename as full_table,
                COUNT(*) as index_count
            FROM pg_indexes
            WHERE indexname LIKE 'idx_%'
            AND schemaname IN ('core', 'identity', 'lead', 'newsletter', 'integra', 'feedback')
            GROUP BY schemaname, tablename
            ORDER BY index_count DESC
            LIMIT 10
        """))
        
        print("\nTop 10 Most Indexed Tables:")
        for row in result.fetchall():
            print(f"  {row[0]:<40} {row[1]:>2} indexes")
    
    print("=" * 80)


if __name__ == "__main__":
    print()
    print("🚀 Starting index deployment...")
    print("   Database: Supabase PostgreSQL (yuchqvpctookhjovvdwi)")
    print("   Target: 50+ performance indexes")
    print()
    
    # Run deployment
    success = asyncio.run(deploy_indexes())
    
    if success:
        # Show statistics
        asyncio.run(show_index_stats())
        
        print()
        print("✅ Next Steps:")
        print("   1. Monitor query performance in admin dashboard")
        print("   2. Run comprehensive API tests again")
        print("   3. Update documentation with new performance metrics")
        print()
        sys.exit(0)
    else:
        print()
        print("⚠️  Deployment had errors. Review output above.")
        print()
        sys.exit(1)
