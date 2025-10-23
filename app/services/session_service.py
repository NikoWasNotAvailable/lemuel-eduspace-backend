from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, func, and_, desc
from sqlalchemy.orm import selectinload, joinedload
from app.models.session import Session
from app.models.subject import Subject
from app.models.classroom import ClassModel
from app.schemas.session import SessionCreate, SessionUpdate
from fastapi import HTTPException, status
from datetime import datetime, date
from sqlalchemy.exc import IntegrityError

class SessionService:
    
    @staticmethod
    async def create_session(db: AsyncSession, session_data: SessionCreate) -> Session:
        """Create a new session."""
        # First check if the subject exists
        subject_result = await db.execute(select(Subject).where(Subject.id == session_data.subject_id))
        subject = subject_result.scalar_one_or_none()
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found"
            )
        
        try:
            session = Session(
                subject_id=session_data.subject_id,
                session_no=session_data.session_no,
                date=session_data.date
            )
            
            db.add(session)
            await db.commit()
            await db.refresh(session)
            return session
        
        except IntegrityError as e:
            await db.rollback()
            if "unique_subject_session_no" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Session number already exists for this subject"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Session creation failed"
                )
    
    @staticmethod
    async def get_session_by_id(db: AsyncSession, session_id: int) -> Optional[Session]:
        """Get session by ID with subject and class information."""
        query = select(Session).options(
            joinedload(Session.subject).joinedload(Subject.class_obj),
            selectinload(Session.attachments)
        ).where(Session.id == session_id)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_sessions(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        subject_id: Optional[int] = None,
        class_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> Tuple[List[Session], int]:
        """Get sessions with optional filters and pagination."""
        query = select(Session).options(
            joinedload(Session.subject).joinedload(Subject.class_obj)
        )
        
        # Apply filters
        conditions = []
        
        if subject_id:
            conditions.append(Session.subject_id == subject_id)
        
        if class_id:
            # Join with Subject to filter by class_id
            query = query.join(Subject)
            conditions.append(Subject.class_id == class_id)
        
        if date_from:
            conditions.append(Session.date >= date_from)
        
        if date_to:
            conditions.append(Session.date <= date_to)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Count total
        count_query = select(func.count(Session.id))
        if conditions:
            if class_id:
                count_query = count_query.select_from(Session).join(Subject)
            count_query = count_query.where(and_(*conditions))
        
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination and ordering
        query = query.order_by(Session.date.desc(), Session.session_no.asc()).offset(skip).limit(limit)
        
        result = await db.execute(query)
        sessions = result.scalars().all()
        
        return sessions, total
    
    @staticmethod
    async def get_sessions_by_subject(
        db: AsyncSession, 
        subject_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Session], int]:
        """Get all sessions for a specific subject."""
        # Check if subject exists
        subject_result = await db.execute(select(Subject).where(Subject.id == subject_id))
        subject = subject_result.scalar_one_or_none()
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found"
            )
        
        return await SessionService.get_sessions(db, skip, limit, subject_id=subject_id)
    
    @staticmethod
    async def get_upcoming_sessions(
        db: AsyncSession,
        limit: int = 10,
        subject_id: Optional[int] = None
    ) -> List[Session]:
        """Get upcoming sessions (today and future)."""
        today = date.today()
        
        query = select(Session).options(
            joinedload(Session.subject).joinedload(Subject.class_obj)
        ).where(Session.date >= today)
        
        if subject_id:
            query = query.where(Session.subject_id == subject_id)
        
        query = query.order_by(Session.date.asc(), Session.session_no.asc()).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def update_session(
        db: AsyncSession,
        session_id: int,
        session_update: SessionUpdate
    ) -> Optional[Session]:
        """Update session information."""
        session = await SessionService.get_session_by_id(db, session_id)
        if not session:
            return None
        
        # If subject_id is being updated, check if the new subject exists
        if session_update.subject_id and session_update.subject_id != session.subject_id:
            subject_result = await db.execute(select(Subject).where(Subject.id == session_update.subject_id))
            subject = subject_result.scalar_one_or_none()
            if not subject:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Target subject not found"
                )
        
        # Update fields
        update_data = session_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(session, field, value)
        
        try:
            await db.commit()
            await db.refresh(session)
            return session
        except IntegrityError as e:
            await db.rollback()
            if "unique_subject_session_no" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Session number already exists for this subject"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Session update failed"
                )
    
    @staticmethod
    async def delete_session(db: AsyncSession, session_id: int) -> bool:
        """Delete session and all its attachments."""
        session = await SessionService.get_session_by_id(db, session_id)
        if not session:
            return False
        
        await db.delete(session)
        await db.commit()
        return True
    
    @staticmethod
    async def get_session_stats(db: AsyncSession) -> dict:
        """Get session statistics."""
        # Total sessions
        total_result = await db.execute(select(func.count(Session.id)))
        total_sessions = total_result.scalar()
        
        # Sessions by subject
        sessions_by_subject_result = await db.execute(
            select(Subject.name, func.count(Session.id))
            .join(Session)
            .group_by(Subject.name)
            .order_by(func.count(Session.id).desc())
        )
        sessions_by_subject = dict(sessions_by_subject_result.fetchall())
        
        # Upcoming sessions count
        today = date.today()
        upcoming_result = await db.execute(
            select(func.count(Session.id)).where(Session.date >= today)
        )
        upcoming_sessions = upcoming_result.scalar()
        
        # Sessions today
        today_result = await db.execute(
            select(func.count(Session.id)).where(Session.date == today)
        )
        sessions_today = today_result.scalar()
        
        return {
            "total_sessions": total_sessions,
            "sessions_by_subject": sessions_by_subject,
            "upcoming_sessions": upcoming_sessions,
            "sessions_today": sessions_today
        }
    
    @staticmethod
    async def get_next_session_number(db: AsyncSession, subject_id: int) -> int:
        """Get the next available session number for a subject."""
        # Check if subject exists
        subject_result = await db.execute(select(Subject).where(Subject.id == subject_id))
        subject = subject_result.scalar_one_or_none()
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found"
            )
        
        # Get the highest session number for this subject
        result = await db.execute(
            select(func.max(Session.session_no))
            .where(Session.subject_id == subject_id)
        )
        max_session_no = result.scalar()
        
        return (max_session_no or 0) + 1