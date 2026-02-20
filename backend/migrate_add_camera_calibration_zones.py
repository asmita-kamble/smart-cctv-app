"""
Migration script to add camera calibration and zone configuration fields.
Run this script once to update your database schema.

Usage:
    python migrate_add_camera_calibration_zones.py
"""
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.utils.database import db
from sqlalchemy import text

def migrate():
    """Add calibration and zone configuration columns to the cameras table."""
    app = create_app()
    
    with app.app_context():
        try:
            # Calibration fields
            fields = [
                ('pixels_per_meter', 'FLOAT'),
                ('camera_height', 'FLOAT'),
                ('camera_angle', 'FLOAT'),
                ('reference_object_height', 'FLOAT'),
                ('red_zones', 'TEXT'),
                ('yellow_zones', 'TEXT'),
                ('sensitive_areas', 'TEXT'),
                ('perimeter_lines', 'TEXT')
            ]
            
            for field_name, field_type in fields:
                result = db.session.execute(text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='cameras' AND column_name='{field_name}'
                """))
                
                if result.fetchone() is None:
                    print(f"Adding {field_name} column to cameras table...")
                    db.session.execute(text(f"""
                        ALTER TABLE cameras 
                        ADD COLUMN {field_name} {field_type}
                    """))
                    db.session.commit()
                    print(f"✓ Added {field_name} column")
                else:
                    print(f"✓ {field_name} column already exists")
            
            print("\n✓ Migration completed successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ Migration failed: {str(e)}")
            raise

if __name__ == '__main__':
    print("Starting database migration for camera calibration and zones...")
    print("=" * 50)
    migrate()
    print("=" * 50)

