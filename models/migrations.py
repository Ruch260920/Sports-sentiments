"""
Database Migration Scripts
Handles database schema updates
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models.database import DATABASE_URL
from models.models import Base

def migrate_database():
    """Run database migrations"""
    print("🔄 Running database migrations...")
    
    # Create engine
    engine = create_engine(DATABASE_URL)
    
    try:
        # Check if new tables exist
        with engine.connect() as conn:
            # Check for Tweet table
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'tweets'
                );
            """))
            tweets_exist = result.scalar()
            
            # Check for TwitterWebhook table
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'twitter_webhooks'
                );
            """))
            webhooks_exist = result.scalar()
            
            # Check for new Entity columns
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'entities' 
                AND column_name IN ('twitter_username', 'twitter_user_id', 'is_twitter_tracked');
            """))
            new_columns = [row[0] for row in result.fetchall()]
            
        if not tweets_exist:
            print("📝 Creating tweets table...")
            Base.metadata.create_all(engine, tables=[Base.metadata.tables['tweets']])
            
        if not webhooks_exist:
            print("📝 Creating twitter_webhooks table...")
            Base.metadata.create_all(engine, tables=[Base.metadata.tables['twitter_webhooks']])
            
        if len(new_columns) < 3:
            print("🔧 Adding new columns to entities table...")
            missing_columns = ['twitter_username', 'twitter_user_id', 'is_twitter_tracked']
            for col in missing_columns:
                if col not in new_columns:
                    try:
                        conn.execute(text(f"ALTER TABLE entities ADD COLUMN {col} VARCHAR(100)"))
                        if col == 'is_twitter_tracked':
                            conn.execute(text(f"ALTER TABLE entities ALTER COLUMN {col} SET DEFAULT FALSE"))
                        print(f"  ✅ Added column: {col}")
                    except Exception as e:
                        print(f"  ⚠️  Column {col} might already exist: {e}")
            
            conn.commit()
            
        print("✅ Database migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        engine.dispose()

def rollback_migration():
    """Rollback database changes (use with caution!)"""
    print("⚠️  Rolling back database changes...")
    
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Drop new tables
            conn.execute(text("DROP TABLE IF EXISTS tweets CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS twitter_webhooks CASCADE"))
            
            # Remove new columns from entities
            try:
                conn.execute(text("ALTER TABLE entities DROP COLUMN IF EXISTS twitter_username"))
                conn.execute(text("ALTER TABLE entities DROP COLUMN IF EXISTS twitter_user_id"))
                conn.execute(text("ALTER TABLE entities DROP COLUMN IF EXISTS is_twitter_tracked"))
            except:
                pass
                
            conn.commit()
            
        print("✅ Rollback completed")
        
    except Exception as e:
        print(f"❌ Rollback failed: {e}")
        raise
    finally:
        engine.dispose()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback_migration()
    else:
        migrate_database() 