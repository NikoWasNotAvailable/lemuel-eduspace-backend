from sqlalchemy import Column, Integer, String, Enum, Date, DateTime, func, Text
from sqlalchemy.orm import relationship
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
    male = "male"
    female = "female"

class UserReligion(str, enum.Enum):
    islam = "islam"
    christian = "christian"
    catholic = "catholic"
    hindu = "hindu"
    buddhism = "buddhism"
    confucianism = "confucianism"
    other = "other"

class UserStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    suspended = "suspended"

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
    birth_place = Column(String(100), nullable=True)  # Tempat lahir
    address = Column(Text, nullable=True)  # Alamat lengkap
    religion = Column(Enum(UserReligion), nullable=True)  # Agama
    status = Column(Enum(UserStatus), default=UserStatus.active, nullable=False)  # Status pengguna
    profile_picture = Column(String(500), nullable=True)  # Path to profile picture file
    created_at = Column(DateTime, default=func.current_timestamp(), nullable=False)
    updated_at = Column(
        DateTime, 
        default=func.current_timestamp(), 
        onupdate=func.current_timestamp(), 
        nullable=False
    )
    
    # Relationship to teacher_subjects
    teacher_subjects = relationship("TeacherSubject", back_populates="teacher", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', role='{self.role}')>"