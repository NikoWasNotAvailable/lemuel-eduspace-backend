#!/usr/bin/env python3
"""
Management CLI for Lemuel Eduspace Backend
"""

import asyncio
import getpass
import sys
import time
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import async_engine
from app.services.user_service import UserService
from app.schemas.user import UserCreate
from app.models.user import UserRole, UserGender, UserReligion, UserStatus
from app.core.security import get_password_hash

# Import all models to ensure they are registered with SQLAlchemy
from app.models import *


class AdminManager:
    """Admin management utilities."""
    
    @staticmethod
    async def check_existing_admins(db: AsyncSession) -> int:
        """Check how many admin users exist."""
        result = await db.execute(
            text("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        )
        return result.scalar() or 0
    
    @staticmethod
    async def create_admin_interactive():
        """Interactive admin creation."""
        print("🔧 Admin User Creation Tool")
        print("=" * 50)
        
        # Check for existing admins first
        async with AsyncSession(async_engine) as db:
            admin_count = await AdminManager.check_existing_admins(db)
            if admin_count > 0:
                print(f"⚠️  Warning: {admin_count} admin user(s) already exist.")
                confirm = input("Do you want to create another admin? (y/N): ").lower()
                if confirm != 'y':
                    print("❌ Admin creation cancelled.")
                    return
        
        # Collect admin information
        print("\n📝 Enter admin details:")
        name = input("Admin Name: ").strip()
        if not name:
            print("❌ Name is required!")
            return
        
        email = input("Admin Email (optional): ").strip() or None
        nis = input("Admin NIS (leave blank for auto-generate): ").strip()
        if not nis:
            nis = f"ADMIN{int(time.time())}"
            print(f"🏷️  Auto-generated NIS: {nis}")
        
        # Gender selection
        print("\nGender options:")
        print("1. Male")
        print("2. Female")
        print("3. Skip (leave blank)")
        gender_choice = input("Select gender (1/2/3): ").strip()
        gender = None
        if gender_choice == "1":
            gender = UserGender.male
        elif gender_choice == "2":
            gender = UserGender.female
        
        # Religion selection
        print("\nReligion options:")
        print("1. Islam")
        print("2. Christian")
        print("3. Catholic")
        print("4. Hindu")
        print("5. Buddhism")
        print("6. Confucianism")
        print("7. Other")
        print("8. Skip (leave blank)")
        religion_choice = input("Select religion (1-8): ").strip()
        religion = None
        if religion_choice == "1":
            religion = UserReligion.islam
        elif religion_choice == "2":
            religion = UserReligion.christian
        elif religion_choice == "3":
            religion = UserReligion.catholic
        elif religion_choice == "4":
            religion = UserReligion.hindu
        elif religion_choice == "5":
            religion = UserReligion.buddhism
        elif religion_choice == "6":
            religion = UserReligion.confucianism
        elif religion_choice == "7":
            religion = UserReligion.other
        
        # Birth place
        birth_place = input("Birth place (optional): ").strip() or None
        
        # Address
        address = input("Address (optional): ").strip() or None
        
        # Password input
        print("\n🔑 Set admin password:")
        while True:
            password = getpass.getpass("Admin Password (min 8 chars): ")
            if len(password) < 8:
                print("❌ Password must be at least 8 characters long!")
                continue
            
            confirm_password = getpass.getpass("Confirm Password: ")
            if password != confirm_password:
                print("❌ Passwords don't match! Please try again.")
                continue
            
            break
        
        # Create the admin user
        async with AsyncSession(async_engine) as db:
            try:
                user_data = UserCreate(
                    nis=nis,
                    name=name,
                    email=email,
                    password=password,
                    role=UserRole.admin,
                    gender=gender,
                    religion=religion,
                    birth_place=birth_place,
                    address=address,
                    status=UserStatus.active
                )
                
                admin_user = await UserService.create_user(db, user_data)
                
                print("\n✅ Admin user created successfully!")
                print("=" * 50)
                print(f"👤 ID: {admin_user.id}")
                print(f"🏷️  NIS: {admin_user.nis}")
                print(f"📛 Name: {admin_user.name}")
                print(f"📧 Email: {admin_user.email or 'Not set'}")
                print(f"⚡ Role: {admin_user.role}")
                print(f"👤 Gender: {admin_user.gender or 'Not set'}")
                print(f"🕊️ Religion: {admin_user.religion or 'Not set'}")
                print(f"📍 Birth Place: {admin_user.birth_place or 'Not set'}")
                print(f"🏠 Address: {admin_user.address or 'Not set'}")
                print(f"🟢 Status: {admin_user.status}")
                print(f"� Created: {admin_user.created_at}")
                print("=" * 50)
                
            except Exception as e:
                print(f"❌ Error creating admin: {str(e)}")
    
    @staticmethod
    async def create_default_admin():
        """Create a default admin user (for automated setup)."""
        print("🔧 Creating default admin user...")
        
        async with AsyncSession(async_engine) as db:
            try:
                # Check if any admin exists
                admin_count = await AdminManager.check_existing_admins(db)
                if admin_count > 0:
                    print(f"ℹ️  Admin users already exist ({admin_count} found). Skipping default creation.")
                    return
                
                # Create default admin
                default_password = "SuperSecretAdmin123!"
                user_data = UserCreate(
                    nis="ADMIN001",
                    name="System Administrator",
                    email="admin@eduspace.com",
                    password=default_password,
                    role=UserRole.admin,
                    status=UserStatus.active
                )
                
                admin_user = await UserService.create_user(db, user_data)
                
                print("✅ Default admin user created successfully!")
                print("=" * 60)
                print("📧 Email/Identifier: admin@eduspace.com")
                print("🏷️  NIS: ADMIN001")
                print("🔑 Default Password: SuperSecretAdmin123!")
                print("⚠️  CRITICAL: Change this password immediately after first login!")
                print("=" * 60)
                
            except Exception as e:
                print(f"❌ Error creating default admin: {str(e)}")
    
    @staticmethod
    async def list_admins():
        """List all admin users."""
        print("👥 Admin Users List")
        print("=" * 60)
        
        async with AsyncSession(async_engine) as db:
            try:
                admins = await UserService.get_users(db, role="admin", limit=100)
                
                if not admins:
                    print("ℹ️  No admin users found.")
                    return
                
                print(f"Found {len(admins)} admin user(s):")
                print()
                
                for i, admin in enumerate(admins, 1):
                    print(f"{i}. ID: {admin.id}")
                    print(f"   🏷️  NIS: {admin.nis}")
                    print(f"   📛 Name: {admin.name}")
                    print(f"   📧 Email: {admin.email or 'Not set'}")
                    print(f"   👤 Gender: {admin.gender or 'Not set'}")
                    print(f"   🕊️ Religion: {admin.religion or 'Not set'}")
                    print(f"   📍 Birth Place: {admin.birth_place or 'Not set'}")
                    print(f"   🏠 Address: {admin.address or 'Not set'}")
                    print(f"   🟢 Status: {admin.status}")
                    print(f"   � Created: {admin.created_at}")
                    print(f"   🔄 Updated: {admin.updated_at}")
                    print()
                
            except Exception as e:
                print(f"❌ Error listing admins: {str(e)}")


def show_help():
    """Show help information."""
    print("🎯 Lemuel Eduspace Backend Management CLI")
    print("=" * 50)
    print("Available commands:")
    print()
    print("  create-admin     Create a new admin user (interactive)")
    print("  default-admin    Create default admin with preset credentials")
    print("  list-admins      List all existing admin users")
    print("  help            Show this help message")
    print()
    print("Examples:")
    print("  python manage.py create-admin")
    print("  python manage.py default-admin")
    print("  python manage.py list-admins")
    print()


async def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    try:
        if command == "create-admin":
            await AdminManager.create_admin_interactive()
        elif command == "default-admin":
            await AdminManager.create_default_admin()
        elif command == "list-admins":
            await AdminManager.list_admins()
        elif command in ["help", "-h", "--help"]:
            show_help()
        else:
            print(f"❌ Unknown command: {command}")
            print("Use 'python manage.py help' for available commands.")
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Operation cancelled by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())