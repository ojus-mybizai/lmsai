import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID, TimestampMixin
from app.models.user import User


class Customer(TimestampMixin, Base):
    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    primary_mobile: Mapped[str] = mapped_column(String(20), nullable=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    type_mappings: Mapped[list["CustomerTypeMap"]] = relationship(
        "CustomerTypeMap", back_populates="customer", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_customers_primary_mobile", "primary_mobile"),
        Index("ix_customers_email", "email"),
    )


class CustomerType(TimestampMixin, Base):
    __tablename__ = "customer_types"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    mappings: Mapped[list["CustomerTypeMap"]] = relationship("CustomerTypeMap", back_populates="customer_type")


class CustomerTypeSource(str, enum.Enum):
    upload = "upload"
    call = "call"
    manual = "manual"


class CustomerTypeMap(Base):
    __tablename__ = "customer_type_maps"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("customers.id"), nullable=False, index=True)
    customer_type_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("customer_types.id"), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    added_by_user: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    customer: Mapped[Customer] = relationship("Customer", back_populates="type_mappings")
    customer_type: Mapped[CustomerType] = relationship("CustomerType", back_populates="mappings")
    added_by: Mapped[User | None] = relationship(User)

    __table_args__ = (
        UniqueConstraint("customer_id", "customer_type_id", name="uq_customer_type_map"),
    )


class UploadStatus(str, enum.Enum):
    processing = "processing"
    completed = "completed"
    failed = "failed"


class UploadBatch(Base):
    __tablename__ = "upload_batches"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("users.id"), nullable=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    total_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    new_customers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    merged_customers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=UploadStatus.processing.value, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    uploaded_user: Mapped[User | None] = relationship(User)


class AssignmentStatus(str, enum.Enum):
    open = "open"
    submitted = "submitted"
    locked = "locked"


class CallerAssignment(Base):
    __tablename__ = "caller_assignments"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    caller_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    assignment_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default=AssignmentStatus.open.value, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    caller: Mapped[User] = relationship(User)
    items: Mapped[list["CallerAssignmentItem"]] = relationship(
        "CallerAssignmentItem", back_populates="assignment", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("caller_id", "assignment_date", name="uq_caller_assignment_date"),
    )


class CallStatus(str, enum.Enum):
    pending = "pending"
    called = "called"
    follow_up = "follow_up"
    not_reachable = "not_reachable"


class CallerAssignmentItem(Base):
    __tablename__ = "caller_assignment_items"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    assignment_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("caller_assignments.id"), nullable=False, index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("customers.id"), nullable=False, index=True)
    call_status: Mapped[str] = mapped_column(String(50), default=CallStatus.pending.value, nullable=False)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    assignment: Mapped[CallerAssignment] = relationship("CallerAssignment", back_populates="items")
    customer: Mapped[Customer] = relationship("Customer")
    remarks: Mapped[list["CallRemark"]] = relationship(
        "CallRemark", back_populates="assignment_item", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("assignment_id", "customer_id", name="uq_assignment_customer"),
    )


class CallRemark(Base):
    __tablename__ = "call_remarks"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    assignment_item_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("caller_assignment_items.id"), nullable=False, index=True)
    remark_text: Mapped[str] = mapped_column(Text, nullable=False)
    outcome: Mapped[str] = mapped_column(String(50), nullable=False)
    follow_up_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    assignment_item: Mapped[CallerAssignmentItem] = relationship("CallerAssignmentItem", back_populates="remarks")
    author: Mapped[User] = relationship(User)

    __table_args__ = (
        Index("ix_call_remarks_follow_up_date", "follow_up_date"),
    )
