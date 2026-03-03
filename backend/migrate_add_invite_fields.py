"""
Migration script to add invite token fields to users table for User Management.
Run this script once to update your database schema.

Usage:
    cd backend && python migrate_add_invite_fields.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.utils.database import db
from sqlalchemy import text


def migrate():
    """Add invite_token and invite_token_expires columns to the users table."""
    app = create_app()

    with app.app_context():
        try:
            result = db.session.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='users' AND column_name='invite_token'
            """))
            if result.fetchone() is None:
                print("Adding invite_token column to users table...")
                db.session.execute(text("""
                    ALTER TABLE users
                    ADD COLUMN invite_token VARCHAR(255)
                """))
                db.session.commit()
                print("✓ Added invite_token column")
            else:
                print("✓ invite_token column already exists")

            result = db.session.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='users' AND column_name='invite_token_expires'
            """))
            if result.fetchone() is None:
                print("Adding invite_token_expires column to users table...")
                db.session.execute(text("""
                    ALTER TABLE users
                    ADD COLUMN invite_token_expires TIMESTAMP
                """))
                db.session.commit()
                print("✓ Added invite_token_expires column")
            else:
                print("✓ invite_token_expires column already exists")

            result = db.session.execute(text("""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename='users' AND indexname='ix_users_invite_token'
            """))
            if result.fetchone() is None:
                print("Creating index on invite_token...")
                db.session.execute(text("""
                    CREATE INDEX ix_users_invite_token ON users(invite_token)
                """))
                db.session.commit()
                print("✓ Created index on invite_token")
            else:
                print("✓ Index on invite_token already exists")

            print("\n✓ Migration completed successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"✗ Migration failed: {str(e)}")
            raise


if __name__ == '__main__':
    print("Starting database migration for invite fields...")
    print("=" * 50)
    migrate()
    print("=" * 50)
