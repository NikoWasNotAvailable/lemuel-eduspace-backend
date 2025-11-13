from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import date, datetime
from app.models.user import UserRole, UserGrade, UserGender, UserReligion, UserStatus

class UserBase(BaseModel):
    """Base User schema with common fields."""
    nis: Optional[str] = None
    name: str
    role: UserRole = UserRole.student
    grade: Optional[UserGrade] = None
    gender: Optional[UserGender] = None
    email: Optional[EmailStr] = None
    region: Optional[str] = None
    dob: Optional[date] = None
    birth_place: Optional[str] = None
    address: Optional[str] = None
    religion: Optional[UserReligion] = None
    status: UserStatus = UserStatus.active
    profile_picture: Optional[str] = None

class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v
    
    @validator('nis')
    def validate_nis(cls, v):
        if v and len(v) < 5:
            raise ValueError('NIS must be at least 5 characters long')
        return v

class PublicUserCreate(BaseModel):
    """Schema for public user registration (role is set by endpoint, not user)."""
    nis: Optional[str] = None
    name: str
    password: str
    grade: Optional[UserGrade] = None
    gender: Optional[UserGender] = None
    email: Optional[EmailStr] = None
    region: Optional[str] = None
    dob: Optional[date] = None
    birth_place: Optional[str] = None
    address: Optional[str] = None
    religion: Optional[UserReligion] = None
    status: UserStatus = UserStatus.active
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v
    
    @validator('nis')
    def validate_nis(cls, v):
        if v and len(v) < 5:
            raise ValueError('NIS must be at least 5 characters long')
        return v

class UserUpdate(BaseModel):
    """Schema for updating user information."""
    nis: Optional[str] = None
    name: Optional[str] = None
    role: Optional[UserRole] = None
    grade: Optional[UserGrade] = None
    gender: Optional[UserGender] = None
    email: Optional[EmailStr] = None
    region: Optional[str] = None
    dob: Optional[date] = None
    birth_place: Optional[str] = None
    address: Optional[str] = None
    religion: Optional[UserReligion] = None
    status: Optional[UserStatus] = None
    profile_picture: Optional[str] = None

class UserChangePassword(BaseModel):
    """Schema for changing user password."""
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('New password must be at least 8 characters long')
        return v

class UserResponse(UserBase):
    """Schema for user response (excludes sensitive data)."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    """Schema for user login."""
    identifier: str  # Can be NIS or email
    password: str

class UserLoginResponse(BaseModel):
    """Schema for login response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class Token(BaseModel):
    """Token schema."""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Token data schema."""
    user_id: Optional[int] = None

class ProfilePictureUploadResponse(BaseModel):
    """Schema for profile picture upload response."""
    success: bool
    message: str
    profile_picture_url: Optional[str] = None