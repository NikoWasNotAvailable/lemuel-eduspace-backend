from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, func, and_, desc
from app.models.notification import Notification, NotificationType
from app.schemas.notification import NotificationCreate, NotificationUpdate, NotificationBulkCreate
from fastapi import HTTPException, status
from datetime import datetime, date

class NotificationService:
    
    @staticmethod
    async def create_notification(db: AsyncSession, notification_data: NotificationCreate) -> Notification:
        """Create a new notification."""
        notification = Notification(
            title=notification_data.title,
            description=notification_data.description,
            type=notification_data.type,
            nominal=notification_data.nominal,
            date=notification_data.date
        )
        
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        return notification
    
    @staticmethod
    async def bulk_create_notifications(
        db: AsyncSession, 
        bulk_data: NotificationBulkCreate
    ) -> List[Notification]:
        """Create multiple notifications at once."""
        notifications = []
        
        for notification_data in bulk_data.notifications:
            notification = Notification(
                title=notification_data.title,
                description=notification_data.description,
                type=notification_data.type,
                nominal=notification_data.nominal,
                date=notification_data.date
            )
            notifications.append(notification)
        
        db.add_all(notifications)
        await db.commit()
        
        for notification in notifications:
            await db.refresh(notification)
        
        return notifications
    
    @staticmethod
    async def get_all_notifications(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        notification_type: Optional[NotificationType] = None,
        search: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Tuple[List[Notification], int]:
        """Get notifications with filters and pagination."""
        query = select(Notification)
        count_query = select(func.count(Notification.id))
        
        # Apply filters
        if notification_type:
            query = query.where(Notification.type == notification_type)
            count_query = count_query.where(Notification.type == notification_type)
        
        if search:
            search_filter = Notification.title.ilike(f"%{search}%")
            if True:  # Always include subject in search
                search_filter = search_filter | Notification.subject.ilike(f"%{search}%")
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        if start_date:
            query = query.where(Notification.created_at >= start_date)
            count_query = count_query.where(Notification.created_at >= start_date)
        
        if end_date:
            query = query.where(Notification.created_at <= end_date)
            count_query = count_query.where(Notification.created_at <= end_date)
        
        # Order by created_at descending (newest first)
        query = query.order_by(desc(Notification.created_at)).offset(skip).limit(limit)
        
        # Execute queries
        result = await db.execute(query)
        notifications = result.scalars().all()
        
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        return notifications, total
    
    @staticmethod
    async def get_notification_by_id(db: AsyncSession, notification_id: int) -> Optional[Notification]:
        """Get a notification by ID."""
        query = select(Notification).where(Notification.id == notification_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_notification(
        db: AsyncSession, 
        notification_id: int, 
        notification_update: NotificationUpdate
    ) -> Optional[Notification]:
        """Update a notification."""
        # First check if notification exists
        notification = await NotificationService.get_notification_by_id(db, notification_id)
        if not notification:
            return None
        
        # Prepare update data (only include fields that are not None)
        update_data = {}
        if notification_update.title is not None:
            update_data["title"] = notification_update.title
        if notification_update.description is not None:
            update_data["description"] = notification_update.description
        if notification_update.type is not None:
            update_data["type"] = notification_update.type
        if notification_update.nominal is not None:
            update_data["nominal"] = notification_update.nominal
        if notification_update.date is not None:
            update_data["date"] = notification_update.date
        
        if not update_data:
            return notification  # No changes to make
        
        # Perform update
        query = update(Notification).where(
            Notification.id == notification_id
        ).values(**update_data)
        
        await db.execute(query)
        await db.commit()
        
        # Return updated notification
        await db.refresh(notification)
        return notification
    
    @staticmethod
    async def delete_notification(db: AsyncSession, notification_id: int) -> bool:
        """Delete a notification."""
        query = delete(Notification).where(Notification.id == notification_id)
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0
    
    @staticmethod
    async def delete_notifications_by_type(db: AsyncSession, notification_type: NotificationType) -> int:
        """Delete all notifications of a specific type."""
        query = delete(Notification).where(Notification.type == notification_type)
        result = await db.execute(query)
        await db.commit()
        return result.rowcount
    
    @staticmethod
    async def delete_old_notifications(db: AsyncSession, older_than_date: datetime) -> int:
        """Delete notifications older than specified date."""
        query = delete(Notification).where(Notification.created_at < older_than_date)
        result = await db.execute(query)
        await db.commit()
        return result.rowcount
    
    @staticmethod
    async def get_latest_notifications(db: AsyncSession, limit: int = 10) -> List[Notification]:
        """Get the latest notifications."""
        query = select(Notification).order_by(
            desc(Notification.created_at)
        ).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_notifications_by_type(
        db: AsyncSession, 
        notification_type: NotificationType,
        limit: int = 50
    ) -> List[Notification]:
        """Get notifications by type."""
        query = select(Notification).where(
            Notification.type == notification_type
        ).order_by(desc(Notification.created_at)).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_notification_stats(db: AsyncSession) -> dict:
        """Get notification statistics."""
        # Total count
        total_query = select(func.count(Notification.id))
        total_result = await db.execute(total_query)
        total_count = total_result.scalar()
        
        # Count by type
        type_query = select(
            Notification.type,
            func.count(Notification.id)
        ).group_by(Notification.type)
        type_result = await db.execute(type_query)
        type_counts = {row[0]: row[1] for row in type_result.fetchall()}
        
        # Latest notification
        latest_query = select(Notification).order_by(
            desc(Notification.created_at)
        ).limit(1)
        latest_result = await db.execute(latest_query)
        latest_notification = latest_result.scalar_one_or_none()
        
        # Today's count
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        today_query = select(func.count(Notification.id)).where(
            and_(
                Notification.created_at >= today_start,
                Notification.created_at <= today_end
            )
        )
        today_result = await db.execute(today_query)
        today_count = today_result.scalar()
        
        return {
            "total_notifications": total_count,
            "by_type": type_counts,
            "latest_notification": latest_notification,
            "today_count": today_count
        }
    
    @staticmethod
    async def search_notifications(
        db: AsyncSession,
        search_term: str,
        limit: int = 50
    ) -> List[Notification]:
        """Search notifications by title and subject."""
        query = select(Notification).where(
            Notification.title.ilike(f"%{search_term}%") |
            Notification.subject.ilike(f"%{search_term}%")
        ).order_by(desc(Notification.created_at)).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()