from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime

class ClassBase(BaseModel):
    """Base Class schema with common fields."""
    name: str
    region_id: Optional[int] = None
    is_active: bool = True
    
    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Class name must be at least 2 characters long')
        return v.strip()

class ClassCreate(ClassBase):
    """Schema for creating a new class."""
    pass

class ClassUpdate(BaseModel):
    """Schema for updating class information."""
    name: Optional[str] = None
    region_id: Optional[int] = None
    is_active: Optional[bool] = None
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and (not v or len(v.strip()) < 2):
            raise ValueError('Class name must be at least 2 characters long')
        return v.strip() if v else v

class ClassResponse(ClassBase):
    """Schema for class response."""
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True