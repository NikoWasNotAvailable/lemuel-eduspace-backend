from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class BannerBase(BaseModel):
    image_url: str
    description: Optional[str] = None
    region_id: int

class BannerCreate(BannerBase):
    pass

class BannerUpdate(BaseModel):
    image_url: Optional[str] = None
    description: Optional[str] = None
    region_id: Optional[int] = None

class BannerResponse(BannerBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
