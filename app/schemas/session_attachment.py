from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime

# Base schemas
class SessionAttachmentBase(BaseModel):
    filename: str
    content_type: str

class SessionAttachmentCreate(SessionAttachmentBase):
    session_id: int
    file_size: int
    file_path: str
    uploaded_by: int
    
    @validator('session_id')
    def validate_session_id(cls, v):
        if v <= 0:
            raise ValueError('Session ID must be a positive integer')
        return v
    
    @validator('file_size')
    def validate_file_size(cls, v):
        if v <= 0:
            raise ValueError('File size must be positive')
        max_size = 50 * 1024 * 1024  # 50MB limit
        if v > max_size:
            raise ValueError('File size cannot exceed 50MB')
        return v
    
    @validator('filename')
    def validate_filename(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Filename cannot be empty')
        # Check for potentially dangerous file extensions
        dangerous_extensions = ['.exe', '.bat', '.cmd', '.scr', '.com', '.pif']
        if any(v.lower().endswith(ext) for ext in dangerous_extensions):
            raise ValueError('File type not allowed for security reasons')
        return v.strip()

class SessionAttachmentUpdate(BaseModel):
    filename: Optional[str] = None
    
    @validator('filename')
    def validate_filename(cls, v):
        if v is not None:
            if not v or len(v.strip()) == 0:
                raise ValueError('Filename cannot be empty')
        return v.strip() if v else v

class SessionAttachmentResponse(SessionAttachmentBase):
    id: int
    session_id: int
    file_size: int
    uploaded_by: int
    created_at: datetime
    
    model_config = {"from_attributes": True}

class SessionAttachmentWithUploaderResponse(SessionAttachmentResponse):
    uploader_name: Optional[str] = None
    uploader_email: Optional[str] = None
    
    model_config = {"from_attributes": True}

class SessionAttachmentListResponse(BaseModel):
    attachments: List[SessionAttachmentResponse]
    total: int
    session_id: int

class FileUploadResponse(BaseModel):
    success: bool
    message: str
    attachment_id: Optional[int] = None
    filename: Optional[str] = None