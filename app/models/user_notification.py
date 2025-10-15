from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base

class UserNotification(Base):
    __tablename__ = "user_notifications"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    notification_id = Column(Integer, ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    notification = relationship("Notification", foreign_keys=[notification_id])
    
    # Unique constraint for user-notification combination
    __table_args__ = (
        UniqueConstraint('user_id', 'notification_id', name='unique_user_notification'),
    )
    
    def __repr__(self):
        return f"<UserNotification(id={self.id}, user_id={self.user_id}, notification_id={self.notification_id}, is_read={self.is_read})>"