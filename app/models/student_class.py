from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base

class StudentClass(Base):
    __tablename__ = "student_classes"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False)
    
    # Relationships
    student = relationship("User", foreign_keys=[student_id])
    class_obj = relationship("ClassModel", foreign_keys=[class_id])
    
    # Unique constraint for student-class combination
    __table_args__ = (
        UniqueConstraint('student_id', 'class_id', name='student_class_unique'),
    )
    
    def __repr__(self):
        return f"<StudentClass(id={self.id}, student_id={self.student_id}, class_id={self.class_id})>"