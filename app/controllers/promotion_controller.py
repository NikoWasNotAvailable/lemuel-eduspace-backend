from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.core.auth import get_admin_user
from app.models.user import User
from app.schemas.promotion import (
    PromotionPreviewRequest, 
    PromotionPreviewResponse, 
    PromotionConfirmRequest,
    PromotionHistoryResponse,
    PromotionHistoryListResponse,
    PromotionHistoryDetailResponse,
    StudentPromotionDetail
)
from app.services.promotion_service import PromotionService
from typing import List

router = APIRouter(prefix="/promotions", tags=["promotions"])

@router.get("/history", response_model=List[PromotionHistoryListResponse])
async def get_promotion_history(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Get all promotion history records.
    Returns list of promotions with summary statistics.
    """
    histories = await PromotionService.get_promotion_history(db)
    
    result = []
    for history in histories:
        # Calculate summary from details
        summary = {"promoted": 0, "graduated": 0}
        for detail in history.details:
            if detail.get('status') == 'promoted':
                summary['promoted'] += 1
            elif detail.get('status') == 'graduated':
                summary['graduated'] += 1
        
        result.append(PromotionHistoryListResponse(
            id=history.id,
            promotion_date=history.promotion_date,
            status=history.status.value if hasattr(history.status, 'value') else history.status,
            summary=summary,
            total_affected=len(history.details)
        ))
    
    return result

@router.get("/history/{history_id}", response_model=PromotionHistoryDetailResponse)
async def get_promotion_history_detail(
    history_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Get a specific promotion history record with full details.
    """
    history = await PromotionService.get_promotion_history_by_id(db, history_id)
    
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Promotion history not found"
        )
    
    # Calculate summary from details
    summary = {"promoted": 0, "graduated": 0}
    for detail in history.details:
        if detail.get('status') == 'promoted':
            summary['promoted'] += 1
        elif detail.get('status') == 'graduated':
            summary['graduated'] += 1
    
    # Convert dict details to StudentPromotionDetail objects
    details = [StudentPromotionDetail(**d) for d in history.details]
    
    return PromotionHistoryDetailResponse(
        id=history.id,
        promotion_date=history.promotion_date,
        status=history.status.value if hasattr(history.status, 'value') else history.status,
        summary=summary,
        total_affected=len(history.details),
        details=details
    )

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
