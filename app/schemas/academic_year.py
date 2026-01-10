from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List


# ========================
# Academic Year Schemas
# ========================

class AcademicYearBase(BaseModel):
    name: str  # e.g., "2024/2025"
    start_date: date
    end_date: date
    is_current: bool = False


class AcademicYearCreate(AcademicYearBase):
    pass


class AcademicYearUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: Optional[bool] = None


class AcademicYearResponse(AcademicYearBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========================
# User Academic History Schemas
# ========================

class UserAcademicHistoryBase(BaseModel):
    user_id: int
    academic_year_id: int
    grade: Optional[str] = None
    class_id: Optional[int] = None
    role: str


class UserAcademicHistoryCreate(UserAcademicHistoryBase):
    pass


class UserAcademicHistoryResponse(BaseModel):
    id: int
    user_id: int
    academic_year_id: int
    grade: Optional[str] = None
    class_id: Optional[int] = None
    class_name: Optional[str] = None
    role: str
    created_at: datetime
    
    # Include academic year info for convenience
    academic_year_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserHistoryWithYearResponse(BaseModel):
    """Response for a user's history with full academic year details"""
    id: int
    academic_year: AcademicYearResponse
    grade: Optional[str] = None
    class_id: Optional[int] = None
    class_name: Optional[str] = None
    role: str
    
    class Config:
        from_attributes = True


class UserAcademicYearsResponse(BaseModel):
    """Response containing all academic years a user has history in"""
    user_id: int
    user_name: str
    current_grade: Optional[str] = None
    current_class_id: Optional[int] = None
    current_class_name: Optional[str] = None
    academic_years: List[UserHistoryWithYearResponse]
    
    class Config:
        from_attributes = True
