from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from app.models.subject import Subject
from app.models.classroom import ClassModel
from app.schemas.subject import SubjectCreate, SubjectUpdate
from fastapi import HTTPException, status

class SubjectService:
    """Service layer for subject operations."""
    
    @staticmethod
    async def create_subject(db: AsyncSession, subject_data: SubjectCreate) -> Subject:
        """Create a new subject."""
        # First check if the class exists
        class_result = await db.execute(select(ClassModel).where(ClassModel.id == subject_data.class_id))
        class_obj = class_result.scalar_one_or_none()
        if not class_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class not found"
            )
        
        try:
            # Create subject instance
            db_subject = Subject(
                name=subject_data.name,
                class_id=subject_data.class_id
            )
            
            db.add(db_subject)
            await db.commit()
            await db.refresh(db_subject)
            return db_subject
            
        except IntegrityError as e:
            await db.rollback()
            if "unique_class_subject" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Subject with this name already exists in this class"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Subject creation failed"
                )
    
    @staticmethod
    async def get_subject_by_id(db: AsyncSession, subject_id: int) -> Optional[Subject]:
        """Get subject by ID."""
        result = await db.execute(
            select(Subject)
            .options(selectinload(Subject.class_obj))
            .where(Subject.id == subject_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_subjects_by_class_id(db: AsyncSession, class_id: int) -> List[Subject]:
        """Get all subjects for a specific class."""
        result = await db.execute(
            select(Subject)
            .where(Subject.class_id == class_id)
            .order_by(Subject.name)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_subjects(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        class_id: Optional[int] = None
    ) -> List[Subject]:
        """Get list of subjects with optional class filter."""
        query = select(Subject).options(selectinload(Subject.class_obj))
        
        # Apply class filter if provided
        if class_id:
            query = query.where(Subject.class_id == class_id)
        
        # Apply pagination and ordering
        query = query.offset(skip).limit(limit).order_by(Subject.name)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def update_subject(
        db: AsyncSession, 
        subject_id: int, 
        subject_update: SubjectUpdate
    ) -> Optional[Subject]:
        """Update subject information."""
        db_subject = await SubjectService.get_subject_by_id(db, subject_id)
        if not db_subject:
            return None
        
        # If class_id is being updated, check if the new class exists
        if subject_update.class_id and subject_update.class_id != db_subject.class_id:
            class_result = await db.execute(select(ClassModel).where(ClassModel.id == subject_update.class_id))
            class_obj = class_result.scalar_one_or_none()
            if not class_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Target class not found"
                )
        
        # Update fields
        update_data = subject_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_subject, field, value)
        
        try:
            await db.commit()
            await db.refresh(db_subject)
            return db_subject
        except IntegrityError as e:
            await db.rollback()
            if "unique_class_subject" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Subject with this name already exists in this class"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Subject update failed"
                )
    
    @staticmethod
    async def delete_subject(db: AsyncSession, subject_id: int) -> bool:
        """Delete subject."""
        db_subject = await SubjectService.get_subject_by_id(db, subject_id)
        if not db_subject:
            return False
        
        await db.delete(db_subject)
        await db.commit()
        return True
    
    @staticmethod
    async def search_subjects(
        db: AsyncSession, 
        search_term: str, 
        class_id: Optional[int] = None
    ) -> List[Subject]:
        """Search subjects by name with optional class filter."""
        query = select(Subject).options(selectinload(Subject.class_obj))
        
        # Add search condition
        query = query.where(Subject.name.contains(search_term))
        
        # Add class filter if provided
        if class_id:
            query = query.where(Subject.class_id == class_id)
        
        # Order by name
        query = query.order_by(Subject.name)
        
        result = await db.execute(query)
        return result.scalars().all()