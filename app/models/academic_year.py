from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class AcademicYear(Base):
    """
    Represents an academic year period.
    Example: "2024/2025" starting August 2024, ending July 2025
    """
    __tablename__ = "academic_years"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)  # e.g., "2024/2025"
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_current = Column(Boolean, default=False, nullable=False)  # Only one should be current
    created_at = Column(DateTime, default=func.current_timestamp(), nullable=False)
    
    # Relationships
    # passive_deletes=True tells SQLAlchemy to rely on database CASCADE instead of setting FK to NULL
    user_histories = relationship("UserAcademicHistory", back_populates="academic_year", passive_deletes=True)
    
    def __repr__(self):
        return f"<AcademicYear(id={self.id}, name='{self.name}', is_current={self.is_current})>"
