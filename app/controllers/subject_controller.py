from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.core.auth import get_current_user, get_admin_user, get_teacher_or_admin_user
from app.services.subject_service import SubjectService
from app.schemas.subject import SubjectCreate, SubjectUpdate, SubjectResponse, SubjectWithClassResponse
from app.models.user import User

router = APIRouter(prefix="/subjects", tags=["subjects"])

@router.post("/", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
async def create_subject(
    subject_data: SubjectCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_teacher_or_admin_user)
):
    """Create a new subject (teacher or admin only)."""
    new_subject = await SubjectService.create_subject(db, subject_data)
    return SubjectResponse.model_validate(new_subject)

@router.get("/", response_model=List[SubjectWithClassResponse])
async def get_subjects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    class_id: Optional[int] = Query(None, description="Filter by class ID"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of subjects with optional class filter."""
    subjects = await SubjectService.get_subjects(db, skip=skip, limit=limit, class_id=class_id)
    
    # Convert to response format with class information
    response_subjects = []
    for subject in subjects:
        subject_dict = SubjectResponse.model_validate(subject).model_dump()
        subject_dict['class_name'] = subject.class_obj.name if subject.class_obj else None
        response_subjects.append(SubjectWithClassResponse(**subject_dict))
    
    return response_subjects

@router.get("/search", response_model=List[SubjectWithClassResponse])
async def search_subjects(
    q: str = Query(..., description="Search term for subject name"),
    class_id: Optional[int] = Query(None, description="Filter by class ID"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Search subjects by name with optional class filter."""
    subjects = await SubjectService.search_subjects(db, q, class_id)
    
    # Convert to response format with class information
    response_subjects = []
    for subject in subjects:
        subject_dict = SubjectResponse.model_validate(subject).model_dump()
        subject_dict['class_name'] = subject.class_obj.name if subject.class_obj else None
        response_subjects.append(SubjectWithClassResponse(**subject_dict))
    
    return response_subjects

@router.get("/class/{class_id}", response_model=List[SubjectResponse])
async def get_subjects_by_class(
    class_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get all subjects for a specific class."""
    subjects = await SubjectService.get_subjects_by_class_id(db, class_id)
    return [SubjectResponse.model_validate(subject) for subject in subjects]

@router.get("/{subject_id}", response_model=SubjectWithClassResponse)
async def get_subject_by_id(
    subject_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get subject by ID."""
    subject = await SubjectService.get_subject_by_id(db, subject_id)
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    # Convert to response format with class information
    subject_dict = SubjectResponse.model_validate(subject).model_dump()
    subject_dict['class_name'] = subject.class_obj.name if subject.class_obj else None
    return SubjectWithClassResponse(**subject_dict)

@router.put("/{subject_id}", response_model=SubjectResponse)
async def update_subject(
    subject_id: int,
    subject_update: SubjectUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_teacher_or_admin_user)
):
    """Update subject (teacher or admin only)."""
    updated_subject = await SubjectService.update_subject(db, subject_id, subject_update)
    if not updated_subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    return SubjectResponse.model_validate(updated_subject)

@router.delete("/{subject_id}")
async def delete_subject(
    subject_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """Delete subject (admin only)."""
    success = await SubjectService.delete_subject(db, subject_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    return {"message": "Subject deleted successfully"}