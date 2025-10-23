from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from app.models.notification import NotificationType

# Base schemas
class NotificationBase(BaseModel):
    title: str
    description: Optional[str] = None
    type: NotificationType = NotificationType.general
    nominal: Optional[Decimal] = None  # Optional, for payment notifications
    date: Optional[datetime] = None  # Optional, for events and assignments

class NotificationCreate(NotificationBase):
    @validator('title')
    def validate_title(cls, v):
        if len(v.strip()) < 3:
            raise ValueError('Title must be at least 3 characters long')
        if len(v.strip()) > 255:
            raise ValueError('Title must not exceed 255 characters')
        return v.strip()
    
    @validator('description')
    def validate_description(cls, v):
        if v is not None and len(v.strip()) == 0:
            return None
        return v
    
    @validator('nominal')
    def validate_nominal(cls, v, values):
        if v is not None:
            if v < 0:
                raise ValueError('Nominal amount must be non-negative')
            # Check if nominal is provided for non-payment notifications
            notification_type = values.get('type')
            if notification_type and notification_type != NotificationType.payment:
                raise ValueError('Nominal can only be set for payment notifications')
        return v
    
    @validator('date')
    def validate_date(cls, v, values):
        if v is not None:
            notification_type = values.get('type')
            if notification_type and notification_type not in [NotificationType.event, NotificationType.assignment]:
                raise ValueError('Date can only be set for event and assignment notifications')
        return v

class NotificationUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[NotificationType] = None
    nominal: Optional[Decimal] = None
    date: Optional[datetime] = None
    
    @validator('title')
    def validate_title(cls, v):
        if v is not None:
            if len(v.strip()) < 3:
                raise ValueError('Title must be at least 3 characters long')
            if len(v.strip()) > 255:
                raise ValueError('Title must not exceed 255 characters')
        return v.strip() if v else v
    
    @validator('description')
    def validate_description(cls, v):
        if v is not None and len(v.strip()) == 0:
            return None
        return v
    
    @validator('nominal')
    def validate_nominal(cls, v):
        if v is not None and v < 0:
            raise ValueError('Nominal amount must be non-negative')
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