from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, DECIMAL, func
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
    created_at = Column(DateTime, default=func.current_timestamp(), nullable=False)
    
    def __repr__(self):
        return f"<Notification(id={self.id}, title='{self.title}', type='{self.type}')>"