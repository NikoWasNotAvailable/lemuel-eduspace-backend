from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
from app.models.notification import NotificationType

# Base schemas
class NotificationBase(BaseModel):
    title: str
    subject: Optional[str] = None
    type: NotificationType = NotificationType.general

class NotificationCreate(NotificationBase):
    @validator('title')
    def validate_title(cls, v):
        if len(v.strip()) < 3:
            raise ValueError('Title must be at least 3 characters long')
        if len(v.strip()) > 255:
            raise ValueError('Title must not exceed 255 characters')
        return v.strip()
    
    @validator('subject')
    def validate_subject(cls, v):
        if v is not None and len(v.strip()) == 0:
            return None
        return v

class NotificationUpdate(BaseModel):
    title: Optional[str] = None
    subject: Optional[str] = None
    type: Optional[NotificationType] = None
    
    @validator('title')
    def validate_title(cls, v):
        if v is not None:
            if len(v.strip()) < 3:
                raise ValueError('Title must be at least 3 characters long')
            if len(v.strip()) > 255:
                raise ValueError('Title must not exceed 255 characters')
        return v.strip() if v else v
    
    @validator('subject')
    def validate_subject(cls, v):
        if v is not None and len(v.strip()) == 0:
            return None
        return v

class NotificationBulkCreate(BaseModel):
    notifications: List[NotificationCreate]
    
    @validator('notifications')
    def validate_notifications(cls, v):
        if len(v) == 0:
            raise ValueError('At least one notification must be provided')
        if len(v) > 50:
            raise ValueError('Cannot create more than 50 notifications at once')
        return v

# Response schemas
class NotificationResponse(NotificationBase):
    id: int
    created_at: datetime
    
    model_config = {"from_attributes": True}

class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class BulkOperationResponse(BaseModel):
    success: bool
    count: int
    message: str
    created_ids: Optional[List[int]] = None

class NotificationStatsResponse(BaseModel):
    total_notifications: int
    by_type: dict  # {"general": 10, "announcement": 5, ...}
    latest_notification: Optional[NotificationResponse] = None
    today_count: int