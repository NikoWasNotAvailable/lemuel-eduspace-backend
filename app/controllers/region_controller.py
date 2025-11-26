from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.auth import get_admin_user
from app.schemas.region import RegionCreate, RegionResponse, RegionUpdate
from app.services.region_service import RegionService
from app.models.user import User

router = APIRouter(
    prefix="/regions",
    tags=["regions"]
)

@router.post("/", response_model=RegionResponse, status_code=status.HTTP_201_CREATED)
async def create_region(
    region: RegionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Create a new region.
    Only admins can create regions.
    """
    return await RegionService.create_region(db, region)

@router.get("/", response_model=List[RegionResponse])
async def read_regions(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_active_user) # Assuming authenticated users can read regions
):
    """
    Retrieve all regions.
    """
    return await RegionService.get_all_regions(db, skip=skip, limit=limit)

@router.get("/{region_id}", response_model=RegionResponse)
async def read_region(
    region_id: int,
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve a specific region by ID.
    """
    region = await RegionService.get_region_by_id(db, region_id)
    if not region:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Region not found"
        )
    return region

@router.put("/{region_id}", response_model=RegionResponse)
async def update_region(
    region_id: int,
    region_update: RegionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Update a region.
    Only admins can update regions.
    """
    updated_region = await RegionService.update_region(db, region_id, region_update)
    if not updated_region:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Region not found"
        )
    return updated_region

@router.delete("/{region_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_region(
    region_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Delete a region.
    Only admins can delete regions.
    """
    success = await RegionService.delete_region(db, region_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Region not found"
        )
    return None
