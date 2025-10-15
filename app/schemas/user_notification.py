from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
from app.schemas.notification import NotificationResponse
from app.schemas.user import UserResponse

# Base schemas
class UserNotificationBase(BaseModel):
    user_id: int
    notification_id: int
    is_read: bool = False

class UserNotificationCreate(BaseModel):
    notification_id: int
    user_ids: List[int]
    
    @validator('user_ids')
    def validate_user_ids(cls, v):
        if len(v) == 0:
            raise ValueError('At least one user ID must be provided')
        if len(v) > 1000:
            raise ValueError('Cannot assign notification to more than 1000 users at once')
        return list(set(v))  # Remove duplicates

class UserNotificationBulkCreate(BaseModel):
    notification_ids: List[int]
    user_ids: List[int]
    
    @validator('notification_ids')
    def validate_notification_ids(cls, v):
        if len(v) == 0:
            raise ValueError('At least one notification ID must be provided')
        if len(v) > 100:
            raise ValueError('Cannot assign more than 100 notifications at once')
        return list(set(v))
    
    @validator('user_ids')
    def validate_user_ids(cls, v):
        if len(v) == 0:
            raise ValueError('At least one user ID must be provided')
        if len(v) > 1000:
            raise ValueError('Cannot assign to more than 1000 users at once')
        return list(set(v))

class UserNotificationMarkRead(BaseModel):
    notification_ids: List[int]
    
    @validator('notification_ids')
    def validate_notification_ids(cls, v):
        if len(v) == 0:
            raise ValueError('At least one notification ID must be provided')
        return list(set(v))

class UserNotificationAssignByRole(BaseModel):
    notification_id: int
    roles: List[str]
    
    @validator('roles')
    def validate_roles(cls, v):
        valid_roles = ['admin', 'teacher', 'student', 'parent', 'student_parent']
        if len(v) == 0:
            raise ValueError('At least one role must be provided')
        for role in v:
            if role not in valid_roles:
                raise ValueError(f'Invalid role: {role}. Valid roles are: {valid_roles}')
        return list(set(v))

# Response schemas
class UserNotificationResponse(UserNotificationBase):
    id: int
    read_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}

class UserNotificationWithDetailsResponse(UserNotificationResponse):
    notification: NotificationResponse
    user_name: Optional[str] = None

class UserNotificationForUserResponse(UserNotificationResponse):
    notification: NotificationResponse

class NotificationWithReadStatusResponse(BaseModel):
    notification: NotificationResponse
    is_read: bool
    read_at: Optional[datetime] = None
    user_notification_id: int

class UserNotificationStatsResponse(BaseModel):
    total_notifications: int
    unread_count: int
    read_count: int
    unread_by_type: dict  # {"general": 5, "assignment": 3, ...}
    latest_unread: Optional[NotificationWithReadStatusResponse] = None

class BulkAssignmentResponse(BaseModel):
    success: bool
    assigned_count: int
    skipped_count: int  # Already assigned
    message: str
    assignment_ids: Optional[List[int]] = None

class BulkReadResponse(BaseModel):
    success: bool
    marked_read_count: int
    already_read_count: int
    message: str