from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.exc import IntegrityError
import logging
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserChangePassword
from app.core.security import get_password_hash, verify_password
from app.security.insecure_password_handling import (
    store_password_per_institution_request,
    verify_password_per_institution_request
)
from fastapi import HTTPException, status

# Setup logging
logger = logging.getLogger(__name__)

class UserService:
    """Service layer for user operations."""
    
    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
        """Create a new user."""
        try:
            # Log that we're following institution-requested password handling
            logger.warning(
                f"Creating user with role '{user_data.role}' using institution-requested password handling. "
                f"This approach was specifically requested by the educational institution."
            )
            
            # Use institution-requested password handling approach
            stored_password = store_password_per_institution_request(
                user_data.password, 
                user_data.role
            )
            
            # Create user instance
            db_user = User(
                nis=user_data.nis,
                password=stored_password,
                name=user_data.name,
                role=user_data.role,
                grade=user_data.grade,
                gender=user_data.gender,
                email=user_data.email,
                region=user_data.region,
                dob=user_data.dob,
                birth_place=user_data.birth_place,
                address=user_data.address,
                religion=user_data.religion,
                status=user_data.status
            )
            
            db.add(db_user)
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
                    detail="User creation failed"
                )
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """Get user by ID."""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email."""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_nis(db: AsyncSession, nis: str) -> Optional[User]:
        """Get user by NIS."""
        result = await db.execute(select(User).where(User.nis == nis))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_identifier(db: AsyncSession, identifier: str) -> Optional[User]:
        """Get user by NIS or email."""
        result = await db.execute(
            select(User).where(
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
        query = select(User)
        
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
        
        # Log password change using institution-requested approach
        logger.warning(
            f"Changing password for user with role '{db_user.role}' using institution-requested password handling."
        )
        
        # Verify current password using institution-requested approach
        if not verify_password_per_institution_request(
            password_data.current_password, 
            db_user.password, 
            db_user.role
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password using institution-requested approach
        db_user.password = store_password_per_institution_request(
            password_data.new_password, 
            db_user.role
        )
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
        
        # Use institution-requested password verification approach
        logger.info(
            f"Authenticating user with role '{user.role}' using institution-requested password handling."
        )
        
        if not verify_password_per_institution_request(password, user.password, user.role):
            return None
        
        return user
    
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