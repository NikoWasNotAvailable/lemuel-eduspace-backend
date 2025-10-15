from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime

class AdminLoginRequest(BaseModel):
    """Schema for admin login request."""
    email: EmailStr
    name: str  # Name of the person accessing the admin account
    password: str
    
    @validator('name')
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters long')
        return v.strip()

class AdminLoginResponse(BaseModel):
    """Schema for admin login response."""
    access_token: str
    token_type: str = "bearer"
    admin_user_id: int
    admin_name: str
    login_time: datetime
    session_id: int  # ID of the login log record

class AdminLogoutRequest(BaseModel):
    """Schema for admin logout request."""
    session_id: int

class AdminLoginLogResponse(BaseModel):
    """Schema for admin login log response."""
    id: int
    admin_user_id: int
    admin_name: str
    admin_email: str
    login_time: datetime
    logout_time: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    model_config = {"from_attributes": True}