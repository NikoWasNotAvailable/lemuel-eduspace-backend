from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.core.auth import get_current_user, get_admin_user, get_teacher_or_admin_user
from app.services.teacher_subject_service import TeacherSubjectService
from app.schemas.teacher_subject import (
    TeacherSubjectCreate, 
    TeacherSubjectBulkCreate,
    TeacherSubjectResponse, 
    TeacherSubjectWithDetailsResponse,
    TeacherWithSubjectsResponse,
    SubjectWithTeachersResponse
)
from app.models.user import User

router = APIRouter(prefix="/teacher-subjects", tags=["teacher-subjects"])

@router.post("/assign", response_model=TeacherSubjectResponse, status_code=status.HTTP_201_CREATED)
async def assign_teacher_to_subject(
    assignment_data: TeacherSubjectCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """Assign a teacher to a subject (admin only)."""
    assignment = await TeacherSubjectService.assign_teacher_to_subject(db, assignment_data)
    return TeacherSubjectResponse.model_validate(assignment)

@router.post("/bulk-assign", response_model=List[TeacherSubjectResponse], status_code=status.HTTP_201_CREATED)
async def bulk_assign_teacher_to_subjects(
    assignment_data: TeacherSubjectBulkCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """Assign a teacher to multiple subjects (admin only)."""
    assignments = await TeacherSubjectService.bulk_assign_teacher_to_subjects(db, assignment_data)
    return [TeacherSubjectResponse.model_validate(assignment) for assignment in assignments]

@router.get("/", response_model=List[TeacherSubjectWithDetailsResponse])
async def get_teacher_subject_assignments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    teacher_id: Optional[int] = Query(None, description="Filter by teacher ID"),
    subject_id: Optional[int] = Query(None, description="Filter by subject ID"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_teacher_or_admin_user)
):
    """Get teacher-subject assignments with optional filters (teacher or admin)."""
    assignments = await TeacherSubjectService.get_all_assignments(
        db, skip=skip, limit=limit, teacher_id=teacher_id, subject_id=subject_id
    )
    
    # Convert to detailed response format
    detailed_assignments = []
    for assignment in assignments:
        assignment_dict = TeacherSubjectResponse.model_validate(assignment).model_dump()
        assignment_dict['teacher_name'] = assignment.teacher.name if assignment.teacher else None
        assignment_dict['subject_name'] = assignment.subject.name if assignment.subject else None
        assignment_dict['class_name'] = assignment.subject.class_obj.name if assignment.subject and assignment.subject.class_obj else None
        detailed_assignments.append(TeacherSubjectWithDetailsResponse(**assignment_dict))
    
    return detailed_assignments

@router.get("/teacher/{teacher_id}", response_model=TeacherWithSubjectsResponse)
async def get_teacher_subjects(
    teacher_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get all subjects assigned to a specific teacher."""
    assignments = await TeacherSubjectService.get_teacher_subjects(db, teacher_id)
    
    if not assignments:
        # Check if teacher exists
        teachers = await TeacherSubjectService.get_teachers_list(db)
        teacher = next((t for t in teachers if t.id == teacher_id), None)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher not found"
            )
        return TeacherWithSubjectsResponse(
            teacher_id=teacher_id,
            teacher_name=teacher.name,
            subjects=[]
        )
    
    # Build response
    teacher_name = assignments[0].teacher.name if assignments[0].teacher else "Unknown"
    subjects = []
    for assignment in assignments:
        if assignment.subject:
            subject_info = {
                "id": assignment.subject.id,
                "name": assignment.subject.name,
                "class_id": assignment.subject.class_id,
                "class_name": assignment.subject.class_obj.name if assignment.subject.class_obj else None
            }
            subjects.append(subject_info)
    
    return TeacherWithSubjectsResponse(
        teacher_id=teacher_id,
        teacher_name=teacher_name,
        subjects=subjects
    )

@router.get("/subject/{subject_id}", response_model=SubjectWithTeachersResponse)
async def get_subject_teachers(
    subject_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get all teachers assigned to a specific subject."""
    assignments = await TeacherSubjectService.get_subject_teachers(db, subject_id)
    
    if not assignments:
        # Check if subject exists by trying to get it through the service
        from app.services.subject_service import SubjectService
        subject = await SubjectService.get_subject_by_id(db, subject_id)
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found"
            )
        return SubjectWithTeachersResponse(
            subject_id=subject_id,
            subject_name=subject.name,
            class_name=subject.class_obj.name if subject.class_obj else "Unknown",
            teachers=[]
        )
    
    # Build response
    assignment_with_subject = assignments[0]
    subject_name = assignment_with_subject.subject.name if assignment_with_subject.subject else "Unknown"
    class_name = assignment_with_subject.subject.class_obj.name if assignment_with_subject.subject and assignment_with_subject.subject.class_obj else "Unknown"
    
    teachers = []
    for assignment in assignments:
        if assignment.teacher:
            teacher_info = {
                "id": assignment.teacher.id,
                "name": assignment.teacher.name,
                "email": assignment.teacher.email
            }
            teachers.append(teacher_info)
    
    return SubjectWithTeachersResponse(
        subject_id=subject_id,
        subject_name=subject_name,
        class_name=class_name,
        teachers=teachers
    )

@router.get("/teachers", response_model=List[dict])
async def get_available_teachers(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_teacher_or_admin_user)
):
    """Get all available teachers."""
    teachers = await TeacherSubjectService.get_teachers_list(db)
    return [{"id": teacher.id, "name": teacher.name, "email": teacher.email} for teacher in teachers]

@router.delete("/unassign/{teacher_id}/{subject_id}")
async def unassign_teacher_from_subject(
    teacher_id: int,
    subject_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """Remove teacher assignment from a subject (admin only)."""
    success = await TeacherSubjectService.remove_teacher_from_subject(db, teacher_id, subject_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    return {"message": "Teacher unassigned from subject successfully"}

@router.delete("/{assignment_id}")
async def delete_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """Delete teacher-subject assignment by ID (admin only)."""
    success = await TeacherSubjectService.remove_assignment_by_id(db, assignment_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    return {"message": "Assignment deleted successfully"}

@router.delete("/teacher/{teacher_id}/all")
async def remove_all_teacher_assignments(
    teacher_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """Remove all subject assignments for a teacher (admin only)."""
    count = await TeacherSubjectService.remove_all_teacher_assignments(db, teacher_id)
    return {"message": f"Removed {count} assignments for teacher"}

@router.get("/{assignment_id}", response_model=TeacherSubjectWithDetailsResponse)
async def get_assignment_by_id(
    assignment_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get teacher-subject assignment by ID."""
    assignment = await TeacherSubjectService.get_assignment_by_id(db, assignment_id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Convert to detailed response format
    assignment_dict = TeacherSubjectResponse.model_validate(assignment).model_dump()
    assignment_dict['teacher_name'] = assignment.teacher.name if assignment.teacher else None
    assignment_dict['subject_name'] = assignment.subject.name if assignment.subject else None
    assignment_dict['class_name'] = assignment.subject.class_obj.name if assignment.subject and assignment.subject.class_obj else None
    
    return TeacherSubjectWithDetailsResponse(**assignment_dict)