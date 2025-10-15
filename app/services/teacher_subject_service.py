from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from app.models.teacher_subject import TeacherSubject
from app.models.user import User, UserRole
from app.models.subject import Subject
from app.schemas.teacher_subject import TeacherSubjectCreate, TeacherSubjectBulkCreate
from fastapi import HTTPException, status

class TeacherSubjectService:
    """Service layer for teacher-subject assignment operations."""
    
    @staticmethod
    async def assign_teacher_to_subject(db: AsyncSession, assignment_data: TeacherSubjectCreate) -> TeacherSubject:
        """Assign a teacher to a subject."""
        # Verify teacher exists and has teacher role
        teacher_result = await db.execute(
            select(User).where(
                and_(User.id == assignment_data.teacher_id, User.role == UserRole.teacher)
            )
        )
        teacher = teacher_result.scalar_one_or_none()
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher not found or user is not a teacher"
            )
        
        # Verify subject exists
        subject_result = await db.execute(select(Subject).where(Subject.id == assignment_data.subject_id))
        subject = subject_result.scalar_one_or_none()
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found"
            )
        
        try:
            # Create assignment
            db_assignment = TeacherSubject(
                teacher_id=assignment_data.teacher_id,
                subject_id=assignment_data.subject_id
            )
            
            db.add(db_assignment)
            await db.commit()
            await db.refresh(db_assignment)
            return db_assignment
            
        except IntegrityError as e:
            await db.rollback()
            if "unique_teacher_subject" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Teacher is already assigned to this subject"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Assignment creation failed"
                )
    
    @staticmethod
    async def bulk_assign_teacher_to_subjects(db: AsyncSession, assignment_data: TeacherSubjectBulkCreate) -> List[TeacherSubject]:
        """Assign a teacher to multiple subjects."""
        # Verify teacher exists and has teacher role
        teacher_result = await db.execute(
            select(User).where(
                and_(User.id == assignment_data.teacher_id, User.role == UserRole.teacher)
            )
        )
        teacher = teacher_result.scalar_one_or_none()
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher not found or user is not a teacher"
            )
        
        # Verify all subjects exist
        subjects_result = await db.execute(
            select(Subject).where(Subject.id.in_(assignment_data.subject_ids))
        )
        subjects = subjects_result.scalars().all()
        if len(subjects) != len(assignment_data.subject_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more subjects not found"
            )
        
        assignments = []
        for subject_id in assignment_data.subject_ids:
            try:
                # Check if assignment already exists
                existing_result = await db.execute(
                    select(TeacherSubject).where(
                        and_(
                            TeacherSubject.teacher_id == assignment_data.teacher_id,
                            TeacherSubject.subject_id == subject_id
                        )
                    )
                )
                existing = existing_result.scalar_one_or_none()
                
                if not existing:
                    db_assignment = TeacherSubject(
                        teacher_id=assignment_data.teacher_id,
                        subject_id=subject_id
                    )
                    db.add(db_assignment)
                    assignments.append(db_assignment)
                else:
                    assignments.append(existing)
                    
            except Exception as e:
                await db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to assign subject {subject_id}"
                )
        
        await db.commit()
        
        # Refresh all new assignments
        for assignment in assignments:
            await db.refresh(assignment)
        
        return assignments
    
    @staticmethod
    async def get_assignment_by_id(db: AsyncSession, assignment_id: int) -> Optional[TeacherSubject]:
        """Get teacher-subject assignment by ID."""
        result = await db.execute(
            select(TeacherSubject)
            .options(
                selectinload(TeacherSubject.teacher),
                selectinload(TeacherSubject.subject).selectinload(Subject.class_obj)
            )
            .where(TeacherSubject.id == assignment_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_teacher_subjects(db: AsyncSession, teacher_id: int) -> List[TeacherSubject]:
        """Get all subjects assigned to a teacher."""
        result = await db.execute(
            select(TeacherSubject)
            .options(
                selectinload(TeacherSubject.subject).selectinload(Subject.class_obj)
            )
            .where(TeacherSubject.teacher_id == teacher_id)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_subject_teachers(db: AsyncSession, subject_id: int) -> List[TeacherSubject]:
        """Get all teachers assigned to a subject."""
        result = await db.execute(
            select(TeacherSubject)
            .options(selectinload(TeacherSubject.teacher))
            .where(TeacherSubject.subject_id == subject_id)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_all_assignments(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        teacher_id: Optional[int] = None,
        subject_id: Optional[int] = None
    ) -> List[TeacherSubject]:
        """Get all teacher-subject assignments with optional filters."""
        query = select(TeacherSubject).options(
            selectinload(TeacherSubject.teacher),
            selectinload(TeacherSubject.subject).selectinload(Subject.class_obj)
        )
        
        # Apply filters
        if teacher_id:
            query = query.where(TeacherSubject.teacher_id == teacher_id)
        if subject_id:
            query = query.where(TeacherSubject.subject_id == subject_id)
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def remove_teacher_from_subject(db: AsyncSession, teacher_id: int, subject_id: int) -> bool:
        """Remove teacher assignment from a subject."""
        result = await db.execute(
            select(TeacherSubject).where(
                and_(
                    TeacherSubject.teacher_id == teacher_id,
                    TeacherSubject.subject_id == subject_id
                )
            )
        )
        assignment = result.scalar_one_or_none()
        
        if not assignment:
            return False
        
        await db.delete(assignment)
        await db.commit()
        return True
    
    @staticmethod
    async def remove_assignment_by_id(db: AsyncSession, assignment_id: int) -> bool:
        """Remove teacher-subject assignment by ID."""
        assignment = await TeacherSubjectService.get_assignment_by_id(db, assignment_id)
        if not assignment:
            return False
        
        await db.delete(assignment)
        await db.commit()
        return True
    
    @staticmethod
    async def remove_all_teacher_assignments(db: AsyncSession, teacher_id: int) -> int:
        """Remove all subject assignments for a teacher."""
        result = await db.execute(
            select(TeacherSubject).where(TeacherSubject.teacher_id == teacher_id)
        )
        assignments = result.scalars().all()
        
        count = len(assignments)
        for assignment in assignments:
            await db.delete(assignment)
        
        await db.commit()
        return count
    
    @staticmethod
    async def get_teachers_list(db: AsyncSession) -> List[User]:
        """Get all users with teacher role."""
        result = await db.execute(
            select(User).where(User.role == UserRole.teacher).order_by(User.name)
        )
        return result.scalars().all()