from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
import os
from app.core.database import get_async_db
from app.core.auth import get_current_user, get_admin_user
from app.core.security import create_access_token
from app.services.user_service import UserService
from app.services.profile_picture_service import ProfilePictureService
from app.schemas.user import (
    UserCreate, 
    UserUpdate, 
    UserResponse, 
    UserLogin, 
    UserLoginResponse,
    UserChangePassword,
    ProfilePictureUploadResponse
)
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """Register a new user."""
    return await UserService.create_user(db, user_data)

@router.post("/login/student", response_model=UserLoginResponse)
async def login_student(
    user_credentials: UserLogin,
    db: AsyncSession = Depends(get_async_db)
):
    """Authenticate student and return access token."""
    user = await UserService.authenticate_user(
        db, user_credentials.identifier, user_credentials.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect identifier or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Only allow student users
    if user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only for student users",
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return UserLoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.post("/login/parent", response_model=UserLoginResponse)
async def login_parent(
    user_credentials: UserLogin,
    db: AsyncSession = Depends(get_async_db)
):
    """Authenticate parent and return access token."""
    user = await UserService.authenticate_user(
        db, user_credentials.identifier, user_credentials.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect identifier or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Only allow parent users
    if user.role not in ["parent", "student_parent"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only for parent users",
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return UserLoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.post("/login/teacher", response_model=UserLoginResponse)
async def login_teacher(
    user_credentials: UserLogin,
    db: AsyncSession = Depends(get_async_db)
):
    """Authenticate teacher and return access token."""
    user = await UserService.authenticate_user(
        db, user_credentials.identifier, user_credentials.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect identifier or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Only allow teacher users
    if user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only for teacher users",
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return UserLoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.post("/login", response_model=UserLoginResponse)
async def login_user(
    user_credentials: UserLogin,
    db: AsyncSession = Depends(get_async_db)
):
    """General authentication endpoint (excludes admin users - they must use /admin-auth/login)"""
    user = await UserService.authenticate_user(
        db, user_credentials.identifier, user_credentials.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect identifier or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Prevent admin users from using regular login
    if user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin users must use the dedicated admin login endpoint: /api/v1/admin-auth/login/admin or /api/v1/admin-auth/login",
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return UserLoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information."""
    return UserResponse.model_validate(current_user)

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Update current user information."""
    updated_user = await UserService.update_user(db, current_user.id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return UserResponse.model_validate(updated_user)

@router.post("/me/change-password")
async def change_current_user_password(
    password_data: UserChangePassword,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Change current user password."""
    success = await UserService.change_password(db, current_user.id, password_data)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to change password"
        )
    return {"message": "Password changed successfully"}

@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    role: Optional[str] = Query(None),
    grade: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """Get list of users (admin only)."""
    users = await UserService.get_users(db, skip=skip, limit=limit, role=role, grade=grade)
    return [UserResponse.model_validate(user) for user in users]

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """Get user by ID (admin only)."""
    user = await UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return UserResponse.model_validate(user)

@router.put("/{user_id}", response_model=UserResponse)
async def update_user_by_id(
    user_id: int,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """Update user by ID (admin only)."""
    updated_user = await UserService.update_user(db, user_id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return UserResponse.model_validate(updated_user)

@router.delete("/{user_id}")
async def delete_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """Delete user by ID (admin only)."""
    success = await UserService.delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {"message": "User deleted successfully"}

@router.post("/profile-picture", response_model=ProfilePictureUploadResponse)
async def upload_profile_picture(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Upload profile picture for the current user."""
    try:
        # Delete old profile picture if exists
        if current_user.profile_picture:
            ProfilePictureService.delete_profile_picture(current_user.profile_picture)
        
        # Save new profile picture
        file_path = await ProfilePictureService.save_profile_picture(file, current_user.id)
        
        # Update user record
        updated_user = await UserService.update_profile_picture(db, current_user.id, file_path)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Generate profile picture URL
        profile_picture_url = ProfilePictureService.get_profile_picture_url(
            file_path, 
            base_url=""  # You can set this to your domain
        )
        
        return ProfilePictureUploadResponse(
            success=True,
            message="Profile picture uploaded successfully",
            profile_picture_url=profile_picture_url
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload profile picture"
        )

@router.get("/profile-picture/{filename}")
async def get_profile_picture(filename: str):
    """Serve profile picture files."""
    file_path = os.path.join(ProfilePictureService.UPLOAD_DIRECTORY, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile picture not found"
        )
    
    return FileResponse(file_path)

@router.delete("/profile-picture")
async def delete_profile_picture(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Delete the current user's profile picture."""
    if not current_user.profile_picture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No profile picture to delete"
        )
    
    # Delete file from disk
    ProfilePictureService.delete_profile_picture(current_user.profile_picture)
    
    # Update user record
    updated_user = await UserService.remove_profile_picture(db, current_user.id)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "Profile picture deleted successfully"}

@router.post("/{user_id}/profile-picture", response_model=ProfilePictureUploadResponse)
async def upload_user_profile_picture(
    user_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """Upload profile picture for a specific user (admin only)."""
    # Check if target user exists
    target_user = await UserService.get_user_by_id(db, user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Delete old profile picture if exists
        if target_user.profile_picture:
            ProfilePictureService.delete_profile_picture(target_user.profile_picture)
        
        # Save new profile picture
        file_path = await ProfilePictureService.save_profile_picture(file, user_id)
        
        # Update user record
        updated_user = await UserService.update_profile_picture(db, user_id, file_path)
        
        # Generate profile picture URL
        profile_picture_url = ProfilePictureService.get_profile_picture_url(
            file_path, 
            base_url=""
        )
        
        return ProfilePictureUploadResponse(
            success=True,
            message="Profile picture uploaded successfully",
            profile_picture_url=profile_picture_url
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload profile picture"
        )