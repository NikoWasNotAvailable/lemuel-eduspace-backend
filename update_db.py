import asyncio
from sqlalchemy import text
from app.core.database import async_engine, Base
# Import all models to ensure they are registered with Base.metadata
from app.models.user import User
from app.models.classroom import ClassModel
from app.models.subject import Subject
from app.models.teacher_subject import TeacherSubject
from app.models.admin_login_log import AdminLoginLog
from app.models.notification import Notification
from app.models.user_notification import UserNotification
from app.models.session import Session
from app.models.session_attachment import SessionAttachment
from app.models.banner import Banner
from app.models.region import Region

async def update_database():
    async with async_engine.begin() as conn:
        print("Checking and updating database schema...")
        
        # 1. Fix notifications table (add created_by if missing)
        try:
            print("Attempting to add created_by column to notifications table...")
            await conn.execute(text("ALTER TABLE notifications ADD COLUMN created_by INT NULL;"))
            await conn.execute(text("ALTER TABLE notifications ADD CONSTRAINT fk_notifications_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;"))
            print("Added created_by column to notifications.")
        except Exception as e:
            # Column likely already exists or other error
            print(f"Note: Could not add created_by column (it might already exist): {e}")

        # 2. Create any missing tables (like banners)
        print("Creating any missing tables...")
        await conn.run_sync(Base.metadata.create_all)
        
    print("Database update complete!")

if __name__ == "__main__":
    asyncio.run(update_database())
