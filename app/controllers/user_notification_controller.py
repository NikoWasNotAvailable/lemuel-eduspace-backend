from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.core.auth import get_current_user, get_admin_user, get_teacher_or_admin_user
from app.services.user_notification_service import UserNotificationService
from app.schemas.user_notification import (
    UserNotificationCreate,
    UserNotificationBulkCreate,
    UserNotificationMarkRead,
    UserNotificationAssignByRole,
    UserNotificationResponse,
    UserNotificationWithDetailsResponse,
    UserNotificationForUserResponse,
    NotificationWithReadStatusResponse,
    UserNotificationStatsResponse,
    BulkAssignmentResponse,
    BulkReadResponse
)
from app.schemas.notification import NotificationResponse
from app.models.notification import NotificationType
from app.models.user import User
import math

router = APIRouter(prefix="/user-notifications", tags=["user-notifications"])

@router.post("/assign", response_model=BulkAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def assign_notification_to_users(
    assignment_data: UserNotificationCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_teacher_or_admin_user)
):
    """Assign a notification to multiple users (teacher or admin)."""
    assignments, skipped_count = await UserNotificationService.assign_notification_to_users(
        db, assignment_data
    )
    
    return BulkAssignmentResponse(
        success=True,
        assigned_count=len(assignments),
        skipped_count=skipped_count,
        message=f"Assigned notification to {len(assignments)} users, {skipped_count} already assigned",
        assignment_ids=[assignment.id for assignment in assignments]
    )

@router.post("/bulk-assign", response_model=BulkAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def bulk_assign_notifications_to_users(
    bulk_data: UserNotificationBulkCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_teacher_or_admin_user)
):
    """Assign multiple notifications to multiple users (teacher or admin)."""
    assignments, skipped_count = await UserNotificationService.bulk_assign_notifications_to_users(
        db, bulk_data
    )
    
    return BulkAssignmentResponse(
        success=True,
        assigned_count=len(assignments),
        skipped_count=skipped_count,
        message=f"Created {len(assignments)} assignments, {skipped_count} already existed",
        assignment_ids=[assignment.id for assignment in assignments]
    )

@router.post("/assign-by-role", response_model=BulkAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def assign_notification_by_role(
    assignment_data: UserNotificationAssignByRole,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_teacher_or_admin_user)
):
    """Assign a notification to all users with specific roles (teacher or admin)."""
    assignments, skipped_count = await UserNotificationService.assign_notification_by_role(
        db, assignment_data
    )
    
    return BulkAssignmentResponse(
        success=True,
        assigned_count=len(assignments),
        skipped_count=skipped_count,
        message=f"Assigned to {len(assignments)} users with roles {assignment_data.roles}, {skipped_count} already assigned",
        assignment_ids=[assignment.id for assignment in assignments]
    )

