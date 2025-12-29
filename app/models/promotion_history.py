from sqlalchemy import Column, Integer, String, DateTime, func, JSON, Enum
from app.core.database import Base
import enum

class PromotionStatus(str, enum.Enum):
    applied = "applied"
    reverted = "reverted"

class PromotionHistory(Base):
    __tablename__ = "promotion_history"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    promotion_date = Column(DateTime, default=func.current_timestamp(), nullable=False)
    details = Column(JSON, nullable=False)  # Stores list of {student_id, old_grade, old_class_id, new_grade, new_class_id}
    status = Column(Enum(PromotionStatus), default=PromotionStatus.applied, nullable=False)
    
    def __repr__(self):
        return f"<PromotionHistory(id={self.id}, date='{self.promotion_date}', status='{self.status}')>"
