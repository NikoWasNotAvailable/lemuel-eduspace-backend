from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class ClassModel(Base):
    __tablename__ = "classes"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=func.current_timestamp(), nullable=False)
    
    # Relationship to subjects
    subjects = relationship("Subject", back_populates="class_obj", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ClassModel(id={self.id}, name='{self.name}')>"