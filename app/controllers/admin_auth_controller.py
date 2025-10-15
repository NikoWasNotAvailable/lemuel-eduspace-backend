from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.core.auth import get_current_user, get_admin_user
from app.services.admin_auth_service import AdminAuthService
from app.schemas.admin_auth import (
    AdminLoginRequest,
    AdminLoginResponse,
    AdminLogoutRequest,
    AdminLoginLogResponse
)
from app.models.user import User
from datetime import datetime

router = APIRouter(prefix="/admin-auth", tags=["admin-authentication"])

@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(
    login_data: AdminLoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Admin login with name tracking and session logging."""
    
    admin_user, login_log = await AdminAuthService.authenticate_admin(db, login_data, request)
    
    return AdminLoginResponse(
        access_token=login_log.session_token,
        token_type="bearer",
        admin_user_id=admin_user.id,
        admin_name=login_data.name,
        login_time=login_log.login_time,
        session_id=login_log.id
    )

@router.post("/logout")
async def admin_logout(
    logout_data: AdminLogoutRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """Admin logout - updates logout time in log."""
    
    success = await AdminAuthService.logout_admin(db, logout_data)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return {"message": "Successfully logged out", "session_id": logout_data.session_id}

@router.get("/logs", response_model=List[AdminLoginLogResponse])
async def get_admin_login_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    admin_user_id: Optional[int] = Query(None, description="Filter by admin user ID"),
    admin_name: Optional[str] = Query(None, description="Filter by admin name"),
    start_date: Optional[datetime] = Query(None, description="Filter from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter to this date"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """Get admin login logs (admin only)."""
    
    logs = await AdminAuthService.get_admin_login_logs(
        db, skip=skip, limit=limit, admin_user_id=admin_user_id,
        admin_name=admin_name, start_date=start_date, end_date=end_date
    )
    
    return [AdminLoginLogResponse.model_validate(log) for log in logs]

@router.get("/active-sessions", response_model=List[AdminLoginLogResponse])
async def get_active_admin_sessions(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """Get currently active admin sessions (admin only)."""
    
    sessions = await AdminAuthService.get_active_admin_sessions(db)
    
    return [AdminLoginLogResponse.model_validate(session) for session in sessions]

@router.post("/force-logout/{session_id}")
async def force_logout_admin_session(
    session_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """Force logout a specific admin session (admin only)."""
    
    success = await AdminAuthService.force_logout_session(db, session_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return {"message": f"Session {session_id} forcefully logged out"}

@router.get("/verify-session")
async def verify_admin_session(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """Verify current admin session is still active."""
    
    return {
        "message": "Session is active",
        "admin_id": current_user.id,
        "admin_email": current_user.email
    }