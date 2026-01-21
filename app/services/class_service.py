from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.models.classroom import ClassModel
from app.schemas.classroom import ClassCreate, ClassUpdate
from fastapi import HTTPException, status

class ClassService:
    """Service layer for class operations."""
    
    @staticmethod
    async def create_class(db: AsyncSession, class_data: ClassCreate) -> ClassModel:
        """Create a new class."""
        try:
            # Create class instance
            db_class = ClassModel(
                name=class_data.name,
                region_id=class_data.region_id,
                is_active=class_data.is_active
            )
            
            db.add(db_class)
            await db.commit()
            await db.refresh(db_class)
            return db_class
            
        except IntegrityError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Class creation failed"
            )
    
    @staticmethod
    async def get_class_by_id(db: AsyncSession, class_id: int) -> Optional[ClassModel]:
        """Get class by ID."""
        result = await db.execute(select(ClassModel).where(ClassModel.id == class_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_class_by_name(db: AsyncSession, name: str) -> Optional[ClassModel]:
        """Get class by name."""
        result = await db.execute(select(ClassModel).where(ClassModel.name == name))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_classes(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[ClassModel]:
        """Get list of classes with optional is_active filter."""
        query = select(ClassModel)
        if is_active is not None:
            query = query.where(ClassModel.is_active == is_active)
        query = query.offset(skip).limit(limit).order_by(ClassModel.name)
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def update_class(
        db: AsyncSession, 
        class_id: int, 
        class_update: ClassUpdate
    ) -> Optional[ClassModel]:
        """Update class information."""
        db_class = await ClassService.get_class_by_id(db, class_id)
        if not db_class:
            return None
        
        # Update fields
        update_data = class_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_class, field, value)
        
        try:
            await db.commit()
            await db.refresh(db_class)
            return db_class
        except IntegrityError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Class update failed"
            )
    
    @staticmethod
    async def delete_class(db: AsyncSession, class_id: int) -> bool:
        """Delete class. Sets class_id to NULL for all students in this class first."""
        db_class = await ClassService.get_class_by_id(db, class_id)
        if not db_class:
            return False
        
        # First, set class_id to NULL for all users in this class
        from app.models.user import User
        query = select(User).where(User.class_id == class_id)
        result = await db.execute(query)
        users_in_class = result.scalars().all()
        
        for user in users_in_class:
            user.class_id = None
        
        # Now delete the class
        await db.delete(db_class)
        await db.commit()
        return True
    
    @staticmethod
    async def search_classes(db: AsyncSession, search_term: str, is_active: Optional[bool] = None) -> List[ClassModel]:
        """Search classes by name with optional is_active filter."""
        query = select(ClassModel).where(ClassModel.name.contains(search_term))
        if is_active is not None:
            query = query.where(ClassModel.is_active == is_active)
        query = query.order_by(ClassModel.name)
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_classes_by_region(db: AsyncSession, region_id: int, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None) -> List[ClassModel]:
        """Get classes by region ID with optional is_active filter."""
        query = select(ClassModel).where(ClassModel.region_id == region_id)
        if is_active is not None:
            query = query.where(ClassModel.is_active == is_active)
        query = query.offset(skip).limit(limit).order_by(ClassModel.name)
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_active_classes_by_name(db: AsyncSession, name: str) -> Optional[ClassModel]:
        """Get active class by name."""
        result = await db.execute(
            select(ClassModel).where(
                ClassModel.name == name,
                ClassModel.is_active == True
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def duplicate_class_as_active(db: AsyncSession, original_class: ClassModel) -> ClassModel:
        """Duplicate a class and set it as active, marking the original as inactive."""
        # Create new active class with same name and region
        new_class = ClassModel(
            name=original_class.name,
            region_id=original_class.region_id,
            is_active=True
        )
        db.add(new_class)
        
        # Mark original class as inactive
        original_class.is_active = False
        
        await db.flush()  # Get the new class ID
        return new_class
