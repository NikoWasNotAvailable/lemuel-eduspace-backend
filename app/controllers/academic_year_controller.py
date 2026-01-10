from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_async_db
from app.core.auth import get_admin_user, get_current_user
from app.models.user import User
from app.schemas.academic_year import (
    AcademicYearCreate,
    AcademicYearUpdate,
    AcademicYearResponse,
    UserAcademicHistoryResponse,
    UserAcademicYearsResponse,
    UserHistoryWithYearResponse
)
from app.services.academic_year_service import AcademicYearService
from app.services.admin_activity_log_service import AdminActivityLogService
from app.models.admin_activity_log import ActionType, EntityType

router = APIRouter(prefix="/academic-years", tags=["academic-years"])


# ========================
# Academic Year Endpoints
# ========================

@router.get("/", response_model=List[AcademicYearResponse])
async def get_academic_years(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get all academic years."""
    years = await AcademicYearService.get_academic_years(db)
    return years


@router.get("/current", response_model=AcademicYearResponse)
async def get_current_academic_year(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get the current academic year."""
    year = await AcademicYearService.get_current_academic_year(db)
    if not year:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No current academic year set"
        )
    return year


@router.post("/", response_model=AcademicYearResponse, status_code=status.HTTP_201_CREATED)
async def create_academic_year(
    data: AcademicYearCreate,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """Create a new academic year (admin only)."""
    year = await AcademicYearService.create_academic_year(db, data)
    
    # Log admin activity
    admin_name = request.headers.get("X-Admin-Name", current_user.name)
    await AdminActivityLogService.log_activity_by_name(
        db,
        admin_id=current_user.id,
        admin_name=admin_name,
        action=ActionType.create,
        entity_type=EntityType.academic_year,  # Using promotion as closest entity type
        entity_id=year.id,
        entity_name=year.name,
        details={"type": "academic_year", "is_current": year.is_current},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent")
    )
    
    return year


@router.get("/{year_id}", response_model=AcademicYearResponse)
async def get_academic_year(
    year_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get an academic year by ID."""
    year = await AcademicYearService.get_academic_year_by_id(db, year_id)
    if not year:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic year not found"
        )
    return year


@router.put("/{year_id}", response_model=AcademicYearResponse)
async def update_academic_year(
    year_id: int,
    data: AcademicYearUpdate,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """Update an academic year (admin only)."""
    year = await AcademicYearService.update_academic_year(db, year_id, data)
    if not year:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic year not found"
        )
    
    # Log admin activity
    admin_name = request.headers.get("X-Admin-Name", current_user.name)
    await AdminActivityLogService.log_activity_by_name(
        db,
        admin_id=current_user.id,
        admin_name=admin_name,
        action=ActionType.update,
        entity_type=EntityType.academic_year,
        entity_id=year.id,
        entity_name=year.name,
        details={"type": "academic_year", "updated_fields": list(data.dict(exclude_unset=True).keys())},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent")
    )
    
    return year


@router.post("/{year_id}/set-current", response_model=AcademicYearResponse)
async def set_current_academic_year(
    year_id: int,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """Set an academic year as the current one (admin only)."""
    year = await AcademicYearService.set_current_academic_year(db, year_id)
    if not year:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic year not found"
        )
    
    # Log admin activity
    admin_name = request.headers.get("X-Admin-Name", current_user.name)
    await AdminActivityLogService.log_activity_by_name(
        db,
        admin_id=current_user.id,
        admin_name=admin_name,
        action=ActionType.update,
        entity_type=EntityType.academic_year,
        entity_id=year.id,
        entity_name=year.name,
        details={"type": "academic_year", "action": "set_as_current"},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent")
    )
    
    return year


@router.delete("/{year_id}")
async def delete_academic_year(
    year_id: int,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """Delete an academic year (admin only)."""
    # Get year info before deletion
    year = await AcademicYearService.get_academic_year_by_id(db, year_id)
    if not year:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic year not found"
        )
    
    year_name = year.name
    
    success = await AcademicYearService.delete_academic_year(db, year_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic year not found"
        )
    
    # Log admin activity
    admin_name = request.headers.get("X-Admin-Name", current_user.name)
    await AdminActivityLogService.log_activity_by_name(
        db,
        admin_id=current_user.id,
        admin_name=admin_name,
        action=ActionType.delete,
        entity_type=EntityType.academic_year,
        entity_id=year_id,
        entity_name=year_name,
        details={"type": "academic_year"},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent")
    )
    
    return {"message": "Academic year deleted successfully"}


# ========================
# Snapshot Endpoint
# ========================

@router.post("/snapshot", status_code=status.HTTP_201_CREATED)
async def snapshot_users_for_current_year(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Snapshot all active users' current grade/class to the current academic year.
    Should be run at the start of each academic year to preserve history.
    (admin only)
    """
    count = await AcademicYearService.snapshot_all_users_for_current_year(db)
    
    if count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No current academic year set or no users to snapshot"
        )
    
    # Log admin activity
    admin_name = request.headers.get("X-Admin-Name", current_user.name)
    await AdminActivityLogService.log_activity_by_name(
        db,
        admin_id=current_user.id,
        admin_name=admin_name,
        action=ActionType.create,
        entity_type=EntityType.academic_year,
        entity_id=None,
        entity_name="User History Snapshot",
        details={"type": "snapshot", "users_snapshotted": count},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent")
    )
    
    return {"message": f"Successfully snapshotted {count} users for current academic year"}


# ========================
# User History Endpoints
# ========================

@router.get("/me/history", response_model=List[UserHistoryWithYearResponse])
async def get_my_academic_history(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get the current user's academic history across all years."""
    histories = await AcademicYearService.get_user_academic_history(db, current_user.id)
    
    result = []
    for h in histories:
        result.append(UserHistoryWithYearResponse(
            id=h.id,
            academic_year=AcademicYearResponse.model_validate(h.academic_year),
            grade=h.grade.value if h.grade else None,
            class_id=h.class_id,
            class_name=h.class_obj.name if h.class_obj else None,
            role=h.role.value if h.role else None
        ))
    
    return result


@router.get("/users/{user_id}/history", response_model=List[UserHistoryWithYearResponse])
async def get_user_academic_history(
    user_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a user's academic history across all years.
    Students can only view their own history.
    Teachers and admins can view any user's history.
    """
    # Check permissions
    if current_user.role == "student" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students can only view their own academic history"
        )
    
    histories = await AcademicYearService.get_user_academic_history(db, user_id)
    
    result = []
    for h in histories:
        result.append(UserHistoryWithYearResponse(
            id=h.id,
            academic_year=AcademicYearResponse.model_validate(h.academic_year),
            grade=h.grade.value if h.grade else None,
            class_id=h.class_id,
            class_name=h.class_obj.name if h.class_obj else None,
            role=h.role.value if h.role else None
        ))
    
    return result


@router.get("/users/{user_id}/history/{year_id}", response_model=UserHistoryWithYearResponse)
async def get_user_history_for_year(
    user_id: int,
    year_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a user's history for a specific academic year.
    Students can only view their own history.
    """
    # Check permissions
    if current_user.role == "student" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students can only view their own academic history"
        )
    
    history = await AcademicYearService.get_user_history_for_year(db, user_id, year_id)
    
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No history found for this user and academic year"
        )
    
    return UserHistoryWithYearResponse(
        id=history.id,
        academic_year=AcademicYearResponse.model_validate(history.academic_year),
        grade=history.grade.value if history.grade else None,
        class_id=history.class_id,
        class_name=history.class_obj.name if history.class_obj else None,
        role=history.role.value if history.role else None
    )
