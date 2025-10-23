from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import date

from app.core.database import get_async_db
from app.core.auth import get_current_user, require_roles
from app.models.user import User, UserRole
from app.services.session_service import SessionService
from app.schemas.session import (
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    SessionWithSubjectResponse,
    SessionListResponse,
    SessionStatsResponse
)

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: SessionCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_roles([UserRole.admin, UserRole.teacher]))
):
    """Create a new session. Only admin and teachers can create sessions."""
    return await SessionService.create_session(db, session_data)

@router.get("/", response_model=SessionListResponse)
async def get_sessions(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    subject_id: Optional[int] = Query(None, description="Filter by subject ID"),
    class_id: Optional[int] = Query(None, description="Filter by class ID"),
    date_from: Optional[date] = Query(None, description="Filter sessions from this date"),
    date_to: Optional[date] = Query(None, description="Filter sessions until this date"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get all sessions with optional filters and pagination."""
    sessions, total = await SessionService.get_sessions(
        db, skip, limit, subject_id, class_id, date_from, date_to
    )
    
    total_pages = (total + limit - 1) // limit
    
    return SessionListResponse(
        sessions=sessions,
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        total_pages=total_pages
    )

@router.get("/upcoming", response_model=List[SessionWithSubjectResponse])
async def get_upcoming_sessions(
    limit: int = Query(10, ge=1, le=50, description="Number of upcoming sessions to return"),
    subject_id: Optional[int] = Query(None, description="Filter by subject ID"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get upcoming sessions (today and future)."""
    sessions = await SessionService.get_upcoming_sessions(db, limit, subject_id)
    
    # Transform to include subject and class names
    result = []
    for session in sessions:
        session_dict = {
            "id": session.id,
            "subject_id": session.subject_id,
            "session_no": session.session_no,
            "date": session.date,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "subject_name": session.subject.name if session.subject else None,
            "class_name": session.subject.class_obj.name if session.subject and session.subject.class_obj else None
        }
        result.append(SessionWithSubjectResponse(**session_dict))
    
    return result

@router.get("/stats", response_model=SessionStatsResponse)
async def get_session_stats(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_roles([UserRole.admin, UserRole.teacher]))
):
    """Get session statistics. Only admin and teachers can access statistics."""
    stats = await SessionService.get_session_stats(db)
    return SessionStatsResponse(**stats)

@router.get("/subject/{subject_id}", response_model=SessionListResponse)
async def get_sessions_by_subject(
    subject_id: int,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get all sessions for a specific subject."""
    sessions, total = await SessionService.get_sessions_by_subject(db, subject_id, skip, limit)
    
    total_pages = (total + limit - 1) // limit
    
    return SessionListResponse(
        sessions=sessions,
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        total_pages=total_pages
    )

@router.get("/subject/{subject_id}/next-number", response_model=dict)
async def get_next_session_number(
    subject_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_roles([UserRole.admin, UserRole.teacher]))
):
    """Get the next available session number for a subject."""
    next_number = await SessionService.get_next_session_number(db, subject_id)
    return {"subject_id": subject_id, "next_session_number": next_number}

@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get session by ID."""
    session = await SessionService.get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return session

@router.get("/{session_id}/attachments")
async def get_session_attachments(
    session_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get session attachments separately to avoid circular reference."""
    session = await SessionService.get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Return just the attachments as a simple list
    attachments = []
    for attachment in session.attachments:
        attachments.append({
            "id": attachment.id,
            "filename": attachment.filename,
            "file_size": attachment.file_size,
            "content_type": attachment.content_type,
            "created_at": attachment.created_at.isoformat(),
            "uploaded_by": attachment.uploaded_by
        })
    
    return {"session_id": session_id, "attachments": attachments}

@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: int,
    session_update: SessionUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_roles([UserRole.admin, UserRole.teacher]))
):
    """Update session information. Only admin and teachers can update sessions."""
    session = await SessionService.update_session(db, session_id, session_update)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return session

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_roles([UserRole.admin, UserRole.teacher]))
):
    """Delete session. Only admin and teachers can delete sessions."""
    deleted = await SessionService.delete_session(db, session_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return None