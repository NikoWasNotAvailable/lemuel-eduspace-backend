from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, Union
from datetime import date, datetime
from app.models.user import UserRole, UserGrade, UserGender, UserReligion, UserStatus
from app.schemas.region import RegionResponse

class UserBase(BaseModel):
    """Base User schema with common fields."""
    nis: Optional[str] = None
    name: str
    role: UserRole = UserRole.student
    grade: Optional[UserGrade] = None
    gender: Optional[UserGender] = None
    email: Optional[EmailStr] = None
    region_id: Optional[int] = None
    class_id: Optional[int] = None
    dob: Optional[date] = None
    birth_place: Optional[str] = None
    address: Optional[str] = None
    religion: Optional[UserReligion] = None
    status: UserStatus = UserStatus.active
    profile_picture: Optional[str] = None

class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str
    parent_password: Optional[str] = None  # Only for student roles
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v
    
    @validator('parent_password')
    def validate_parent_password(cls, v, values):
        # Only validate parent_password for student roles
        if v is not None:
            if len(v) < 8:
                raise ValueError('Parent password must be at least 8 characters long')
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
    parent_password: Optional[str] = None  # Only for student registrations
    grade: Optional[UserGrade] = None
    gender: Optional[UserGender] = None
    email: Optional[EmailStr] = None
    region_id: Optional[int] = None
    class_id: Optional[int] = None
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
    region_id: Optional[int] = None
    class_id: Optional[int] = None
    dob: Optional[date] = None
    birth_place: Optional[str] = None
    address: Optional[str] = None
    religion: Optional[UserReligion] = None
    status: Optional[UserStatus] = None
    profile_picture: Optional[str] = None
    password: Optional[str] = None
    parent_password: Optional[str] = None

    @validator('password')
    def validate_password(cls, v):
        if v and len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

    @validator('parent_password')
    def validate_parent_password(cls, v):
        if v and len(v) < 8:
            raise ValueError('Parent password must be at least 8 characters long')
        return v

class UserChangePassword(BaseModel):
    """Schema for changing user password."""
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('New password must be at least 8 characters long')
        return v

class ParentPasswordSet(BaseModel):
    """Schema for setting parent password (student only)."""
    student_password: str  # Student's current password for verification
    parent_password: str
    
    @validator('parent_password')
    def validate_parent_password(cls, v):
        if len(v) < 8:
            raise ValueError('Parent password must be at least 8 characters long')
        return v

class ParentPasswordChange(BaseModel):
    """Schema for changing parent password."""
    current_parent_password: str
    new_parent_password: str
    
    @validator('new_parent_password')
    def validate_new_parent_password(cls, v):
        if len(v) < 8:
            raise ValueError('New parent password must be at least 8 characters long')
        return v

# NOTE: ParentLogin schema not needed - we use UserLogin for /login/parent endpoint
# Parents use the same identifier (student's NIS/email) + parent_password field

class UserResponse(UserBase):
    """Schema for user response (excludes sensitive data)."""
    id: int
    created_at: datetime
    updated_at: datetime
    region: Optional[str] = None
    class_name: Optional[str] = None
    profile_picture_url: Optional[str] = None
    
    @validator('region', pre=True)
    def extract_region_name(cls, v):
        if v and hasattr(v, 'name'):
            return v.name
        return v
    
    @validator('class_name', pre=True, always=True)
    def extract_class_name(cls, v, values):
        # This validator extracts class name from the ORM object if present
        # Note: This won't work directly from values, needs to be set in service layer
        return v

    @validator('profile_picture_url', pre=True, always=True)
    def compute_profile_picture_url(cls, v, values):
        profile_picture = values.get('profile_picture')
        if not profile_picture:
            return None
        
        # Convert file path to URL
        # The path in DB is like "uploads/profile_pictures/filename.jpg"
        # The URL should be "/api/v1/users/profile-picture/filename.jpg"
        import os
        filename = os.path.basename(profile_picture)
        return f"/api/v1/users/profile-picture/{filename}"

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
    parent_access: bool = False  # True when logged in via /login/parent endpoint

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