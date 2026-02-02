from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.core.auth import get_current_user, get_admin_user
from app.services.banner_service import BannerService
from app.schemas.banner import BannerCreate, BannerUpdate, BannerResponse
from app.models.user import User
import shutil
import os
import uuid

router = APIRouter(prefix="/banners", tags=["banners"])

# Configuration
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.avif'}

@router.get("/", response_model=List[BannerResponse])
async def get_banners(
    region_id: Optional[int] = Query(None, description="Filter by region ID"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """Get all banners (Admin only). Can filter by region."""
    return await BannerService.get_banners(db, region_id)

@router.get("/my-banners", response_model=List[BannerResponse])
async def get_my_banners(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get banners for the current user's region."""
    if not current_user.region_id:
        # If user has no region (e.g. super admin or unassigned), maybe return all or none?
        # For now, let's return empty list if no region assigned, unless it's admin who might want to see something?
        # But admins should use the main GET /banners endpoint.
        # If an admin uses this endpoint, they might expect to see banners for their "region" if they have one.
        return []
    
    return await BannerService.get_banners(db, region_id=current_user.region_id)

@router.post("/", response_model=BannerResponse, status_code=status.HTTP_201_CREATED)
async def create_banner(
    region_id: int = Form(...),
    description: Optional[str] = Form(None),
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """Create a new banner (Admin only)."""
    # Validate file
    if not image.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required"
        )
    
    # Check file extension
    file_extension = os.path.splitext(image.filename)[1].lower()
    if file_extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File type not allowed. Please upload JPG, PNG, GIF, or WebP images."
        )
    
    # Read file content to check size
    file_content = await image.read()
    file_size = len(file_content)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty"
        )
    
    # Save file
    upload_dir = "uploads/banners"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_name = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(upload_dir, file_name)
    
    with open(file_path, "wb") as buffer:
        buffer.write(file_content)
        
    # Create URL (relative path)
    image_url = f"/uploads/banners/{file_name}"
    
    banner_data = BannerCreate(
        region_id=region_id,
        description=description,
        image_url=image_url
    )
    
    return await BannerService.create_banner(db, banner_data)

@router.put("/{banner_id}", response_model=BannerResponse)
async def update_banner(
    banner_id: int,
    region_id: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """Update a banner (Admin only)."""
    update_data = {}
    if region_id is not None:
        update_data['region_id'] = region_id
    if description is not None:
        update_data['description'] = description
        
    if image and image.filename:
        # Check file extension
        file_extension = os.path.splitext(image.filename)[1].lower()
        if file_extension not in ALLOWED_IMAGE_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File type not allowed. Please upload JPG, PNG, GIF, or WebP images."
            )
        
        # Read file content to check size
        file_content = await image.read()
        file_size = len(file_content)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )
        
        upload_dir = "uploads/banners"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_name = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, file_name)
        
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
            
        update_data['image_url'] = f"/uploads/banners/{file_name}"
    
    banner_data = BannerUpdate(**update_data)
    
    updated_banner = await BannerService.update_banner(db, banner_id, banner_data)
    if not updated_banner:
        raise HTTPException(status_code=404, detail="Banner not found")
    return updated_banner

@router.delete("/{banner_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_banner(
    banner_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """Delete a banner (Admin only)."""
    banner = await BannerService.get_banner(db, banner_id)
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")
        
    # Try to delete file if it exists
    if banner.image_url and banner.image_url.startswith("/uploads/"):
        try:
            # Remove leading slash for local path
            file_path = banner.image_url.lstrip("/")
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file: {e}")

    success = await BannerService.delete_banner(db, banner_id)
    return None
