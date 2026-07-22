import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.statement import StatementStatus
from app.schemas.statement_type import StatementTypeOut


class StatementSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    original_filename: str
    status: StatementStatus
    statement_type: StatementTypeOut
    uploaded_at: datetime


class StatementDetail(StatementSummary):
    opening_balance: float | None
    closing_balance: float | None
    reconciliation_passed: bool | None
    error_message: str | None
    processed_at: datetime | None


class ReprocessRequest(BaseModel):
    statement_type_id: int | None = None
