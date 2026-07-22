import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.statement_type import StatementType
    from app.models.transaction import Transaction


class StatementStatus(str, enum.Enum):
    QUEUED = "queued"
    PARSING = "parsing"
    NEEDS_REVIEW = "needs_review"
    DONE = "done"
    FAILED = "failed"


class Statement(Base):
    __tablename__ = "statements"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    statement_type_id: Mapped[int] = mapped_column(ForeignKey("statement_types.id"), nullable=False)

    original_filename: Mapped[str] = mapped_column(String(255))
    pdf_path: Mapped[str] = mapped_column(String(500))
    xlsx_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    status: Mapped[StatementStatus] = mapped_column(
        Enum(StatementStatus, name="statement_status", native_enum=False, length=20),
        default=StatementStatus.QUEUED,
        server_default=StatementStatus.QUEUED.value,
    )

    opening_balance: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    closing_balance: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    reconciliation_passed: Mapped[bool | None] = mapped_column(nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    uploaded_at: Mapped[datetime] = mapped_column(server_default=func.now())
    processed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    statement_type: Mapped["StatementType"] = relationship(back_populates="statements")
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="statement",
        cascade="all, delete-orphan",
        order_by="Transaction.row_number",
    )
