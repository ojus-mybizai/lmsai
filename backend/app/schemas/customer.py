from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, validator

from app.schemas.customer_type import CustomerTypeRead


class CustomerBase(BaseModel):
    name: str
    primary_mobile: Optional[str] = None
    email: Optional[EmailStr] = None

    @validator("primary_mobile")
    def normalize_mobile(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return v
        digits = "".join(ch for ch in v if ch.isdigit())
        if len(digits) < 7:
            return v
        if digits.startswith("91") and len(digits) == 12:
            digits = digits[2:]
        return digits


class CustomerCreate(CustomerBase):
    customer_type_ids: list[UUID]
    source: str = "manual"


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    primary_mobile: Optional[str] = None
    email: Optional[EmailStr] = None
    customer_type_ids: Optional[list[UUID]] = None


class CustomerTypeMapRead(BaseModel):
    id: UUID
    customer_type: CustomerTypeRead
    source: str
    added_by_user: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True


class CustomerRead(CustomerBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    types: list[CustomerTypeMapRead] = []

    class Config:
        from_attributes = True
