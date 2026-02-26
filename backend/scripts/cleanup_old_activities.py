"""
One-time script to delete activity records that are NOT uploads (video_uploaded/image_uploaded).
These are old detection-based entries like "Suspicious activity: rapid_movement (motion: 34.8%)".
Activities are now only for uploads; detection events are in Alerts.

Run from backend directory: python scripts/cleanup_old_activities.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models.activity import Activity
from app.repositories.activity_repository import UPLOAD_ACTIVITY_TYPES
from app.utils.database import db


def main():
    app = create_app()
    with app.app_context():
        # Find activities that are NOT uploads
        to_delete = Activity.query.filter(
            ~Activity.activity_type.in_(UPLOAD_ACTIVITY_TYPES)
        ).all()
        count = len(to_delete)
        if count == 0:
            print("No old (non-upload) activities found. Nothing to delete.")
            return
        print(f"Found {count} old activity record(s) to delete (e.g. suspicious_activity, rapid_movement, motion_detected).")
        for a in to_delete:
            desc = (a.description or '')[:60]
            print(f"  - id={a.id} type={a.activity_type} desc={desc}")
        for a in to_delete:
            db.session.delete(a)
        db.session.commit()
        print(f"Deleted {count} old activity record(s). Activities list will now show only uploads.")


if __name__ == "__main__":
    main()
