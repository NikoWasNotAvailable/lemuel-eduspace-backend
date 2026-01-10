from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.user import UserGrade, UserRole
import enum


class UserAcademicHistory(Base):
    """
    Stores a user's grade and class for each academic year.
    This allows viewing historical data - what class/grade a student was in during previous years.
    Also stores teacher assignments to classes per academic year.
    """
    __tablename__ = "user_academic_history"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False)
    
    # For students: their grade and class during this academic year
    grade = Column(Enum(UserGrade), nullable=True)
    class_id = Column(Integer, ForeignKey("classes.id", ondelete="SET NULL"), nullable=True)
    
    # Role at that time (in case someone's role changes)
    role = Column(Enum(UserRole), nullable=False)
    
    created_at = Column(DateTime, default=func.current_timestamp(), nullable=False)
    
    # Ensure one record per user per academic year
    __table_args__ = (
        UniqueConstraint('user_id', 'academic_year_id', name='unique_user_academic_year'),
    )
    
    # Relationships
    user = relationship("User", back_populates="academic_histories")
    academic_year = relationship("AcademicYear", back_populates="user_histories")
    class_obj = relationship("ClassModel", foreign_keys=[class_id])
    
    def __repr__(self):
        return f"<UserAcademicHistory(user_id={self.user_id}, year_id={self.academic_year_id}, grade={self.grade})>"
