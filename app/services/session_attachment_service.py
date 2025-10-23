import os
import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload, joinedload
from app.models.session_attachment import SessionAttachment
from app.models.session import Session
from app.models.user import User
from app.schemas.session_attachment import SessionAttachmentCreate, SessionAttachmentUpdate
from fastapi import HTTPException, status, UploadFile
from pathlib import Path

class SessionAttachmentService:
    
    # Configuration
    UPLOAD_DIRECTORY = "uploads/session_attachments"
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = {
        '.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx',
        '.txt', '.rtf', '.jpg', '.jpeg', '.png', '.gif', '.zip',
        '.rar', '.mp4', '.avi', '.mov', '.mp3', '.wav'
    }
    
    @staticmethod
    def _ensure_upload_directory():
        """Ensure the upload directory exists."""
        Path(SessionAttachmentService.UPLOAD_DIRECTORY).mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def _get_file_extension(filename: str) -> str:
        """Get file extension from filename."""
        return Path(filename).suffix.lower()
    
    @staticmethod
    def _is_allowed_file(filename: str) -> bool:
        """Check if file extension is allowed."""
        extension = SessionAttachmentService._get_file_extension(filename)
        return extension in SessionAttachmentService.ALLOWED_EXTENSIONS
    
    @staticmethod
    def _generate_unique_filename(original_filename: str) -> str:
        """Generate a unique filename to prevent conflicts."""
        extension = SessionAttachmentService._get_file_extension(original_filename)
        unique_id = str(uuid.uuid4())
        return f"{unique_id}{extension}"
    
    @staticmethod
    async def upload_file(
        db: AsyncSession,
        file: UploadFile,
        session_id: int,
        uploaded_by: int
    ) -> SessionAttachment:
        """Upload and save file for a session."""
        # Check if session exists
        session_result = await db.execute(select(Session).where(Session.id == session_id))
        session = session_result.scalar_one_or_none()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Check if user exists
        user_result = await db.execute(select(User).where(User.id == uploaded_by))
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required"
            )
        
        if not SessionAttachmentService._is_allowed_file(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File type not allowed"
            )
        
        # Read file content to check size
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > SessionAttachmentService.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum allowed size of {SessionAttachmentService.MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )
        
        # Ensure upload directory exists
        SessionAttachmentService._ensure_upload_directory()
        
        # Generate unique filename and save file
        unique_filename = SessionAttachmentService._generate_unique_filename(file.filename)
        file_path = os.path.join(SessionAttachmentService.UPLOAD_DIRECTORY, unique_filename)
        
        try:
            # Save file to disk
            with open(file_path, "wb") as buffer:
                buffer.write(file_content)
            
            # Create database record
            attachment_data = SessionAttachmentCreate(
                session_id=session_id,
                filename=file.filename,
                file_path=file_path,
                file_size=file_size,
                content_type=file.content_type or "application/octet-stream",
                uploaded_by=uploaded_by
            )
            
            attachment = SessionAttachment(**attachment_data.model_dump())
            db.add(attachment)
            await db.commit()
            await db.refresh(attachment)
            
            return attachment
            
        except Exception as e:
            # Clean up file if database operation fails
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save file"
            )
    
    @staticmethod
    async def get_attachment_by_id(db: AsyncSession, attachment_id: int) -> Optional[SessionAttachment]:
        """Get attachment by ID with session and uploader information."""
        query = select(SessionAttachment).options(
            joinedload(SessionAttachment.session),
            joinedload(SessionAttachment.uploader)
        ).where(SessionAttachment.id == attachment_id)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_attachments_by_session(
        db: AsyncSession,
        session_id: int
    ) -> List[SessionAttachment]:
        """Get all attachments for a specific session."""
        # Check if session exists
        session_result = await db.execute(select(Session).where(Session.id == session_id))
        session = session_result.scalar_one_or_none()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        query = select(SessionAttachment).options(
            joinedload(SessionAttachment.uploader)
        ).where(SessionAttachment.session_id == session_id).order_by(SessionAttachment.created_at.asc())
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def update_attachment(
        db: AsyncSession,
        attachment_id: int,
        attachment_update: SessionAttachmentUpdate
    ) -> Optional[SessionAttachment]:
        """Update attachment information (filename only)."""
        attachment = await SessionAttachmentService.get_attachment_by_id(db, attachment_id)
        if not attachment:
            return None
        
        # Update fields
        update_data = attachment_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(attachment, field, value)
        
        await db.commit()
        await db.refresh(attachment)
        return attachment
    
    @staticmethod
    async def delete_attachment(db: AsyncSession, attachment_id: int) -> bool:
        """Delete attachment and its associated file."""
        attachment = await SessionAttachmentService.get_attachment_by_id(db, attachment_id)
        if not attachment:
            return False
        
        # Delete file from disk
        if os.path.exists(attachment.file_path):
            try:
                os.remove(attachment.file_path)
            except OSError:
                # Log the error but continue with database deletion
                pass
        
        # Delete database record
        await db.delete(attachment)
        await db.commit()
        return True
    
    @staticmethod
    async def get_attachment_file_path(db: AsyncSession, attachment_id: int) -> Optional[str]:
        """Get file path for downloading attachment."""
        attachment = await SessionAttachmentService.get_attachment_by_id(db, attachment_id)
        if not attachment:
            return None
        
        if not os.path.exists(attachment.file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found on disk"
            )
        
        return attachment.file_path
    
    @staticmethod
    async def get_attachments_by_user(
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[SessionAttachment]:
        """Get all attachments uploaded by a specific user."""
        query = select(SessionAttachment).options(
            joinedload(SessionAttachment.session).joinedload(Session.subject)
        ).where(SessionAttachment.uploaded_by == user_id).order_by(
            SessionAttachment.created_at.desc()
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_attachment_stats(db: AsyncSession) -> dict:
        """Get attachment statistics."""
        from sqlalchemy import func
        
        # Total attachments
        total_result = await db.execute(select(func.count(SessionAttachment.id)))
        total_attachments = total_result.scalar()
        
        # Total file size
        size_result = await db.execute(select(func.sum(SessionAttachment.file_size)))
        total_size = size_result.scalar() or 0
        
        # Attachments by content type
        type_result = await db.execute(
            select(SessionAttachment.content_type, func.count(SessionAttachment.id))
            .group_by(SessionAttachment.content_type)
            .order_by(func.count(SessionAttachment.id).desc())
        )
        attachments_by_type = dict(type_result.fetchall())
        
        return {
            "total_attachments": total_attachments,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "attachments_by_type": attachments_by_type
        }