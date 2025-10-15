from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_
from sqlalchemy.orm import selectinload
from app.models.student_class import StudentClass
from app.models.user import User, UserRole
from app.models.classroom import ClassModel
from app.schemas.student_class import StudentClassCreate, StudentClassBulkCreate, StudentClassBulkCreateMultiple
from fastapi import HTTPException, status

class StudentClassService:
    
    @staticmethod
    async def enroll_student_in_class(db: AsyncSession, enrollment_data: StudentClassCreate) -> StudentClass:
        """Enroll a student in a class."""
        # Check if student exists and has student role
        student_query = select(User).where(
            and_(User.id == enrollment_data.student_id, User.role == UserRole.student)
        )
        student_result = await db.execute(student_query)
        student = student_result.scalar_one_or_none()
        
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        
        # Check if class exists
        class_query = select(ClassModel).where(ClassModel.id == enrollment_data.class_id)
        class_result = await db.execute(class_query)
        class_obj = class_result.scalar_one_or_none()
        
        if not class_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class not found"
            )
        
        # Check if enrollment already exists
        existing_query = select(StudentClass).where(
            and_(
                StudentClass.student_id == enrollment_data.student_id,
                StudentClass.class_id == enrollment_data.class_id
            )
        )
        existing_result = await db.execute(existing_query)
        existing_enrollment = existing_result.scalar_one_or_none()
        
        if existing_enrollment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student is already enrolled in this class"
            )
        
        # Create new enrollment
        enrollment = StudentClass(
            student_id=enrollment_data.student_id,
            class_id=enrollment_data.class_id
        )
        
        db.add(enrollment)
        await db.commit()
        await db.refresh(enrollment)
        return enrollment
    
    @staticmethod
    async def bulk_enroll_student_in_classes(
        db: AsyncSession, 
        enrollment_data: StudentClassBulkCreate
    ) -> List[StudentClass]:
        """Enroll a student in multiple classes."""
        # Check if student exists and has student role
        student_query = select(User).where(
            and_(User.id == enrollment_data.student_id, User.role == UserRole.student)
        )
        student_result = await db.execute(student_query)
        student = student_result.scalar_one_or_none()
        
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        
        # Check which classes exist
        classes_query = select(ClassModel).where(ClassModel.id.in_(enrollment_data.class_ids))
        classes_result = await db.execute(classes_query)
        existing_classes = classes_result.scalars().all()
        existing_class_ids = [cls.id for cls in existing_classes]
        
        missing_class_ids = set(enrollment_data.class_ids) - set(existing_class_ids)
        if missing_class_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Classes not found: {list(missing_class_ids)}"
            )
        
        # Check existing enrollments
        existing_enrollments_query = select(StudentClass).where(
            and_(
                StudentClass.student_id == enrollment_data.student_id,
                StudentClass.class_id.in_(enrollment_data.class_ids)
            )
        )
        existing_enrollments_result = await db.execute(existing_enrollments_query)
        existing_enrollments = existing_enrollments_result.scalars().all()
        existing_enrollment_class_ids = [enrollment.class_id for enrollment in existing_enrollments]
        
        # Create only new enrollments
        new_class_ids = set(enrollment_data.class_ids) - set(existing_enrollment_class_ids)
        
        if not new_class_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student is already enrolled in all specified classes"
            )
        
        enrollments = []
        for class_id in new_class_ids:
            enrollment = StudentClass(
                student_id=enrollment_data.student_id,
                class_id=class_id
            )
            db.add(enrollment)
            enrollments.append(enrollment)
        
        await db.commit()
        for enrollment in enrollments:
            await db.refresh(enrollment)
        
        return enrollments
    
    @staticmethod
    async def bulk_enroll_multiple_students(
        db: AsyncSession, 
        enrollment_data: StudentClassBulkCreateMultiple
    ) -> List[StudentClass]:
        """Enroll multiple students in their respective classes."""
        enrollments = []
        
        for single_enrollment in enrollment_data.enrollments:
            try:
                enrollment = await StudentClassService.enroll_student_in_class(db, single_enrollment)
                enrollments.append(enrollment)
            except HTTPException as e:
                # Skip existing enrollments but raise other errors
                if e.status_code != status.HTTP_400_BAD_REQUEST:
                    raise e
        
        return enrollments
    
    @staticmethod
    async def get_all_enrollments(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        student_id: Optional[int] = None,
        class_id: Optional[int] = None
    ) -> List[StudentClass]:
        """Get student-class enrollments with optional filters."""
        query = select(StudentClass).options(
            selectinload(StudentClass.student),
            selectinload(StudentClass.class_obj)
        )
        
        if student_id:
            query = query.where(StudentClass.student_id == student_id)
        if class_id:
            query = query.where(StudentClass.class_id == class_id)
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_student_classes(db: AsyncSession, student_id: int) -> List[StudentClass]:
        """Get all classes for a specific student."""
        query = select(StudentClass).options(
            selectinload(StudentClass.class_obj)
        ).where(StudentClass.student_id == student_id)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_class_students(db: AsyncSession, class_id: int) -> List[StudentClass]:
        """Get all students in a specific class."""
        query = select(StudentClass).options(
            selectinload(StudentClass.student)
        ).where(StudentClass.class_id == class_id)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_students_list(db: AsyncSession) -> List[User]:
        """Get all users with student role."""
        query = select(User).where(User.role == UserRole.student)
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_classes_list(db: AsyncSession) -> List[ClassModel]:
        """Get all available classes."""
        query = select(ClassModel)
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def remove_student_from_class(db: AsyncSession, student_id: int, class_id: int) -> bool:
        """Remove a student from a class."""
        query = delete(StudentClass).where(
            and_(
                StudentClass.student_id == student_id,
                StudentClass.class_id == class_id
            )
        )
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0
    
    @staticmethod
    async def remove_enrollment_by_id(db: AsyncSession, enrollment_id: int) -> bool:
        """Remove enrollment by ID."""
        query = delete(StudentClass).where(StudentClass.id == enrollment_id)
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0
    
    @staticmethod
    async def remove_all_student_enrollments(db: AsyncSession, student_id: int) -> int:
        """Remove all class enrollments for a student."""
        query = delete(StudentClass).where(StudentClass.student_id == student_id)
        result = await db.execute(query)
        await db.commit()
        return result.rowcount
    
    @staticmethod
    async def remove_all_class_enrollments(db: AsyncSession, class_id: int) -> int:
        """Remove all student enrollments from a class."""
        query = delete(StudentClass).where(StudentClass.class_id == class_id)
        result = await db.execute(query)
        await db.commit()
        return result.rowcount
    
    @staticmethod
    async def get_enrollment_by_id(db: AsyncSession, enrollment_id: int) -> Optional[StudentClass]:
        """Get enrollment by ID."""
        query = select(StudentClass).options(
            selectinload(StudentClass.student),
            selectinload(StudentClass.class_obj)
        ).where(StudentClass.id == enrollment_id)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()