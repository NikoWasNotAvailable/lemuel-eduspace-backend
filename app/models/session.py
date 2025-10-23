from sqlalchemy import Column, Integer, String, Date, ForeignKey, UniqueConstraint, DateTime, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    session_no = Column(Integer, nullable=False)  # Session number (1, 2, 3, etc.)
    date = Column(Date, nullable=False)  # Session date
    created_at = Column(DateTime, default=func.current_timestamp(), nullable=False)
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)
    
    # Relationship to Subject
    subject = relationship("Subject", back_populates="sessions")
    
    # Relationship to SessionAttachment (one-to-many)
    attachments = relationship("SessionAttachment", back_populates="session", cascade="all, delete-orphan")
    
    # Unique constraint for subject_id and session_no combination
    __table_args__ = (
        UniqueConstraint('subject_id', 'session_no', name='unique_subject_session_no'),
    )
    
    def __repr__(self):
        return f"<Session(id={self.id}, subject_id={self.subject_id}, session_no={self.session_no}, date='{self.date}')>"