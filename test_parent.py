"""
Test script for parent functionality
Run this after setting up the database to test parent operations
"""

import asyncio
from app.core.database import get_async_db
from app.services.user_service import UserService
from app.services.parent_service import ParentService
from app.schemas.user import UserCreate
from app.schemas.parent import ParentCreate
from app.models.user import UserRole

async def test_parent_functionality():
    """Test parent creation and authentication."""
    
    async for db in get_async_db():
        try:
            print("Testing parent functionality...")
            
            # First, create a test student
            student_data = UserCreate(
                nis="TEST001",
                name="Test Student",
                password="testpass123",
                role=UserRole.student,
                email="student@test.com"
            )
            
            print("Creating test student...")
            student = await UserService.create_user(db, student_data)
            print(f"Student created: {student.name} (ID: {student.id})")
            
            # Now create a parent for this student
            parent_data = ParentCreate(
                student_id=student.id,
                parent_password="parentpass123"
            )
            
            print("Creating test parent...")
            parent = await ParentService.create_parent(db, parent_data)
            print(f"Parent created for student {parent.student_id} (ID: {parent.id})")
            
            # Test parent authentication by student NIS
            print("Testing parent authentication by student NIS...")
            auth_parent = await ParentService.authenticate_parent(
                db, "TEST001", "parentpass123"
            )
            
            if auth_parent:
                print("Parent authentication by student NIS successful!")
                print(f"Student: {auth_parent.student.name}")
            else:
                print("Parent authentication by student NIS failed!")
            
            # Test authentication by student email
            print("Testing authentication by student email...")
            auth_parent_email = await ParentService.authenticate_parent(
                db, "student@test.com", "parentpass123"
            )
            
            if auth_parent_email:
                print("Parent authentication by student email successful!")
            else:
                print("Parent authentication by student email failed!")
                
            print("\nParent functionality test completed!")
            
        except Exception as e:
            print(f"Error during testing: {e}")
            import traceback
            traceback.print_exc()
        finally:
            break

if __name__ == "__main__":
    asyncio.run(test_parent_functionality())