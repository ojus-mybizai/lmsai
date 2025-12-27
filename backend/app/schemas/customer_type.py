from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class CustomerTypeBase(BaseModel):
    name: str
    is_active: bool = True


class CustomerTypeCreate(CustomerTypeBase):
    pass


class CustomerTypeUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None


class CustomerTypeRead(CustomerTypeBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