@router.get("/my-notifications", response_model=List[NotificationWithReadStatusResponse])
async def get_my_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False, description="Show only unread notifications"),
    type: Optional[NotificationType] = Query(None, description="Filter by notification type"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get notifications for the current user."""
    skip = (page - 1) * page_size
    
    user_notifications, total = await UserNotificationService.get_user_notifications(
        db, current_user.id, skip=skip, limit=page_size, 
        unread_only=unread_only, notification_type=type
    )
    
    response = []
    for user_notif in user_notifications:
        response.append(NotificationWithReadStatusResponse(
            notification=NotificationResponse.model_validate(user_notif.notification),
            is_read=user_notif.is_read,
            read_at=user_notif.read_at,
            user_notification_id=user_notif.id
        ))
    
    return response

@router.get("/user/{user_id}", response_model=List[UserNotificationForUserResponse])
async def get_user_notifications(
    user_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False, description="Show only unread notifications"),
    type: Optional[NotificationType] = Query(None, description="Filter by notification type"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_teacher_or_admin_user)
):
    """Get notifications for a specific user (teacher or admin)."""
    skip = (page - 1) * page_size
    
    user_notifications, total = await UserNotificationService.get_user_notifications(
        db, user_id, skip=skip, limit=page_size, 
        unread_only=unread_only, notification_type=type
    )
    
    return [UserNotificationForUserResponse.model_validate(user_notif) for user_notif in user_notifications]

@router.get("/notification/{notification_id}/recipients", response_model=List[UserNotificationWithDetailsResponse])
async def get_notification_recipients(
    notification_id: int,
    read_status: Optional[bool] = Query(None, description="Filter by read status"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_teacher_or_admin_user)
):
    """Get all users who received a specific notification (teacher or admin)."""
    recipients = await UserNotificationService.get_notification_recipients(
        db, notification_id, read_status
    )
    
    response = []
    for recipient in recipients:
        response.append(UserNotificationWithDetailsResponse(
            id=recipient.id,
            user_id=recipient.user_id,
            notification_id=recipient.notification_id,
            is_read=recipient.is_read,
            read_at=recipient.read_at,
            notification=NotificationResponse.model_validate(recipient.notification),
            user_name=recipient.user.name if recipient.user else None
        ))
    
    return response

@router.post("/mark-read", response_model=BulkReadResponse)
async def mark_notifications_as_read(
    read_data: UserNotificationMarkRead,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Mark specific notifications as read for current user."""
    marked_read, already_read = await UserNotificationService.mark_notifications_as_read(
        db, current_user.id, read_data
    )
    
    return BulkReadResponse(
        success=True,
        marked_read_count=marked_read,
        already_read_count=already_read,
        message=f"Marked {marked_read} notifications as read, {already_read} were already read"
    )

@router.post("/mark-all-read")
async def mark_all_notifications_as_read(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Mark all notifications as read for current user."""
    count = await UserNotificationService.mark_all_as_read(db, current_user.id)
    return {"message": f"Marked {count} notifications as read"}

@router.get("/my-stats", response_model=UserNotificationStatsResponse)
async def get_my_notification_stats(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get notification statistics for current user."""
    stats = await UserNotificationService.get_user_notification_stats(db, current_user.id)
    
    latest_unread = None
    if stats["latest_unread"]:
        latest_unread = NotificationWithReadStatusResponse(
            notification=NotificationResponse.model_validate(stats["latest_unread"].notification),
            is_read=stats["latest_unread"].is_read,
            read_at=stats["latest_unread"].read_at,
            user_notification_id=stats["latest_unread"].id
        )
    
    return UserNotificationStatsResponse(
        total_notifications=stats["total_notifications"],
        unread_count=stats["unread_count"],
        read_count=stats["read_count"],
        unread_by_type=stats["unread_by_type"],
        latest_unread=latest_unread
    )

@router.get("/user/{user_id}/stats", response_model=UserNotificationStatsResponse)
async def get_user_notification_stats(
    user_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_teacher_or_admin_user)
):
    """Get notification statistics for a specific user (teacher or admin)."""
    stats = await UserNotificationService.get_user_notification_stats(db, user_id)
    
    latest_unread = None
    if stats["latest_unread"]:
        latest_unread = NotificationWithReadStatusResponse(
            notification=NotificationResponse.model_validate(stats["latest_unread"].notification),
            is_read=stats["latest_unread"].is_read,
            read_at=stats["latest_unread"].read_at,
            user_notification_id=stats["latest_unread"].id
        )
    
    return UserNotificationStatsResponse(
        total_notifications=stats["total_notifications"],
        unread_count=stats["unread_count"],
        read_count=stats["read_count"],
        unread_by_type=stats["unread_by_type"],
        latest_unread=latest_unread
    )

@router.delete("/remove/{notification_id}")
async def remove_notification_from_user(
    notification_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a notification assignment from current user."""
    success = await UserNotificationService.delete_user_notification(
        db, current_user.id, notification_id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification assignment not found"
        )
    return {"message": "Notification removed successfully"}

@router.delete("/user/{user_id}/notification/{notification_id}")
async def remove_notification_from_specific_user(
    user_id: int,
    notification_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """Remove a notification assignment from a specific user (admin only)."""
    success = await UserNotificationService.delete_user_notification(
        db, user_id, notification_id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification assignment not found"
        )
    return {"message": "Notification removed from user successfully"}

@router.delete("/user/{user_id}/all")
async def remove_all_notifications_from_user(
    user_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """Remove all notification assignments from a user (admin only)."""
    count = await UserNotificationService.delete_all_user_notifications(db, user_id)
    return {"message": f"Removed {count} notification assignments from user"}