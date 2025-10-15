from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime

class TeacherSubjectBase(BaseModel):
    """Base TeacherSubject schema with common fields."""
    teacher_id: int
    subject_id: int
    
    @validator('teacher_id')
    def validate_teacher_id(cls, v):
        if v <= 0:
            raise ValueError('Teacher ID must be a positive integer')
        return v
    
    @validator('subject_id')
    def validate_subject_id(cls, v):
        if v <= 0:
            raise ValueError('Subject ID must be a positive integer')
        return v

class TeacherSubjectCreate(TeacherSubjectBase):
    """Schema for creating a new teacher-subject assignment."""
    pass

class TeacherSubjectBulkCreate(BaseModel):
    """Schema for creating multiple teacher-subject assignments."""
    teacher_id: int
    subject_ids: List[int]
    
    @validator('teacher_id')
    def validate_teacher_id(cls, v):
        if v <= 0:
            raise ValueError('Teacher ID must be a positive integer')
        return v
    
    @validator('subject_ids')
    def validate_subject_ids(cls, v):
        if not v:
            raise ValueError('At least one subject ID is required')
        for subject_id in v:
            if subject_id <= 0:
                raise ValueError('All subject IDs must be positive integers')
        return v

class TeacherSubjectResponse(TeacherSubjectBase):
    """Schema for teacher-subject response."""
    id: int
    
    class Config:
        from_attributes = True

class TeacherSubjectWithDetailsResponse(TeacherSubjectResponse):
    """Schema for teacher-subject response with detailed information."""
    teacher_name: Optional[str] = None
    subject_name: Optional[str] = None
    class_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class TeacherWithSubjectsResponse(BaseModel):
    """Schema for teacher with their assigned subjects."""
    teacher_id: int
    teacher_name: str
    subjects: List[dict]  # List of subjects with id, name, class info
    
    class Config:
        from_attributes = True

class SubjectWithTeachersResponse(BaseModel):
    """Schema for subject with its assigned teachers."""
    subject_id: int
    subject_name: str
    class_name: str
    teachers: List[dict]  # List of teachers with id, name
    
    class Config:
        from_attributes = True