from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.core.auth import get_current_user, get_admin_user, get_teacher_or_admin_user
from app.services.notification_service import NotificationService
from app.schemas.notification import (
    NotificationCreate,
    NotificationUpdate,
    NotificationBulkCreate,
    NotificationResponse,
    NotificationListResponse,
    BulkOperationResponse,
    NotificationStatsResponse
)
from app.models.notification import NotificationType
from app.models.user import User
from datetime import datetime, timedelta
import math

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.post("/", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def create_notification(
    notification_data: NotificationCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_teacher_or_admin_user)
):
    """Create a new notification (teacher or admin)."""
    notification = await NotificationService.create_notification(db, notification_data)
    return NotificationResponse.model_validate(notification)

@router.post("/bulk", response_model=BulkOperationResponse, status_code=status.HTTP_201_CREATED)
async def bulk_create_notifications(
    bulk_data: NotificationBulkCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_teacher_or_admin_user)
):
    """Create multiple notifications at once (teacher or admin)."""
    notifications = await NotificationService.bulk_create_notifications(db, bulk_data)
    
    return BulkOperationResponse(
        success=True,
        count=len(notifications),
        message=f"Successfully created {len(notifications)} notifications",
        created_ids=[notif.id for notif in notifications]
    )

@router.get("/", response_model=NotificationListResponse)
async def get_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type: Optional[NotificationType] = Query(None, description="Filter by notification type"),
    search: Optional[str] = Query(None, description="Search in title and subject"),
    start_date: Optional[datetime] = Query(None, description="Filter from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter to this date"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get notifications with pagination and filters."""
    skip = (page - 1) * page_size
    
    notifications, total = await NotificationService.get_all_notifications(
        db, skip=skip, limit=page_size, notification_type=type,
        search=search, start_date=start_date, end_date=end_date
    )
    
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    
    return NotificationListResponse(
        notifications=[NotificationResponse.model_validate(notif) for notif in notifications],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.get("/latest", response_model=List[NotificationResponse])
async def get_latest_notifications(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get the latest notifications."""
    notifications = await NotificationService.get_latest_notifications(db, limit)
    return [NotificationResponse.model_validate(notif) for notif in notifications]

@router.get("/by-type/{notification_type}", response_model=List[NotificationResponse])
async def get_notifications_by_type(
    notification_type: NotificationType,
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get notifications by type."""
    notifications = await NotificationService.get_notifications_by_type(db, notification_type, limit)
    return [NotificationResponse.model_validate(notif) for notif in notifications]

@router.get("/search", response_model=List[NotificationResponse])
async def search_notifications(
    q: str = Query(..., min_length=2, description="Search term"),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Search notifications by title and subject."""
    notifications = await NotificationService.search_notifications(db, q, limit)
    return [NotificationResponse.model_validate(notif) for notif in notifications]

@router.get("/stats", response_model=NotificationStatsResponse)
async def get_notification_stats(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_teacher_or_admin_user)
):
    """Get notification statistics (teacher or admin)."""
    stats = await NotificationService.get_notification_stats(db)
    
    latest_notification = None
    if stats["latest_notification"]:
        latest_notification = NotificationResponse.model_validate(stats["latest_notification"])
    
    return NotificationStatsResponse(
        total_notifications=stats["total_notifications"],
        by_type=stats["by_type"],
        latest_notification=latest_notification,
        today_count=stats["today_count"]
    )

@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific notification by ID."""
    notification = await NotificationService.get_notification_by_id(db, notification_id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    return NotificationResponse.model_validate(notification)

@router.put("/{notification_id}", response_model=NotificationResponse)
async def update_notification(
    notification_id: int,
    notification_update: NotificationUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """Update a notification (admin only)."""
    updated_notification = await NotificationService.update_notification(
        db, notification_id, notification_update
    )
    if not updated_notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    return NotificationResponse.model_validate(updated_notification)

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """Delete a notification (admin only)."""
    success = await NotificationService.delete_notification(db, notification_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    return {"message": "Notification deleted successfully"}

@router.delete("/by-type/{notification_type}")
async def delete_notifications_by_type(
    notification_type: NotificationType,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """Delete all notifications of a specific type (admin only)."""
    count = await NotificationService.delete_notifications_by_type(db, notification_type)
    return {"message": f"Deleted {count} notifications of type '{notification_type}'"}

@router.delete("/cleanup/old")
async def cleanup_old_notifications(
    days_old: int = Query(30, ge=1, description="Delete notifications older than this many days"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """Delete notifications older than specified days (admin only)."""
    cutoff_date = datetime.now() - timedelta(days=days_old)
    count = await NotificationService.delete_old_notifications(db, cutoff_date)
    return {"message": f"Deleted {count} notifications older than {days_old} days"}