from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, func, and_, or_, desc
from sqlalchemy.orm import selectinload
from app.models.user_notification import UserNotification
from app.models.notification import Notification, NotificationType
from app.models.user import User, UserRole
from app.schemas.user_notification import (
    UserNotificationCreate, 
    UserNotificationBulkCreate,
    UserNotificationMarkRead,
    UserNotificationAssignByRole
)
from fastapi import HTTPException, status
from datetime import datetime

class UserNotificationService:
    
    @staticmethod
    async def assign_notification_to_users(
        db: AsyncSession, 
        assignment_data: UserNotificationCreate
    ) -> Tuple[List[UserNotification], int]:
        """Assign a notification to multiple users."""
        # Check if notification exists
        notification_query = select(Notification).where(
            Notification.id == assignment_data.notification_id
        )
        notification_result = await db.execute(notification_query)
        notification = notification_result.scalar_one_or_none()
        
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        # Check which users exist
        users_query = select(User).where(User.id.in_(assignment_data.user_ids))
        users_result = await db.execute(users_query)
        existing_users = users_result.scalars().all()
        existing_user_ids = [user.id for user in existing_users]
        
        missing_user_ids = set(assignment_data.user_ids) - set(existing_user_ids)
        if missing_user_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Users not found: {list(missing_user_ids)}"
            )
        
        # Check existing assignments
        existing_assignments_query = select(UserNotification).where(
            and_(
                UserNotification.notification_id == assignment_data.notification_id,
                UserNotification.user_id.in_(assignment_data.user_ids)
            )
        )
        existing_assignments_result = await db.execute(existing_assignments_query)
        existing_assignments = existing_assignments_result.scalars().all()
        existing_assignment_user_ids = [assign.user_id for assign in existing_assignments]
        
        # Create only new assignments
        new_user_ids = set(assignment_data.user_ids) - set(existing_assignment_user_ids)
        
        assignments = []
        for user_id in new_user_ids:
            assignment = UserNotification(
                user_id=user_id,
                notification_id=assignment_data.notification_id
            )
            db.add(assignment)
            assignments.append(assignment)
        
        await db.commit()
        for assignment in assignments:
            await db.refresh(assignment)
        
        return assignments, len(existing_assignment_user_ids)
    
    @staticmethod
    async def bulk_assign_notifications_to_users(
        db: AsyncSession, 
        bulk_data: UserNotificationBulkCreate
    ) -> Tuple[List[UserNotification], int]:
        """Assign multiple notifications to multiple users."""
        # Check if notifications exist
        notifications_query = select(Notification).where(
            Notification.id.in_(bulk_data.notification_ids)
        )
        notifications_result = await db.execute(notifications_query)
        existing_notifications = notifications_result.scalars().all()
        existing_notification_ids = [notif.id for notif in existing_notifications]
        
        missing_notification_ids = set(bulk_data.notification_ids) - set(existing_notification_ids)
        if missing_notification_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notifications not found: {list(missing_notification_ids)}"
            )
        
        # Check if users exist
        users_query = select(User).where(User.id.in_(bulk_data.user_ids))
        users_result = await db.execute(users_query)
        existing_users = users_result.scalars().all()
        existing_user_ids = [user.id for user in existing_users]
        
        missing_user_ids = set(bulk_data.user_ids) - set(existing_user_ids)
        if missing_user_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Users not found: {list(missing_user_ids)}"
            )
        
        # Check existing assignments
        existing_assignments_query = select(UserNotification).where(
            and_(
                UserNotification.notification_id.in_(bulk_data.notification_ids),
                UserNotification.user_id.in_(bulk_data.user_ids)
            )
        )
        existing_assignments_result = await db.execute(existing_assignments_query)
        existing_assignments = existing_assignments_result.scalars().all()
        existing_pairs = {(assign.user_id, assign.notification_id) for assign in existing_assignments}
        
        # Create only new assignments
        assignments = []
        skipped_count = 0
        
        for user_id in bulk_data.user_ids:
            for notification_id in bulk_data.notification_ids:
                if (user_id, notification_id) not in existing_pairs:
                    assignment = UserNotification(
                        user_id=user_id,
                        notification_id=notification_id
                    )
                    db.add(assignment)
                    assignments.append(assignment)
                else:
                    skipped_count += 1
        
        await db.commit()
        for assignment in assignments:
            await db.refresh(assignment)
        
        return assignments, skipped_count
    
    @staticmethod
    async def assign_notification_by_role(
        db: AsyncSession, 
        assignment_data: UserNotificationAssignByRole
    ) -> Tuple[List[UserNotification], int]:
        """Assign a notification to all users with specific roles."""
        # Check if notification exists
        notification_query = select(Notification).where(
            Notification.id == assignment_data.notification_id
        )
        notification_result = await db.execute(notification_query)
        notification = notification_result.scalar_one_or_none()
        
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        # Get all users with specified roles
        role_enums = [UserRole(role) for role in assignment_data.roles]
        users_query = select(User).where(User.role.in_(role_enums))
        users_result = await db.execute(users_query)
        users = users_result.scalars().all()
        
        if not users:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No users found with roles: {assignment_data.roles}"
            )
        
        user_ids = [user.id for user in users]
        
        # Check existing assignments
        existing_assignments_query = select(UserNotification).where(
            and_(
                UserNotification.notification_id == assignment_data.notification_id,
                UserNotification.user_id.in_(user_ids)
            )
        )
        existing_assignments_result = await db.execute(existing_assignments_query)
        existing_assignments = existing_assignments_result.scalars().all()
        existing_assignment_user_ids = [assign.user_id for assign in existing_assignments]
        
        # Create only new assignments
        new_user_ids = set(user_ids) - set(existing_assignment_user_ids)
        
        assignments = []
        for user_id in new_user_ids:
            assignment = UserNotification(
                user_id=user_id,
                notification_id=assignment_data.notification_id
            )
            db.add(assignment)
            assignments.append(assignment)
        
        await db.commit()
        for assignment in assignments:
            await db.refresh(assignment)
        
        return assignments, len(existing_assignment_user_ids)
    
    @staticmethod
    async def get_user_notifications(
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        unread_only: bool = False,
        notification_type: Optional[NotificationType] = None
    ) -> Tuple[List[UserNotification], int]:
        """Get notifications for a specific user."""
        query = select(UserNotification).options(
            selectinload(UserNotification.notification)
        ).where(UserNotification.user_id == user_id)
        
        count_query = select(func.count(UserNotification.id)).where(
            UserNotification.user_id == user_id
        )
        
        if unread_only:
            query = query.where(UserNotification.is_read == False)
            count_query = count_query.where(UserNotification.is_read == False)
        
        if notification_type:
            query = query.join(Notification).where(Notification.type == notification_type)
            count_query = count_query.join(Notification).where(Notification.type == notification_type)
        
        # Order by notification creation time (newest first)
        query = query.join(Notification).order_by(
            desc(Notification.created_at)
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        user_notifications = result.scalars().all()
        
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        return user_notifications, total
    
    @staticmethod
    async def mark_notifications_as_read(
        db: AsyncSession,
        user_id: int,
        read_data: UserNotificationMarkRead
    ) -> Tuple[int, int]:
        """Mark specific notifications as read for a user."""
        now = datetime.utcnow()
        
        # Get existing assignments that are unread
        existing_query = select(UserNotification).where(
            and_(
                UserNotification.user_id == user_id,
                UserNotification.notification_id.in_(read_data.notification_ids),
                UserNotification.is_read == False
            )
        )
        existing_result = await db.execute(existing_query)
        unread_assignments = existing_result.scalars().all()
        
        # Count already read
        total_query = select(func.count(UserNotification.id)).where(
            and_(
                UserNotification.user_id == user_id,
                UserNotification.notification_id.in_(read_data.notification_ids)
            )
        )
        total_result = await db.execute(total_query)
        total_count = total_result.scalar()
        
        already_read_count = total_count - len(unread_assignments)
        
        if unread_assignments:
            # Update unread notifications
            unread_ids = [assign.id for assign in unread_assignments]
            update_query = update(UserNotification).where(
                UserNotification.id.in_(unread_ids)
            ).values(is_read=True, read_at=now)
            
            await db.execute(update_query)
            await db.commit()
        
        return len(unread_assignments), already_read_count
    
    @staticmethod
    async def mark_all_as_read(db: AsyncSession, user_id: int) -> int:
        """Mark all notifications as read for a user."""
        now = datetime.utcnow()
        
        query = update(UserNotification).where(
            and_(
                UserNotification.user_id == user_id,
                UserNotification.is_read == False
            )
        ).values(is_read=True, read_at=now)
        
        result = await db.execute(query)
        await db.commit()
        return result.rowcount
    
    @staticmethod
    async def get_notification_recipients(
        db: AsyncSession,
        notification_id: int,
        read_status: Optional[bool] = None
    ) -> List[UserNotification]:
        """Get all users who received a specific notification."""
        query = select(UserNotification).options(
            selectinload(UserNotification.user)
        ).where(UserNotification.notification_id == notification_id)
        
        if read_status is not None:
            query = query.where(UserNotification.is_read == read_status)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_user_notification_stats(db: AsyncSession, user_id: int) -> dict:
        """Get notification statistics for a user."""
        # Total count
        total_query = select(func.count(UserNotification.id)).where(
            UserNotification.user_id == user_id
        )
        total_result = await db.execute(total_query)
        total_count = total_result.scalar()
        
        # Unread count
        unread_query = select(func.count(UserNotification.id)).where(
            and_(
                UserNotification.user_id == user_id,
                UserNotification.is_read == False
            )
        )
        unread_result = await db.execute(unread_query)
        unread_count = unread_result.scalar()
        
        read_count = total_count - unread_count
        
        # Unread count by type
        type_query = select(
            Notification.type,
            func.count(UserNotification.id)
        ).join(UserNotification).where(
            and_(
                UserNotification.user_id == user_id,
                UserNotification.is_read == False
            )
        ).group_by(Notification.type)
        
        type_result = await db.execute(type_query)
        unread_by_type = {row[0]: row[1] for row in type_result.fetchall()}
        
        # Latest unread notification
        latest_query = select(UserNotification).options(
            selectinload(UserNotification.notification)
        ).join(Notification).where(
            and_(
                UserNotification.user_id == user_id,
                UserNotification.is_read == False
            )
        ).order_by(desc(Notification.created_at)).limit(1)
        
        latest_result = await db.execute(latest_query)
        latest_unread = latest_result.scalar_one_or_none()
        
        return {
            "total_notifications": total_count,
            "unread_count": unread_count,
            "read_count": read_count,
            "unread_by_type": unread_by_type,
            "latest_unread": latest_unread
        }
    
    @staticmethod
    async def delete_user_notification(
        db: AsyncSession,
        user_id: int,
        notification_id: int
    ) -> bool:
        """Remove a notification assignment from a user."""
        query = delete(UserNotification).where(
            and_(
                UserNotification.user_id == user_id,
                UserNotification.notification_id == notification_id
            )
        )
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0
    
    @staticmethod
    async def delete_all_user_notifications(db: AsyncSession, user_id: int) -> int:
        """Remove all notification assignments for a user."""
        query = delete(UserNotification).where(UserNotification.user_id == user_id)
        result = await db.execute(query)
        await db.commit()
        return result.rowcount