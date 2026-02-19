"""
Migration script to add password reset fields to users table.
Run this script once to update your database schema.

Usage:
    python migrate_add_password_reset_fields.py
"""
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.utils.database import db
from sqlalchemy import text

def migrate():
    """Add password reset columns to the users table."""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if reset_token column exists
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='reset_token'
            """))
            
            if result.fetchone() is None:
                print("Adding reset_token column to users table...")
                db.session.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN reset_token VARCHAR(255)
                """))
                db.session.commit()
                print("✓ Added reset_token column")
            else:
                print("✓ reset_token column already exists")
            
            # Check if reset_token_expires column exists
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='reset_token_expires'
            """))
            
            if result.fetchone() is None:
                print("Adding reset_token_expires column to users table...")
                db.session.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN reset_token_expires TIMESTAMP
                """))
                db.session.commit()
                print("✓ Added reset_token_expires column")
            else:
                print("✓ reset_token_expires column already exists")
            
            # Create index on reset_token for faster lookups
            result = db.session.execute(text("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename='users' AND indexname='ix_users_reset_token'
            """))
            
            if result.fetchone() is None:
                print("Creating index on reset_token...")
                db.session.execute(text("""
                    CREATE INDEX ix_users_reset_token ON users(reset_token)
                """))
                db.session.commit()
                print("✓ Created index on reset_token")
            else:
                print("✓ Index on reset_token already exists")
            
            print("\n✓ Migration completed successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ Migration failed: {str(e)}")
            raise

if __name__ == '__main__':
    print("Starting database migration for password reset fields...")
    print("=" * 50)
    migrate()
    print("=" * 50)

