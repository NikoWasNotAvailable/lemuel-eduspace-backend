from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
from decimal import Decimal

class AssignmentSubmissionBase(BaseModel):
    filename: str

class AssignmentSubmissionCreate(AssignmentSubmissionBase):
    session_id: int
    
class AssignmentSubmissionUpdate(BaseModel):
    grade: Optional[Decimal] = None
    feedback: Optional[str] = None
    
    @validator('grade')
    def validate_grade(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Grade must be between 0 and 100')
        return v

class AssignmentSubmissionResponse(AssignmentSubmissionBase):
    id: int
    session_id: int
    student_id: int
    file_path: str
    grade: Optional[Decimal] = None
    feedback: Optional[str] = None
    submitted_at: datetime
    student_name: Optional[str] = None
    
    model_config = {"from_attributes": True}
