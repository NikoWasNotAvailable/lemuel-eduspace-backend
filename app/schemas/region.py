from pydantic import BaseModel
from typing import Optional

class RegionBase(BaseModel):
    name: str

class RegionCreate(RegionBase):
    pass

class RegionUpdate(BaseModel):
    name: Optional[str] = None

class RegionResponse(RegionBase):
    id: int

    class Config:
        from_attributes = True
