from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base

class Subject(Base):
    __tablename__ = "subjects"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False)
    
    # Relationship to ClassModel
    class_obj = relationship("ClassModel", back_populates="subjects")
    
    # Unique constraint for class_id and name combination
    __table_args__ = (
        UniqueConstraint('class_id', 'name', name='unique_class_subject'),
    )
    
    def __repr__(self):
        return f"<Subject(id={self.id}, name='{self.name}', class_id={self.class_id})>"