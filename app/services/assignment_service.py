from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import joinedload
from fastapi import UploadFile, HTTPException, status
import os
import shutil
import uuid
from app.models.assignment_submission import AssignmentSubmission
from app.models.user import User
from app.schemas.assignment_submission import AssignmentSubmissionUpdate

class AssignmentService:
    
    @staticmethod
    async def submit_assignment(
        db: AsyncSession, 
        session_id: int, 
        student_id: int, 
        file: UploadFile
    ) -> AssignmentSubmission:
        """Submit an assignment."""
        # Check if submission already exists for this session and student
        query = select(AssignmentSubmission).where(
            and_(
                AssignmentSubmission.session_id == session_id,
                AssignmentSubmission.student_id == student_id
            )
        )
        result = await db.execute(query)
        existing_submission = result.scalar_one_or_none()
        
        # Setup upload directory
        upload_dir = "uploads/assignments"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        relative_path = f"/uploads/assignments/{unique_filename}"
        
        if existing_submission:
            # Update existing submission
            existing_submission.filename = file.filename
            existing_submission.file_path = relative_path
            existing_submission.submitted_at = func.now()
            
            await db.commit()
            await db.refresh(existing_submission)
            return existing_submission
        else:
            # Create new submission
            submission = AssignmentSubmission(
                session_id=session_id,
                student_id=student_id,
                filename=file.filename,
                file_path=relative_path
            )
            db.add(submission)
            await db.commit()
            await db.refresh(submission)
            return submission

    @staticmethod
    async def get_submissions_by_session(
        db: AsyncSession, 
        session_id: int
    ) -> List[AssignmentSubmission]:
        """Get all submissions for a session (Teacher view)."""
        query = select(AssignmentSubmission).options(
            joinedload(AssignmentSubmission.student)
        ).where(AssignmentSubmission.session_id == session_id)
        
        result = await db.execute(query)
        submissions = result.scalars().all()
        return submissions

    @staticmethod
    async def get_my_submissions(
        db: AsyncSession, 
        student_id: int
    ) -> List[AssignmentSubmission]:
        """Get all submissions by a student."""
        query = select(AssignmentSubmission).where(
            AssignmentSubmission.student_id == student_id
        )
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def grade_submission(
        db: AsyncSession, 
        submission_id: int, 
        grade_data: AssignmentSubmissionUpdate
    ) -> Optional[AssignmentSubmission]:
        """Grade a submission."""
        query = select(AssignmentSubmission).where(AssignmentSubmission.id == submission_id)
        result = await db.execute(query)
        submission = result.scalar_one_or_none()
        
        if not submission:
            return None
            
        if grade_data.grade is not None:
            submission.grade = grade_data.grade
        if grade_data.feedback is not None:
            submission.feedback = grade_data.feedback
            
        await db.commit()
        await db.refresh(submission)
        return submission
