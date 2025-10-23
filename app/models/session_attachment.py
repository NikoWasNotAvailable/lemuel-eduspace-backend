from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, BigInteger
from sqlalchemy.orm import relationship
from app.core.database import Base

class SessionAttachment(Base):
    __tablename__ = "session_attachments"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)  # Original filename
    file_path = Column(String(500), nullable=False)  # Path where file is stored
    file_size = Column(BigInteger, nullable=False)  # File size in bytes
    content_type = Column(String(100), nullable=False)  # MIME type (application/pdf, etc.)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # Who uploaded the file
    created_at = Column(DateTime, default=func.current_timestamp(), nullable=False)
    
    # Relationship to Session
    session = relationship("Session", back_populates="attachments")
    
    # Relationship to User (who uploaded the file)
    uploader = relationship("User")
    
    def __repr__(self):
        return f"<SessionAttachment(id={self.id}, session_id={self.session_id}, filename='{self.filename}')>"