from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.core.auth import get_current_user, get_admin_user, get_teacher_or_admin_user
from app.services.class_service import ClassService
from app.schemas.classroom import ClassCreate, ClassUpdate, ClassResponse
from app.models.user import User

router = APIRouter(prefix="/classes", tags=["classes"])

@router.post("/", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
async def create_class(
    class_data: ClassCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """Create a new class (admin only)."""
    new_class = await ClassService.create_class(db, class_data)
    return ClassResponse.model_validate(new_class)

@router.get("/", response_model=List[ClassResponse])
async def get_classes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None, description="Filter by active status (true/false)"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of classes. Optionally filter by is_active status."""
    classes = await ClassService.get_classes(db, skip=skip, limit=limit, is_active=is_active)
    return [ClassResponse.model_validate(class_obj) for class_obj in classes]

@router.get("/search", response_model=List[ClassResponse])
async def search_classes(
    q: str = Query(..., description="Search term for class name"),
    is_active: Optional[bool] = Query(None, description="Filter by active status (true/false)"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Search classes by name. Optionally filter by is_active status."""
    classes = await ClassService.search_classes(db, q, is_active=is_active)
    return [ClassResponse.model_validate(class_obj) for class_obj in classes]

@router.get("/by-region/{region_id}", response_model=List[ClassResponse])
async def get_classes_by_region(
    region_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None, description="Filter by active status (true/false)"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get classes by region ID. Optionally filter by is_active status."""
    classes = await ClassService.get_classes_by_region(db, region_id, skip=skip, limit=limit, is_active=is_active)
    return [ClassResponse.model_validate(class_obj) for class_obj in classes]

@router.get("/{class_id}", response_model=ClassResponse)
async def get_class_by_id(
    class_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get class by ID."""
    class_obj = await ClassService.get_class_by_id(db, class_id)
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    return ClassResponse.model_validate(class_obj)

@router.put("/{class_id}", response_model=ClassResponse)
async def update_class(
    class_id: int,
    class_update: ClassUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_teacher_or_admin_user)
):
    """Update class (teacher or admin only)."""
    # Check if another class with the same name already exists    
    updated_class = await ClassService.update_class(db, class_id, class_update)
    if not updated_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    return ClassResponse.model_validate(updated_class)

@router.delete("/{class_id}")
async def delete_class(
    class_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """Delete class (admin only)."""
    success = await ClassService.delete_class(db, class_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    return {"message": "Class deleted successfully"}
