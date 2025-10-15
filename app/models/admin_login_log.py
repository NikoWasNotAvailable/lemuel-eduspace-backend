from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class AdminLoginLog(Base):
    __tablename__ = "admin_login_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    admin_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    admin_name = Column(String(100), nullable=False)  # Name of person accessing admin account
    admin_email = Column(String(100), nullable=False)  # Email used for login
    login_time = Column(DateTime, default=func.current_timestamp(), nullable=False)
    logout_time = Column(DateTime, nullable=True)
    session_token = Column(String(255), nullable=False)  # JWT token for tracking sessions
    ip_address = Column(String(45), nullable=True)  # Store IP address
    user_agent = Column(String(500), nullable=True)  # Store browser/device info
    
    # Relationship to user
    admin_user = relationship("User", foreign_keys=[admin_user_id])
    
    def __repr__(self):
        return f"<AdminLoginLog(id={self.id}, admin_name='{self.admin_name}', login_time='{self.login_time}')>"