# Import all models to ensure they are registered with SQLAlchemy
from .user import User
from .classroom import ClassModel
from .subject import Subject
from .teacher_subject import TeacherSubject
from .student_class import StudentClass
from .notification import Notification
from .user_notification import UserNotification
from .session import Session
from .session_attachment import SessionAttachment
from .admin_login_log import AdminLoginLog

# Export all models for easier imports
__all__ = [
    "User",
    "ClassModel", 
    "Subject",
    "TeacherSubject",
    "StudentClass",
    "Notification",
    "UserNotification",
    "Session",
    "SessionAttachment",
    "AdminLoginLog"
]