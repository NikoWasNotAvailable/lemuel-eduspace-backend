from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime
import json
import logging

from app.models.admin_activity_log import AdminActivityLog, ActionType, EntityType
from app.models.user import User

logger = logging.getLogger(__name__)

class AdminActivityLogService:
    """Service for logging admin CRUD operations."""
    
    @staticmethod
    async def log_activity_by_name(
        db: AsyncSession,
        admin_id: int,
        admin_name: str,
        action: ActionType,
        entity_type: EntityType,
        entity_id: Optional[int] = None,
        entity_name: Optional[str] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AdminActivityLog:
        """
        Log an admin activity using admin name directly (from X-Admin-Name header).
        
        Args:
            db: Database session
            admin_id: The admin user ID
            admin_name: The admin name (from X-Admin-Name header)
            action: Type of action (create, read, update, delete)
            entity_type: Type of entity being affected
            entity_id: ID of the affected entity
            entity_name: Display name of the entity
            details: Additional details as dict (will be stored as JSON)
            ip_address: Client IP address
            user_agent: Client user agent
        """
        try:
            log_entry = AdminActivityLog(
                admin_id=admin_id,
                admin_name=admin_name,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                entity_name=entity_name,
                details=json.dumps(details) if details else None,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            db.add(log_entry)
            await db.commit()
            await db.refresh(log_entry)
            
            logger.info(f"Admin activity logged: {admin_name} {action.value} {entity_type.value} {entity_id}")
            return log_entry
            
        except Exception as e:
            logger.error(f"Failed to log admin activity: {e}")
            await db.rollback()
            # Don't raise - logging failure shouldn't break the main operation
            return None
    
    @staticmethod
    async def log_activity(
        db: AsyncSession,
        admin: User,
        action: ActionType,
        entity_type: EntityType,
        entity_id: Optional[int] = None,
        entity_name: Optional[str] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AdminActivityLog:
        """
        Log an admin activity.
        
        Args:
            db: Database session
            admin: The admin user performing the action
            action: Type of action (create, read, update, delete)
            entity_type: Type of entity being affected
            entity_id: ID of the affected entity
            entity_name: Display name of the entity
            details: Additional details as dict (will be stored as JSON)
            ip_address: Client IP address
            user_agent: Client user agent
        """
        try:
            log_entry = AdminActivityLog(
                admin_id=admin.id,
                admin_name=admin.name,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                entity_name=entity_name,
                details=json.dumps(details) if details else None,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            db.add(log_entry)
            await db.commit()
            await db.refresh(log_entry)
            
            logger.info(f"Admin activity logged: {admin.name} {action.value} {entity_type.value} {entity_id}")
            return log_entry
            
        except Exception as e:
            logger.error(f"Failed to log admin activity: {e}")
            await db.rollback()
            # Don't raise - logging failure shouldn't break the main operation
            return None
    
    @staticmethod
    async def get_activity_logs(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        admin_id: Optional[int] = None,
        admin_name: Optional[str] = None,
        action: Optional[ActionType] = None,
        entity_type: Optional[EntityType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AdminActivityLog]:
        """Get activity logs with filters."""
        query = select(AdminActivityLog)
        
        conditions = []
        if admin_id:
            conditions.append(AdminActivityLog.admin_id == admin_id)
        if admin_name:
            query = query.filter(AdminActivityLog.admin_name.ilike(f"%{admin_name}%"))
        if action:
            conditions.append(AdminActivityLog.action == action)
        if entity_type:
            conditions.append(AdminActivityLog.entity_type == entity_type)
        if start_date:
            conditions.append(AdminActivityLog.created_at >= start_date)
        if end_date:
            conditions.append(AdminActivityLog.created_at <= end_date)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(AdminActivityLog.created_at.desc())
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_activity_log_by_id(
        db: AsyncSession,
        log_id: int
    ) -> Optional[AdminActivityLog]:
        """Get a specific activity log entry."""
        result = await db.execute(
            select(AdminActivityLog).where(AdminActivityLog.id == log_id)
        )
        return result.scalar_one_or_none()
