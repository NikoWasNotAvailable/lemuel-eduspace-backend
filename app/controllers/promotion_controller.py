from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.core.auth import get_admin_user
from app.models.user import User
from app.schemas.promotion import (
    PromotionPreviewRequest, 
    PromotionPreviewResponse, 
    PromotionConfirmRequest,
    PromotionHistoryResponse
)
from app.services.promotion_service import PromotionService

router = APIRouter(prefix="/promotions", tags=["promotions"])

@router.post("/preview", response_model=PromotionPreviewResponse)
async def preview_promotion(
    request: PromotionPreviewRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Preview mass promotion of students.
    Calculates next grade and assigns classes deterministically.
    Does not modify the database.
    """
    return await PromotionService.preview_promotion(db, request.exclude_student_ids)

@router.post("/confirm", response_model=PromotionHistoryResponse)
async def confirm_promotion(
    request: PromotionConfirmRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Apply mass promotion.
    Updates student grades and classes.
    Creates a history record for undo.
    """
    history = await PromotionService.confirm_promotion(db, request.exclude_student_ids)
    
    if not history:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No students to promote or no classes available"
        )
        
    # Calculate summary for response
    summary = {"promoted": 0, "graduated": 0}
    for detail in history.details:
        if detail['status'] == 'promoted':
            summary['promoted'] += 1
        elif detail['status'] == 'graduated':
            summary['graduated'] += 1
            
    return PromotionHistoryResponse(
        id=history.id,
        promotion_date=history.promotion_date,
        status=history.status,
        summary=summary
    )

@router.post("/{history_id}/undo")
async def undo_promotion(
    history_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Undo a previous mass promotion.
    Reverts students to their old grades and classes.
    """
    success = await PromotionService.undo_promotion(db, history_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to undo promotion. History not found or already reverted."
        )
        
    return {"message": "Promotion undone successfully"}
