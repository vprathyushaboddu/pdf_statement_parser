import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    row_number: int
    txn_date: date
    description: str
    debit: float | None
    credit: float | None
    balance: float | None


class TransactionUpdate(BaseModel):
    txn_date: date | None = None
    description: str | None = None
    debit: float | None = None
    credit: float | None = None
    balance: float | None = None
