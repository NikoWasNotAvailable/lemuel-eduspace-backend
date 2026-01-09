from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.user import UserGrade

class PromotionPreviewRequest(BaseModel):
    exclude_student_ids: Optional[List[int]] = []

class PromotionConfirmRequest(BaseModel):
    exclude_student_ids: Optional[List[int]] = []

class StudentPromotionDetail(BaseModel):
    student_id: int
    student_name: str
    old_grade: Optional[str]
    old_class_id: Optional[int]
    old_class_name: Optional[str]
    old_status: Optional[str] = None  # For undo support
    new_grade: Optional[str]
    new_class_id: Optional[int]
    new_class_name: Optional[str]
    new_status: Optional[str] = None  # For graduated students
    status: str  # "promoted", "graduated", "no_class_available", "error"

class PromotionPreviewResponse(BaseModel):
    summary: Dict[str, int]  # e.g. {"promoted": 10, "graduated": 2, "errors": 0}
    details: List[StudentPromotionDetail]

class PromotionHistoryResponse(BaseModel):
    id: int
    promotion_date: datetime
    status: str
    summary: Dict[str, int]

    class Config:
        from_attributes = True

class PromotionHistoryListResponse(BaseModel):
    """Response for listing promotion history records."""
    id: int
    promotion_date: datetime
    status: str
    summary: Dict[str, int]  # Calculated from details
    total_affected: int

    class Config:
        from_attributes = True

class PromotionHistoryDetailResponse(BaseModel):
    """Response for single promotion history with full details."""
    id: int
    promotion_date: datetime
    status: str
    summary: Dict[str, int]
    total_affected: int
    details: List[StudentPromotionDetail]

    class Config:
        from_attributes = True
