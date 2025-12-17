from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import os

from app.core.database import get_async_db
from app.core.auth import get_current_user, require_roles
from app.models.user import User, UserRole
from app.services.assignment_service import AssignmentService
from app.schemas.assignment_submission import (
    AssignmentSubmissionResponse,
    AssignmentSubmissionUpdate
)

router = APIRouter(prefix="/assignments", tags=["assignments"])

@router.post("/submit", response_model=AssignmentSubmissionResponse, status_code=status.HTTP_201_CREATED)
async def submit_assignment(
    session_id: int = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Submit an assignment (Student only)."""
    return await AssignmentService.submit_assignment(
        db, session_id, current_user.id, file
    )

@router.get("/session/{session_id}", response_model=List[AssignmentSubmissionResponse])
async def get_session_submissions(
    session_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_roles([UserRole.admin, UserRole.teacher]))
):
    """Get all submissions for a session (Teacher/Admin only)."""
    submissions = await AssignmentService.get_submissions_by_session(db, session_id)
    
    # Transform to include student name
    result = []
    for sub in submissions:
        sub_response = AssignmentSubmissionResponse.model_validate(sub)
        if sub.student:
            sub_response.student_name = sub.student.name
        result.append(sub_response)
        
    return result

@router.get("/my-submissions", response_model=List[AssignmentSubmissionResponse])
async def get_my_submissions(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get my submissions."""
    return await AssignmentService.get_my_submissions(db, current_user.id)

@router.get("/{submission_id}/download")
async def download_submission(
    submission_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Download assignment submission file."""
    submission = await AssignmentService.get_submission_by_id(db, submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    # Check permissions: Admin/Teacher can download any, Student can only download their own
    if current_user.role not in [UserRole.admin, UserRole.teacher] and submission.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to download this submission"
        )
    
    # Construct absolute file path
    # Assuming file_path in DB is relative like "/uploads/assignments/..."
    # We need to remove the leading slash if present to join correctly
    relative_path = submission.file_path.lstrip("/")
    file_path = os.path.abspath(relative_path)
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server"
        )
    
    return FileResponse(
        path=file_path,
        filename=submission.filename
    )

@router.put("/{submission_id}/grade", response_model=AssignmentSubmissionResponse)
async def grade_submission(
    submission_id: int,
    grade_data: AssignmentSubmissionUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_roles([UserRole.admin, UserRole.teacher]))
):
    """Grade a submission (Teacher/Admin only)."""
    submission = await AssignmentService.grade_submission(db, submission_id, grade_data)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    return submission
