from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Base schemas
class StudentClassBase(BaseModel):
    student_id: int
    class_id: int

class StudentClassCreate(StudentClassBase):
    pass

class StudentClassBulkCreate(BaseModel):
    student_id: int
    class_ids: List[int]

class StudentClassBulkCreateMultiple(BaseModel):
    enrollments: List[StudentClassCreate]

# Response schemas
class StudentClassResponse(StudentClassBase):
    id: int
    
    model_config = {"from_attributes": True}

class StudentClassWithDetailsResponse(StudentClassResponse):
    student_name: Optional[str] = None
    class_name: Optional[str] = None

class StudentWithClassesResponse(BaseModel):
    student_id: int
    student_name: str
    classes: List[dict]  # List of {"id": int, "name": str}

class ClassWithStudentsResponse(BaseModel):
    class_id: int
    class_name: str
    students: List[dict]  # List of {"id": int, "name": str, "nis": str}

class BulkOperationResponse(BaseModel):
    success: bool
    count: int
    message: str