from sqlalchemy import Column, Integer, String, Enum, Date, DateTime, func
from app.core.database import Base
from datetime import datetime
import enum

class UserRole(str, enum.Enum):
    admin = "admin"
    teacher = "teacher"
    student = "student"
    parent = "parent"
    student_parent = "student_parent"

class UserGrade(str, enum.Enum):
    TKA = "TKA"
    TKB = "TKB"
    SD1 = "SD1"
    SD2 = "SD2"
    SD3 = "SD3"
    SD4 = "SD4"
    SD5 = "SD5"
    SD6 = "SD6"
    SMP1 = "SMP1"
    SMP2 = "SMP2"
    SMP3 = "SMP3"

class UserGender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nis = Column(String(50), unique=True, index=True, nullable=True)
    password = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.student, nullable=False)
    grade = Column(Enum(UserGrade), nullable=True)
    gender = Column(Enum(UserGender), nullable=True)
    email = Column(String(100), unique=True, index=True, nullable=True)
    region = Column(String(100), nullable=True)
    dob = Column(Date, nullable=True)
    created_at = Column(DateTime, default=func.current_timestamp(), nullable=False)
    updated_at = Column(
        DateTime, 
        default=func.current_timestamp(), 
        onupdate=func.current_timestamp(), 
        nullable=False
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', role='{self.role}')>"