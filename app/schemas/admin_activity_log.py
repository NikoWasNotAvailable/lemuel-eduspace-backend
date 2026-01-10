from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.admin_activity_log import ActionType, EntityType

class AdminActivityLogCreate(BaseModel):
    """Schema for creating an activity log entry."""
    admin_id: int
    admin_name: str
    action: ActionType
    entity_type: EntityType
    entity_id: Optional[int] = None
    entity_name: Optional[str] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class AdminActivityLogResponse(BaseModel):
    """Schema for activity log response."""
    id: int
    admin_id: int
    admin_name: str
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    entity_name: Optional[str] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class AdminActivityLogFilter(BaseModel):
    """Schema for filtering activity logs."""
    admin_id: Optional[int] = None
    action: Optional[ActionType] = None
    entity_type: Optional[EntityType] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
