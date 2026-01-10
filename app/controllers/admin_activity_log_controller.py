from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime

from app.core.database import get_async_db
from app.core.auth import get_admin_user
from app.models.user import User
from app.models.admin_activity_log import ActionType, EntityType
from app.schemas.admin_activity_log import AdminActivityLogResponse
from app.services.admin_activity_log_service import AdminActivityLogService

router = APIRouter(prefix="/admin-activity-logs", tags=["admin-activity-logs"])

@router.get("/", response_model=List[AdminActivityLogResponse])
async def get_activity_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    admin_id: Optional[int] = Query(None),
    action: Optional[ActionType] = Query(None),
    entity_type: Optional[EntityType] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Get admin activity logs with filters.
    Admin only.
    """
    logs = await AdminActivityLogService.get_activity_logs(
        db,
        skip=skip,
        limit=limit,
        admin_id=admin_id,
        action=action,
        entity_type=entity_type,
        start_date=start_date,
        end_date=end_date
    )
    return logs

@router.get("/{log_id}", response_model=AdminActivityLogResponse)
async def get_activity_log_detail(
    log_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Get a specific activity log entry.
    Admin only.
    """
    log = await AdminActivityLogService.get_activity_log_by_id(db, log_id)
    
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity log not found"
        )
    
    return log
