from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.orm import joinedload
from datetime import date
import logging

from app.models.academic_year import AcademicYear
from app.models.user_academic_history import UserAcademicHistory
from app.models.user import User, UserRole, UserGrade
from app.models.classroom import ClassModel
from app.schemas.academic_year import AcademicYearCreate, AcademicYearUpdate

logger = logging.getLogger(__name__)


class AcademicYearService:
    """Service for managing academic years and user academic history."""
    
    # ========================
    # Academic Year CRUD
    # ========================
    
    @staticmethod
    async def create_academic_year(
        db: AsyncSession, 
        data: AcademicYearCreate
    ) -> AcademicYear:
        """Create a new academic year."""
        # If this is set as current, unset others
        if data.is_current:
            await db.execute(
                update(AcademicYear).values(is_current=False)
            )
        
        academic_year = AcademicYear(
            name=data.name,
            start_date=data.start_date,
            end_date=data.end_date,
            is_current=data.is_current
        )
        
        db.add(academic_year)
        await db.commit()
        await db.refresh(academic_year)
        
        logger.info(f"Created academic year: {academic_year.name}")
        return academic_year
    
    @staticmethod
    async def get_academic_years(db: AsyncSession) -> List[AcademicYear]:
        """Get all academic years ordered by start date descending."""
        result = await db.execute(
            select(AcademicYear).order_by(AcademicYear.start_date.desc())
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_academic_year_by_id(
        db: AsyncSession, 
        year_id: int
    ) -> Optional[AcademicYear]:
        """Get an academic year by ID."""
        result = await db.execute(
            select(AcademicYear).where(AcademicYear.id == year_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_current_academic_year(db: AsyncSession) -> Optional[AcademicYear]:
        """Get the current academic year."""
        result = await db.execute(
            select(AcademicYear).where(AcademicYear.is_current == True)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_academic_year(
        db: AsyncSession,
        year_id: int,
        data: AcademicYearUpdate
    ) -> Optional[AcademicYear]:
        """Update an academic year."""
        academic_year = await AcademicYearService.get_academic_year_by_id(db, year_id)
        if not academic_year:
            return None
        
        # If setting as current, unset others first
        if data.is_current:
            await db.execute(
                update(AcademicYear).where(AcademicYear.id != year_id).values(is_current=False)
            )
        
        update_data = data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(academic_year, field, value)
        
        await db.commit()
        await db.refresh(academic_year)
        return academic_year
    
    @staticmethod
    async def set_current_academic_year(
        db: AsyncSession,
        year_id: int
    ) -> Optional[AcademicYear]:
        """Set an academic year as the current one."""
        # Unset all others
        await db.execute(
            update(AcademicYear).values(is_current=False)
        )
        
        # Set the specified one
        academic_year = await AcademicYearService.get_academic_year_by_id(db, year_id)
        if academic_year:
            academic_year.is_current = True
            await db.commit()
            await db.refresh(academic_year)
        
        return academic_year
    
    @staticmethod
    async def delete_academic_year(db: AsyncSession, year_id: int) -> bool:
        """Delete an academic year (cascades to history records)."""
        academic_year = await AcademicYearService.get_academic_year_by_id(db, year_id)
        if not academic_year:
            return False
        
        await db.delete(academic_year)
        await db.commit()
        return True
    
    # ========================
    # User Academic History
    # ========================
    
    @staticmethod
    async def save_user_history_for_year(
        db: AsyncSession,
        user_id: int,
        academic_year_id: int,
        grade: Optional[UserGrade] = None,
        class_id: Optional[int] = None,
        role: UserRole = UserRole.student
    ) -> UserAcademicHistory:
        """
        Save a user's grade/class for a specific academic year.
        Updates if already exists, creates if not.
        """
        # Check if record exists
        result = await db.execute(
            select(UserAcademicHistory).where(
                and_(
                    UserAcademicHistory.user_id == user_id,
                    UserAcademicHistory.academic_year_id == academic_year_id
                )
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            existing.grade = grade
            existing.class_id = class_id
            existing.role = role
            await db.commit()
            await db.refresh(existing)
            return existing
        
        # Create new
        history = UserAcademicHistory(
            user_id=user_id,
            academic_year_id=academic_year_id,
            grade=grade,
            class_id=class_id,
            role=role
        )
        db.add(history)
        await db.commit()
        await db.refresh(history)
        return history
    
    @staticmethod
    async def snapshot_all_users_for_current_year(db: AsyncSession) -> int:
        """
        Snapshot all active users' current grade/class to the current academic year.
        Returns the number of records created/updated.
        """
        current_year = await AcademicYearService.get_current_academic_year(db)
        if not current_year:
            logger.warning("No current academic year set, cannot snapshot")
            return 0
        
        # Get all active users (students and teachers)
        result = await db.execute(
            select(User).where(
                User.role.in_([UserRole.student, UserRole.teacher]),
                User.status == "active"
            )
        )
        users = result.scalars().all()
        
        count = 0
        for user in users:
            await AcademicYearService.save_user_history_for_year(
                db,
                user_id=user.id,
                academic_year_id=current_year.id,
                grade=user.grade,
                class_id=user.class_id,
                role=user.role
            )
            count += 1
        
        logger.info(f"Snapshotted {count} users for academic year {current_year.name}")
        return count
    
    @staticmethod
    async def get_user_academic_history(
        db: AsyncSession,
        user_id: int
    ) -> List[UserAcademicHistory]:
        """Get all academic history records for a user."""
        result = await db.execute(
            select(UserAcademicHistory)
            .options(
                joinedload(UserAcademicHistory.academic_year),
                joinedload(UserAcademicHistory.class_obj)
            )
            .where(UserAcademicHistory.user_id == user_id)
            .order_by(UserAcademicHistory.academic_year_id.desc())
        )
        return result.scalars().unique().all()
    
    @staticmethod
    async def get_user_history_for_year(
        db: AsyncSession,
        user_id: int,
        academic_year_id: int
    ) -> Optional[UserAcademicHistory]:
        """Get a user's history for a specific academic year."""
        result = await db.execute(
            select(UserAcademicHistory)
            .options(
                joinedload(UserAcademicHistory.academic_year),
                joinedload(UserAcademicHistory.class_obj)
            )
            .where(
                and_(
                    UserAcademicHistory.user_id == user_id,
                    UserAcademicHistory.academic_year_id == academic_year_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_users_by_academic_year_and_class(
        db: AsyncSession,
        academic_year_id: int,
        class_id: int
    ) -> List[UserAcademicHistory]:
        """Get all users who were in a specific class during an academic year."""
        result = await db.execute(
            select(UserAcademicHistory)
            .options(joinedload(UserAcademicHistory.user))
            .where(
                and_(
                    UserAcademicHistory.academic_year_id == academic_year_id,
                    UserAcademicHistory.class_id == class_id
                )
            )
        )
        return result.scalars().unique().all()
