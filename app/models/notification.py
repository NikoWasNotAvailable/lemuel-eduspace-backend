from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, DECIMAL, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class NotificationType(str, enum.Enum):
    general = "general"
    announcement = "announcement"
    assignment = "assignment"
    event = "event"
    payment = "payment"

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(Enum(NotificationType), default=NotificationType.general, nullable=False)
    nominal = Column(DECIMAL(10, 2), nullable=True)  # Optional, for payment notifications
    date = Column(DateTime, nullable=True)  # Optional, for events and assignments
    is_scheduled = Column(Integer, default=0, nullable=False)  # Boolean: 0 = False, 1 = True
    image = Column(String(500), nullable=True)  # Path to notification image
    link = Column(String(500), nullable=True)  # Optional URL link for notification redirect
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # Who created this notification
    created_at = Column(DateTime, default=func.current_timestamp(), nullable=False)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    user_notifications = relationship("UserNotification", back_populates="notification", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Notification(id={self.id}, title='{self.title}', type='{self.type}')>"