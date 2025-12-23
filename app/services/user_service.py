from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
import logging
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserChangePassword
from app.core.security import get_password_hash, verify_password
from fastapi import HTTPException, status

# Setup logging
logger = logging.getLogger(__name__)

class UserService:
    """Service layer for user operations."""
    
    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
        """Create a new user."""
        try:
            # Hash password
            stored_password = get_password_hash(user_data.password)
            
            # Handle parent password for student roles
            stored_parent_password = None
            if user_data.parent_password and user_data.role == "student":
                stored_parent_password = get_password_hash(user_data.parent_password)
            
            # Create user instance
            db_user = User(
                nis=user_data.nis,
                password=stored_password,
                parent_password=stored_parent_password,
                name=user_data.name,
                role=user_data.role,
                grade=user_data.grade,
                gender=user_data.gender,
                email=user_data.email,
                region_id=user_data.region_id,
                class_id=user_data.class_id,
                dob=user_data.dob,
                birth_place=user_data.birth_place,
                address=user_data.address,
                religion=user_data.religion,
                status=user_data.status
            )
            
            db.add(db_user)
            await db.commit()
            await db.refresh(db_user)
            
            # Eagerly load relationships to avoid MissingGreenlet error during serialization
            query = select(User).where(User.id == db_user.id).options(
                joinedload(User.region),
                joinedload(User.class_obj)
            )
            result = await db.execute(query)
            db_user = result.scalar_one()
            
            return db_user
            
        except IntegrityError as e:
            await db.rollback()
            if "nis" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="NIS already exists"
                )
            elif "email" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User creation failed"
                )
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """Get user by ID."""
        result = await db.execute(
            select(User)
            .options(joinedload(User.region), joinedload(User.class_obj))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email."""
        result = await db.execute(
            select(User)
            .options(joinedload(User.region), joinedload(User.class_obj))
            .where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_nis(db: AsyncSession, nis: str) -> Optional[User]:
        """Get user by NIS."""
        result = await db.execute(
            select(User)
            .options(joinedload(User.region), joinedload(User.class_obj))
            .where(User.nis == nis)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_identifier(db: AsyncSession, identifier: str) -> Optional[User]:
        """Get user by NIS or email."""
        result = await db.execute(
            select(User)
            .options(joinedload(User.region), joinedload(User.class_obj))
            .where(
                or_(User.nis == identifier, User.email == identifier)
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_users(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        role: Optional[str] = None,
        grade: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[User]:
        """Get list of users with filters."""
        query = select(User).options(joinedload(User.region), joinedload(User.class_obj))
        
        # Apply filters
        if role:
            query = query.where(User.role == role)
        if grade:
            query = query.where(User.grade == grade)
        if status:
            query = query.where(User.status == status)
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def update_user(
        db: AsyncSession, 
        user_id: int, 
        user_update: UserUpdate
    ) -> Optional[User]:
        """Update user information."""
        db_user = await UserService.get_user_by_id(db, user_id)
        if not db_user:
            return None
        
        # Update fields
        update_data = user_update.model_dump(exclude_unset=True)
        
        # Handle password hashing if present
        if 'password' in update_data and update_data['password']:
            update_data['password'] = get_password_hash(update_data['password'])
            
        # Handle parent password hashing if present
        if 'parent_password' in update_data and update_data['parent_password']:
            update_data['parent_password'] = get_password_hash(update_data['parent_password'])
            
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        try:
            await db.commit()
            await db.refresh(db_user)
            return db_user
        except IntegrityError as e:
            await db.rollback()
            if "nis" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="NIS already exists"
                )
            elif "email" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User update failed"
                )
    
    @staticmethod
    async def change_password(
        db: AsyncSession, 
        user_id: int, 
        password_data: UserChangePassword
    ) -> bool:
        """Change user password."""
        db_user = await UserService.get_user_by_id(db, user_id)
        if not db_user:
            return False
        
        # Verify current password
        if not verify_password(password_data.current_password, db_user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        db_user.password = get_password_hash(password_data.new_password)
        await db.commit()
        return True
    
    @staticmethod
    async def delete_user(db: AsyncSession, user_id: int) -> bool:
        """Delete user."""
        db_user = await UserService.get_user_by_id(db, user_id)
        if not db_user:
            return False
        
        await db.delete(db_user)
        await db.commit()
        return True
    
    @staticmethod
    async def authenticate_user(db: AsyncSession, identifier: str, password: str) -> Optional[User]:
        """Authenticate user by identifier (NIS or email) and password."""
        user = await UserService.get_user_by_identifier(db, identifier)
        if not user:
            return None
        
        if not verify_password(password, user.password):
            return None
        
        return user
    
    @staticmethod
    async def authenticate_parent_access(db: AsyncSession, identifier: str, parent_password: str) -> Optional[User]:
        """Authenticate parent access to student account by identifier (NIS or email) and parent password."""
        user = await UserService.get_user_by_identifier(db, identifier)
        if not user:
            return None
        
        # Only allow parent access to student accounts
        if user.role != "student":
            return None
        
        # Check if parent password is set
        if not user.parent_password:
            return None
        
        if not verify_password(parent_password, user.parent_password):
            return None
        
        return user
    
    @staticmethod
    async def set_parent_password(
        db: AsyncSession, 
        user_id: int, 
        student_password: str,
        parent_password: str
    ) -> bool:
        """Set parent password for student account."""
        db_user = await UserService.get_user_by_id(db, user_id)
        if not db_user:
            return False
        
        # Only students can have parent passwords
        if db_user.role != "student":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent password can only be set for student accounts"
            )
        
        # Verify student's current password
        if not verify_password(student_password, db_user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student password is incorrect"
            )
        
        # Set parent password
        db_user.parent_password = get_password_hash(parent_password)
        await db.commit()
        return True
    
    @staticmethod
    async def change_parent_password(
        db: AsyncSession, 
        user_id: int, 
        current_parent_password: str,
        new_parent_password: str
    ) -> bool:
        """Change parent password for student account."""
        db_user = await UserService.get_user_by_id(db, user_id)
        if not db_user:
            return False
        
        # Only students can have parent passwords
        if db_user.role != "student":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent password can only be changed for student accounts"
            )
        
        # Check if parent password is set
        if not db_user.parent_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No parent password is set for this account"
            )
        
        # Verify current parent password
        if not verify_password(current_parent_password, db_user.parent_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current parent password is incorrect"
            )
        
        # Update parent password
        db_user.parent_password = get_password_hash(new_parent_password)
        await db.commit()
        return True
    
    @staticmethod
    async def remove_parent_password(
        db: AsyncSession, 
        user_id: int, 
        student_password: str
    ) -> bool:
        """Remove parent password from student account."""
        db_user = await UserService.get_user_by_id(db, user_id)
        if not db_user:
            return False
        
        # Only students can have parent passwords
        if db_user.role != "student":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent password can only be removed from student accounts"
            )
        
        # Verify student's current password
        if not verify_password(student_password, db_user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student password is incorrect"
            )
        
        # Remove parent password
        db_user.parent_password = None
        await db.commit()
        return True
    
    @staticmethod
    async def update_profile_picture(
        db: AsyncSession, 
        user_id: int, 
        profile_picture_path: str
    ) -> Optional[User]:
        """Update user's profile picture path."""
        db_user = await UserService.get_user_by_id(db, user_id)
        if not db_user:
            return None
        
        db_user.profile_picture = profile_picture_path
        
        try:
            await db.commit()
            await db.refresh(db_user)
            return db_user
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update profile picture"
            )
    
    @staticmethod
    async def remove_profile_picture(db: AsyncSession, user_id: int) -> Optional[User]:
        """Remove user's profile picture."""
        db_user = await UserService.get_user_by_id(db, user_id)
        if not db_user:
            return None
        
        db_user.profile_picture = None
        
        try:
            await db.commit()
            await db.refresh(db_user)
            return db_user
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove profile picture"
            )