from pydantic import BaseModel, validator
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, date as DateType

if TYPE_CHECKING:
    from app.schemas.session_attachment import SessionAttachmentResponse

# Base schemas
class SessionBase(BaseModel):
    subject_id: int
    session_no: int
    date: DateType

class SessionCreate(SessionBase):
    @validator('subject_id')
    def validate_subject_id(cls, v):
        if v <= 0:
            raise ValueError('Subject ID must be a positive integer')
        return v
    
    @validator('session_no')
    def validate_session_no(cls, v):
        if v <= 0:
            raise ValueError('Session number must be a positive integer')
        return v
    
    @validator('date')
    def validate_date(cls, v):
        from datetime import date
        if v < date.today():
            raise ValueError('Session date cannot be in the past')
        return v

class SessionUpdate(BaseModel):
    subject_id: Optional[int] = None
    session_no: Optional[int] = None
    date: Optional[DateType] = None
    
    @validator('subject_id')
    def validate_subject_id(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Subject ID must be a positive integer')
        return v
    
    @validator('session_no')
    def validate_session_no(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Session number must be a positive integer')
        return v

class SessionResponse(SessionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}

class SessionWithSubjectResponse(SessionResponse):
    subject_name: Optional[str] = None
    class_name: Optional[str] = None
    
    model_config = {"from_attributes": True}

class SessionWithAttachmentsResponse(SessionResponse):
    attachments: List["SessionAttachmentResponse"] = []
    
    model_config = {"from_attributes": True}

class SessionListResponse(BaseModel):
    sessions: List[SessionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class SessionStatsResponse(BaseModel):
    total_sessions: int
    sessions_by_subject: dict  # {"Math": 5, "Science": 3, ...}
    upcoming_sessions: int
    sessions_today: int