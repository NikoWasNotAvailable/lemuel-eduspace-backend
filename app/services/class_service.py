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
                name=class_data.name
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
        limit: int = 100
    ) -> List[ClassModel]:
        """Get list of classes."""
        query = select(ClassModel).offset(skip).limit(limit).order_by(ClassModel.name)
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
        """Delete class."""
        db_class = await ClassService.get_class_by_id(db, class_id)
        if not db_class:
            return False
        
        await db.delete(db_class)
        await db.commit()
        return True
    
    @staticmethod
    async def search_classes(db: AsyncSession, search_term: str) -> List[ClassModel]:
        """Search classes by name."""
        query = select(ClassModel).where(ClassModel.name.contains(search_term)).order_by(ClassModel.name)
        result = await db.execute(query)
        return result.scalars().all()
