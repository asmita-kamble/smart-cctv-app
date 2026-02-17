"""
Migration script to add new fields to cameras table and create allowed_persons table.
Run this script once to update your database schema.

Usage:
    python migrate_add_camera_fields.py
"""
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.utils.database import db
from sqlalchemy import text

def migrate():
    """Add new columns and tables to the database."""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if is_restricted_zone column exists
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='cameras' AND column_name='is_restricted_zone'
            """))
            
            if result.fetchone() is None:
                print("Adding is_restricted_zone column to cameras table...")
                db.session.execute(text("""
                    ALTER TABLE cameras 
                    ADD COLUMN is_restricted_zone BOOLEAN NOT NULL DEFAULT FALSE
                """))
                db.session.commit()
                print("✓ Added is_restricted_zone column")
            else:
                print("✓ is_restricted_zone column already exists")
            
            # Check if allowed_persons table exists
            result = db.session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name='allowed_persons'
            """))
            
            if result.fetchone() is None:
                print("Creating allowed_persons table...")
                # Create the table using SQLAlchemy
                from app.models.allowed_person import AllowedPerson
                db.create_all()
                print("✓ Created allowed_persons table")
            else:
                print("✓ allowed_persons table already exists")
            
            print("\n✓ Migration completed successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ Migration failed: {str(e)}")
            raise

if __name__ == '__main__':
    print("Starting database migration...")
    print("=" * 50)
    migrate()
    print("=" * 50)

