from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import os

from app.core.database import get_async_db
from app.core.auth import get_current_user, require_roles
from app.models.user import User, UserRole
from app.services.session_attachment_service import SessionAttachmentService
from app.schemas.session_attachment import (
    SessionAttachmentResponse,
    SessionAttachmentWithUploaderResponse,
    SessionAttachmentListResponse,
    SessionAttachmentUpdate,
    FileUploadResponse
)

router = APIRouter(prefix="/session-attachments", tags=["session-attachments"])

@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    session_id: int = Query(..., description="Session ID to attach file to"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_roles([UserRole.admin, UserRole.teacher]))
):
    """Upload a file attachment for a session. Only admin and teachers can upload files."""
    try:
        attachment = await SessionAttachmentService.upload_file(
            db, file, session_id, current_user.id
        )
        
        return FileUploadResponse(
            success=True,
            message="File uploaded successfully",
            attachment_id=attachment.id,
            filename=attachment.filename
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file"
        )

@router.get("/session/{session_id}", response_model=SessionAttachmentListResponse)
async def get_session_attachments(
    session_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get all attachments for a specific session."""
    attachments = await SessionAttachmentService.get_attachments_by_session(db, session_id)
    
    return SessionAttachmentListResponse(
        attachments=attachments,
        total=len(attachments),
        session_id=session_id
    )

@router.get("/user/{user_id}", response_model=List[SessionAttachmentWithUploaderResponse])
async def get_user_attachments(
    user_id: int,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_roles([UserRole.admin, UserRole.teacher]))
):
    """Get all attachments uploaded by a specific user. Only admin and teachers can access."""
    attachments = await SessionAttachmentService.get_attachments_by_user(
        db, user_id, skip, limit
    )
    
    # Transform to include uploader information
    result = []
    for attachment in attachments:
        attachment_dict = {
            "id": attachment.id,
            "session_id": attachment.session_id,
            "filename": attachment.filename,
            "content_type": attachment.content_type,
            "file_size": attachment.file_size,
            "uploaded_by": attachment.uploaded_by,
            "created_at": attachment.created_at,
            "uploader_name": attachment.uploader.full_name if attachment.uploader else None,
            "uploader_email": attachment.uploader.email if attachment.uploader else None
        }
        result.append(SessionAttachmentWithUploaderResponse(**attachment_dict))
    
    return result

@router.get("/stats", response_model=dict)
async def get_attachment_stats(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_roles([UserRole.admin]))
):
    """Get attachment statistics. Only admin can access."""
    stats = await SessionAttachmentService.get_attachment_stats(db)
    return stats

@router.get("/{attachment_id}", response_model=SessionAttachmentWithUploaderResponse)
async def get_attachment(
    attachment_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get attachment by ID with uploader information."""
    attachment = await SessionAttachmentService.get_attachment_by_id(db, attachment_id)
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found"
        )
    
    attachment_dict = {
        "id": attachment.id,
        "session_id": attachment.session_id,
        "filename": attachment.filename,
        "content_type": attachment.content_type,
        "file_size": attachment.file_size,
        "uploaded_by": attachment.uploaded_by,
        "created_at": attachment.created_at,
        "uploader_name": attachment.uploader.full_name if attachment.uploader else None,
        "uploader_email": attachment.uploader.email if attachment.uploader else None
    }
    
    return SessionAttachmentWithUploaderResponse(**attachment_dict)

@router.get("/{attachment_id}/download")
async def download_attachment(
    attachment_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Download attachment file."""
    attachment = await SessionAttachmentService.get_attachment_by_id(db, attachment_id)
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found"
        )
    
    file_path = await SessionAttachmentService.get_attachment_file_path(db, attachment_id)
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    return FileResponse(
        path=file_path,
        filename=attachment.filename,
        media_type=attachment.content_type
    )

@router.put("/{attachment_id}", response_model=SessionAttachmentResponse)
async def update_attachment(
    attachment_id: int,
    attachment_update: SessionAttachmentUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_roles([UserRole.admin, UserRole.teacher]))
):
    """Update attachment information (filename only). Only admin and teachers can update."""
    attachment = await SessionAttachmentService.update_attachment(
        db, attachment_id, attachment_update
    )
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found"
        )
    
    return attachment

@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
    attachment_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_roles([UserRole.admin, UserRole.teacher]))
):
    """Delete attachment and its file. Only admin and teachers can delete."""
    # Check if attachment exists first
    attachment = await SessionAttachmentService.get_attachment_by_id(db, attachment_id)
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found"
        )
    
    # Additional check: only allow deletion if current user uploaded the file or is admin
    if (current_user.role != UserRole.admin and 
        attachment.uploaded_by != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own attachments"
        )
    
    deleted = await SessionAttachmentService.delete_attachment(db, attachment_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found"
        )
    
    return None

@router.post("/bulk-upload", response_model=List[FileUploadResponse])
async def bulk_upload_attachments(
    session_id: int = Query(..., description="Session ID to attach files to"),
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_roles([UserRole.admin, UserRole.teacher]))
):
    """Upload multiple file attachments for a session. Only admin and teachers can upload."""
    if len(files) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot upload more than 10 files at once"
        )
    
    results = []
    
    for file in files:
        try:
            attachment = await SessionAttachmentService.upload_file(
                db, file, session_id, current_user.id
            )
            
            results.append(FileUploadResponse(
                success=True,
                message="File uploaded successfully",
                attachment_id=attachment.id,
                filename=attachment.filename
            ))
            
        except HTTPException as e:
            results.append(FileUploadResponse(
                success=False,
                message=f"Failed to upload {file.filename}: {e.detail}",
                filename=file.filename
            ))
        except Exception as e:
            results.append(FileUploadResponse(
                success=False,
                message=f"Failed to upload {file.filename}: Unknown error",
                filename=file.filename
            ))
    
    return results