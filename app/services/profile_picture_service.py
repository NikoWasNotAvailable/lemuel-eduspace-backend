import os
import uuid
from typing import Optional
from pathlib import Path
from fastapi import HTTPException, status, UploadFile

class ProfilePictureService:
    
    # Configuration
    UPLOAD_DIRECTORY = "uploads/profile_pictures"
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    
    @staticmethod
    def _ensure_upload_directory():
        """Ensure the upload directory exists."""
        Path(ProfilePictureService.UPLOAD_DIRECTORY).mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def _get_file_extension(filename: str) -> str:
        """Get file extension from filename."""
        return Path(filename).suffix.lower()
    
    @staticmethod
    def _is_allowed_file(filename: str) -> bool:
        """Check if file extension is allowed."""
        extension = ProfilePictureService._get_file_extension(filename)
        return extension in ProfilePictureService.ALLOWED_EXTENSIONS
    
    @staticmethod
    def _generate_unique_filename(original_filename: str) -> str:
        """Generate a unique filename to prevent conflicts."""
        extension = ProfilePictureService._get_file_extension(original_filename)
        unique_id = str(uuid.uuid4())
        return f"profile_{unique_id}{extension}"
    
    @staticmethod
    def _validate_image_content(file_content: bytes) -> bool:
        """Basic validation for image file content."""
        # Check for common image file signatures
        image_signatures = [
            b'\xff\xd8\xff',  # JPEG
            b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a',  # PNG
            b'\x47\x49\x46\x38',  # GIF
            b'RIFF',  # WebP (starts with RIFF)
        ]
        
        for signature in image_signatures:
            if file_content.startswith(signature):
                return True
            
        return False
    
    @staticmethod
    async def save_profile_picture(file: UploadFile, user_id: int) -> str:
        """Save profile picture and return the file path."""
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required"
            )
        
        if not ProfilePictureService._is_allowed_file(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File type not allowed. Please upload JPG, PNG, GIF, or WebP images."
            )
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > ProfilePictureService.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum allowed size of {ProfilePictureService.MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )
        
        # Ensure upload directory exists
        ProfilePictureService._ensure_upload_directory()
        
        try:
            # Validate image content
            if not ProfilePictureService._validate_image_content(file_content):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid image file format"
                )
            
            # Generate unique filename
            unique_filename = ProfilePictureService._generate_unique_filename(file.filename)
            file_path = os.path.join(ProfilePictureService.UPLOAD_DIRECTORY, unique_filename)
            
            # Save file to disk
            with open(file_path, "wb") as buffer:
                buffer.write(file_content)
            
            return file_path
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save profile picture"
            )
    
    @staticmethod
    def delete_profile_picture(file_path: str) -> bool:
        """Delete profile picture file from disk."""
        if not file_path:
            return True
        
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except OSError:
            # Log the error but don't raise exception
            return False
    
    @staticmethod
    def get_profile_picture_url(file_path: Optional[str], base_url: str = "") -> Optional[str]:
        """Generate profile picture URL from file path."""
        if not file_path or not os.path.exists(file_path):
            return None
        
        # Convert file path to URL
        # Remove the upload directory prefix and create URL
        relative_path = file_path.replace(ProfilePictureService.UPLOAD_DIRECTORY, "").lstrip(os.path.sep)
        return f"{base_url}/api/v1/users/profile-picture/{relative_path}".replace("\\", "/")
    
    @staticmethod
    def validate_image_file(file_content: bytes) -> bool:
        """Validate if file content is a valid image using file signatures."""
        return ProfilePictureService._validate_image_content(file_content)