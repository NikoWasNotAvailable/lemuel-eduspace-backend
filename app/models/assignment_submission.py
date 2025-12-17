from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, Text, DECIMAL
from sqlalchemy.orm import relationship
from app.core.database import Base

class AssignmentSubmission(Base):
    __tablename__ = "assignment_submissions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    grade = Column(DECIMAL(5, 2), nullable=True)
    feedback = Column(Text, nullable=True)
    submitted_at = Column(DateTime, default=func.current_timestamp(), nullable=False)
    
    # Relationships
    session = relationship("Session", back_populates="submissions")
    student = relationship("User", back_populates="submissions")
    
    def __repr__(self):
        return f"<AssignmentSubmission(id={self.id}, session_id={self.session_id}, student_id={self.student_id})>"
