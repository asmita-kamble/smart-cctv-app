"""
Migration script to add RTSP configuration fields to cameras table.
Run this script to add rtsp_username, rtsp_password, and rtsp_path columns.
"""
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.utils.database import db

def migrate_add_rtsp_fields():
    """Add RTSP fields to cameras table."""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if columns already exist
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('cameras')]
            
            print("Current camera table columns:", columns)
            
            # Add rtsp_username if it doesn't exist
            if 'rtsp_username' not in columns:
                print("Adding rtsp_username column...")
                db.session.execute(text("ALTER TABLE cameras ADD COLUMN rtsp_username VARCHAR(100)"))
                db.session.commit()
                print("✓ Added rtsp_username column")
            else:
                print("✓ rtsp_username column already exists")
            
            # Add rtsp_password if it doesn't exist
            if 'rtsp_password' not in columns:
                print("Adding rtsp_password column...")
                db.session.execute(text("ALTER TABLE cameras ADD COLUMN rtsp_password VARCHAR(255)"))
                db.session.commit()
                print("✓ Added rtsp_password column")
            else:
                print("✓ rtsp_password column already exists")
            
            # Add rtsp_path if it doesn't exist
            if 'rtsp_path' not in columns:
                print("Adding rtsp_path column...")
                db.session.execute(text("ALTER TABLE cameras ADD COLUMN rtsp_path VARCHAR(255)"))
                db.session.commit()
                print("✓ Added rtsp_path column")
            else:
                print("✓ rtsp_path column already exists")
            
            print("\n✅ Migration completed successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Migration failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

if __name__ == '__main__':
    print("Starting migration to add RTSP fields...")
    success = migrate_add_rtsp_fields()
    sys.exit(0 if success else 1)

