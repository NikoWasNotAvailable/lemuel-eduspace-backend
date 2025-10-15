from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.core.auth import get_current_user, get_admin_user, get_teacher_or_admin_user
from app.services.student_class_service import StudentClassService
from app.schemas.student_class import (
    StudentClassCreate, 
    StudentClassBulkCreate,
    StudentClassBulkCreateMultiple,
    StudentClassResponse, 
    StudentClassWithDetailsResponse,
    StudentWithClassesResponse,
    ClassWithStudentsResponse,
    BulkOperationResponse
)
from app.models.user import User

router = APIRouter(prefix="/student-classes", tags=["student-classes"])

@router.post("/enroll", response_model=StudentClassResponse, status_code=status.HTTP_201_CREATED)
async def enroll_student_in_class(
    enrollment_data: StudentClassCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """Enroll a student in a class (admin only)."""
    enrollment = await StudentClassService.enroll_student_in_class(db, enrollment_data)
    return StudentClassResponse.model_validate(enrollment)

@router.post("/bulk-enroll", response_model=List[StudentClassResponse], status_code=status.HTTP_201_CREATED)
async def bulk_enroll_student_in_classes(
    enrollment_data: StudentClassBulkCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """Enroll a student in multiple classes (admin only)."""
    enrollments = await StudentClassService.bulk_enroll_student_in_classes(db, enrollment_data)
    return [StudentClassResponse.model_validate(enrollment) for enrollment in enrollments]

@router.post("/bulk-enroll-multiple", response_model=BulkOperationResponse, status_code=status.HTTP_201_CREATED)
async def bulk_enroll_multiple_students(
    enrollment_data: StudentClassBulkCreateMultiple,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """Enroll multiple students in their respective classes (admin only)."""
    enrollments = await StudentClassService.bulk_enroll_multiple_students(db, enrollment_data)
    return BulkOperationResponse(
        success=True,
        count=len(enrollments),
        message=f"Successfully enrolled {len(enrollments)} students"
    )

@router.get("/", response_model=List[StudentClassWithDetailsResponse])
async def get_student_class_enrollments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    student_id: Optional[int] = Query(None, description="Filter by student ID"),
    class_id: Optional[int] = Query(None, description="Filter by class ID"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_teacher_or_admin_user)
):
    """Get student-class enrollments with optional filters (teacher or admin)."""
    enrollments = await StudentClassService.get_all_enrollments(
        db, skip=skip, limit=limit, student_id=student_id, class_id=class_id
    )
    
    # Convert to detailed response format
    detailed_enrollments = []
    for enrollment in enrollments:
        enrollment_dict = StudentClassResponse.model_validate(enrollment).model_dump()
        enrollment_dict['student_name'] = enrollment.student.name if enrollment.student else None
        enrollment_dict['class_name'] = enrollment.class_obj.name if enrollment.class_obj else None
        detailed_enrollments.append(StudentClassWithDetailsResponse(**enrollment_dict))
    
    return detailed_enrollments

@router.get("/student/{student_id}", response_model=StudentWithClassesResponse)
async def get_student_classes(
    student_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get all classes for a specific student."""
    enrollments = await StudentClassService.get_student_classes(db, student_id)
    
    if not enrollments:
        # Check if student exists
        students = await StudentClassService.get_students_list(db)
        student = next((s for s in students if s.id == student_id), None)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        return StudentWithClassesResponse(
            student_id=student_id,
            student_name=student.name,
            classes=[]
        )
    
    # Build response
    student_name = enrollments[0].student.name if enrollments[0].student else "Unknown"
    classes = []
    for enrollment in enrollments:
        if enrollment.class_obj:
            class_info = {
                "id": enrollment.class_obj.id,
                "name": enrollment.class_obj.name
            }
            classes.append(class_info)
    
    return StudentWithClassesResponse(
        student_id=student_id,
        student_name=student_name,
        classes=classes
    )

@router.get("/class/{class_id}", response_model=ClassWithStudentsResponse)
async def get_class_students(
    class_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get all students in a specific class."""
    enrollments = await StudentClassService.get_class_students(db, class_id)
    
    if not enrollments:
        # Check if class exists
        classes = await StudentClassService.get_classes_list(db)
        class_obj = next((c for c in classes if c.id == class_id), None)
        if not class_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class not found"
            )
        return ClassWithStudentsResponse(
            class_id=class_id,
            class_name=class_obj.name,
            students=[]
        )
    
    # Build response
    class_name = enrollments[0].class_obj.name if enrollments[0].class_obj else "Unknown"
    students = []
    for enrollment in enrollments:
        if enrollment.student:
            student_info = {
                "id": enrollment.student.id,
                "name": enrollment.student.name,
                "nis": enrollment.student.nis or ""
            }
            students.append(student_info)
    
    return ClassWithStudentsResponse(
        class_id=class_id,
        class_name=class_name,
        students=students
    )

@router.get("/students", response_model=List[dict])
async def get_available_students(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_teacher_or_admin_user)
):
    """Get all available students."""
    students = await StudentClassService.get_students_list(db)
    return [{"id": student.id, "name": student.name, "nis": student.nis or ""} for student in students]

@router.get("/classes", response_model=List[dict])
async def get_available_classes(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_teacher_or_admin_user)
):
    """Get all available classes."""
    classes = await StudentClassService.get_classes_list(db)
    return [{"id": class_obj.id, "name": class_obj.name} for class_obj in classes]

@router.delete("/unenroll/{student_id}/{class_id}")
async def unenroll_student_from_class(
    student_id: int,
    class_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """Remove student enrollment from a class (admin only)."""
    success = await StudentClassService.remove_student_from_class(db, student_id, class_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found"
        )
    return {"message": "Student unenrolled from class successfully"}

@router.delete("/{enrollment_id}")
async def delete_enrollment(
    enrollment_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """Delete student-class enrollment by ID (admin only)."""
    success = await StudentClassService.remove_enrollment_by_id(db, enrollment_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found"
        )
    return {"message": "Enrollment deleted successfully"}

@router.delete("/student/{student_id}/all")
async def remove_all_student_enrollments(
    student_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """Remove all class enrollments for a student (admin only)."""
    count = await StudentClassService.remove_all_student_enrollments(db, student_id)
    return {"message": f"Removed {count} enrollments for student"}

@router.delete("/class/{class_id}/all")
async def remove_all_class_enrollments(
    class_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """Remove all student enrollments from a class (admin only)."""
    count = await StudentClassService.remove_all_class_enrollments(db, class_id)
    return {"message": f"Removed {count} students from class"}

@router.get("/{enrollment_id}", response_model=StudentClassWithDetailsResponse)
async def get_enrollment_by_id(
    enrollment_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get student-class enrollment by ID."""
    enrollment = await StudentClassService.get_enrollment_by_id(db, enrollment_id)
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found"
        )
    
    # Convert to detailed response format
    enrollment_dict = StudentClassResponse.model_validate(enrollment).model_dump()
    enrollment_dict['student_name'] = enrollment.student.name if enrollment.student else None
    enrollment_dict['class_name'] = enrollment.class_obj.name if enrollment.class_obj else None
    
    return StudentClassWithDetailsResponse(**enrollment_dict)