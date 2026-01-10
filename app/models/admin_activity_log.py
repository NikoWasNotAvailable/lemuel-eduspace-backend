from sqlalchemy import Column, Integer, String, DateTime, func, Text, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class ActionType(str, enum.Enum):
    create = "create"
    read = "read"
    update = "update"
    delete = "delete"

class EntityType(str, enum.Enum):
    user = "user"
    classroom = "class"
    subject = "subject"
    session = "session"
    notification = "notification"
    promotion = "promotion"
    teacher_subject = "teacher_subject"
    region = "region"
    banner = "banner"
    assignment = "assignment"
    academic_year = "academic_year"

class AdminActivityLog(Base):
    __tablename__ = "admin_activity_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    admin_name = Column(String(100), nullable=False)
    action = Column(Enum(ActionType), nullable=False)
    entity_type = Column(Enum(EntityType), nullable=False)
    entity_id = Column(Integer, nullable=True)  # ID of the affected record
    entity_name = Column(String(255), nullable=True)  # Name/identifier for display
    details = Column(Text, nullable=True)  # JSON string with additional details
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=func.current_timestamp(), nullable=False)
    
    # Relationship to admin user
    admin = relationship("User", foreign_keys=[admin_id])
    
    def __repr__(self):
        return f"<AdminActivityLog(id={self.id}, admin='{self.admin_name}', action='{self.action}', entity='{self.entity_type}')>"
