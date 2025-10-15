"""
Database initialization script
Run this to create tables in your database
"""

import asyncio
from app.core.database import async_engine, Base
from app.models.user import User  # Import to register the model
from app.models.classroom import ClassModel  # Import to register the model
from app.models.subject import Subject  # Import to register the model
from app.models.teacher_subject import TeacherSubject  # Import to register the model
from app.models.student_class import StudentClass  # Import to register the model
from app.models.admin_login_log import AdminLoginLog  # Import to register the model
from app.models.notification import Notification  # Import to register the model

async def create_tables():
    """Create all tables."""
    async with async_engine.begin() as conn:
        # Drop all tables first to ensure clean schema
        print("Dropping existing tables...")
        await conn.run_sync(Base.metadata.drop_all)
        
        # Create all tables with correct schema
        print("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
    
    print("Tables created successfully!")
    print("You can now start registering users.")

if __name__ == "__main__":
    asyncio.run(create_tables())