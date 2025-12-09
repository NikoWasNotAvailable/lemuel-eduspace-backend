from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from app.models.banner import Banner
from app.schemas.banner import BannerCreate, BannerUpdate

class BannerService:
    @staticmethod
    async def get_banners(db: AsyncSession, region_id: Optional[int] = None) -> List[Banner]:
        query = select(Banner)
        if region_id:
            query = query.filter(Banner.region_id == region_id)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_banner(db: AsyncSession, banner_id: int) -> Optional[Banner]:
        result = await db.execute(select(Banner).filter(Banner.id == banner_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_banner(db: AsyncSession, banner_data: BannerCreate) -> Banner:
        db_banner = Banner(**banner_data.model_dump())
        db.add(db_banner)
        await db.commit()
        await db.refresh(db_banner)
        return db_banner

    @staticmethod
    async def update_banner(db: AsyncSession, banner_id: int, banner_data: BannerUpdate) -> Optional[Banner]:
        db_banner = await BannerService.get_banner(db, banner_id)
        if not db_banner:
            return None
        
        update_data = banner_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_banner, key, value)
            
        await db.commit()
        await db.refresh(db_banner)
        return db_banner

    @staticmethod
    async def delete_banner(db: AsyncSession, banner_id: int) -> bool:
        db_banner = await BannerService.get_banner(db, banner_id)
        if not db_banner:
            return False
            
        await db.delete(db_banner)
        await db.commit()
        return True
