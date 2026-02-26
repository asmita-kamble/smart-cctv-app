"""
Migration script to add email verification fields to users table.
Run this script once to update your database schema.

Usage:
    cd backend && python migrate_add_email_verification_fields.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.utils.database import db
from sqlalchemy import text


def migrate():
    """Add email verification columns to the users table."""
    app = create_app()

    with app.app_context():
        try:
            # email_verified
            result = db.session.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'email_verified'
            """))
            if result.fetchone() is None:
                print("Adding email_verified column to users table...")
                db.session.execute(text("""
                    ALTER TABLE users
                    ADD COLUMN email_verified BOOLEAN NOT NULL DEFAULT TRUE
                """))
                db.session.commit()
                print("✓ Added email_verified column (existing users set to TRUE)")
            else:
                print("✓ email_verified column already exists")

            # email_verification_token
            result = db.session.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'email_verification_token'
            """))
            if result.fetchone() is None:
                print("Adding email_verification_token column...")
                db.session.execute(text("""
                    ALTER TABLE users
                    ADD COLUMN email_verification_token VARCHAR(255)
                """))
                db.session.commit()
                print("✓ Added email_verification_token column")
            else:
                print("✓ email_verification_token column already exists")

            # email_verification_expires
            result = db.session.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'email_verification_expires'
            """))
            if result.fetchone() is None:
                print("Adding email_verification_expires column...")
                db.session.execute(text("""
                    ALTER TABLE users
                    ADD COLUMN email_verification_expires TIMESTAMP
                """))
                db.session.commit()
                print("✓ Added email_verification_expires column")
            else:
                print("✓ email_verification_expires column already exists")

            # Index for token lookup
            result = db.session.execute(text("""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = 'users' AND indexname = 'ix_users_email_verification_token'
            """))
            if result.fetchone() is None:
                print("Creating index on email_verification_token...")
                db.session.execute(text("""
                    CREATE INDEX ix_users_email_verification_token ON users(email_verification_token)
                """))
                db.session.commit()
                print("✓ Created index on email_verification_token")
            else:
                print("✓ Index on email_verification_token already exists")

            print("\n✓ Email verification migration completed successfully!")

        except Exception as e:
            db.session.rollback()
            print(f"✗ Migration failed: {str(e)}")
            raise


if __name__ == "__main__":
    print("Starting database migration for email verification fields...")
    print("=" * 50)
    migrate()
    print("=" * 50)
