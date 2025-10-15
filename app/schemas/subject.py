from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime

class SubjectBase(BaseModel):
    """Base Subject schema with common fields."""
    name: str
    class_id: int
    
    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Subject name must be at least 2 characters long')
        return v.strip()
    
    @validator('class_id')
    def validate_class_id(cls, v):
        if v <= 0:
            raise ValueError('Class ID must be a positive integer')
        return v

class SubjectCreate(SubjectBase):
    """Schema for creating a new subject."""
    pass

class SubjectUpdate(BaseModel):
    """Schema for updating subject information."""
    name: Optional[str] = None
    class_id: Optional[int] = None
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and (not v or len(v.strip()) < 2):
            raise ValueError('Subject name must be at least 2 characters long')
        return v.strip() if v else v
    
    @validator('class_id')
    def validate_class_id(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Class ID must be a positive integer')
        return v

class SubjectResponse(SubjectBase):
    """Schema for subject response."""
    id: int
    
    class Config:
        from_attributes = True

class SubjectWithClassResponse(SubjectResponse):
    """Schema for subject response with class information."""
    class_name: Optional[str] = None
    
    class Config:
        from_attributes = True