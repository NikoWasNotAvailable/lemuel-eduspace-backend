from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from app.models.region import Region
from app.schemas.region import RegionCreate, RegionUpdate

class RegionService:
    """Service layer for region operations."""

    @staticmethod
    async def create_region(db: AsyncSession, region_data: RegionCreate) -> Region:
        """Create a new region."""
        try:
            db_region = Region(name=region_data.name)
            db.add(db_region)
            await db.commit()
            await db.refresh(db_region)
            return db_region
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Region with this name already exists"
            )

    @staticmethod
    async def get_region_by_id(db: AsyncSession, region_id: int) -> Optional[Region]:
        """Get region by ID."""
        result = await db.execute(select(Region).where(Region.id == region_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all_regions(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Region]:
        """Get all regions."""
        result = await db.execute(select(Region).offset(skip).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def update_region(db: AsyncSession, region_id: int, region_update: RegionUpdate) -> Optional[Region]:
        """Update a region."""
        db_region = await RegionService.get_region_by_id(db, region_id)
        if not db_region:
            return None

        if region_update.name:
            db_region.name = region_update.name

        try:
            await db.commit()
            await db.refresh(db_region)
            return db_region
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Region name already exists"
            )

    @staticmethod
    async def delete_region(db: AsyncSession, region_id: int) -> bool:
        """Delete a region."""
        db_region = await RegionService.get_region_by_id(db, region_id)
        if not db_region:
            return False

        await db.delete(db_region)
        await db.commit()
        return True
