from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base

class TeacherSubject(Base):
    __tablename__ = "teacher_subjects"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    
    # Relationships
    teacher = relationship("User", back_populates="teacher_subjects")
    subject = relationship("Subject", back_populates="teacher_subjects")
    
    # Unique constraint for teacher_id and subject_id combination
    __table_args__ = (
        UniqueConstraint('teacher_id', 'subject_id', name='unique_teacher_subject'),
    )
    
    def __repr__(self):
        return f"<TeacherSubject(id={self.id}, teacher_id={self.teacher_id}, subject_id={self.subject_id})>"