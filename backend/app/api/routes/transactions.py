import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_statement_or_404
from app.db.session import get_db
from app.models.statement import Statement
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionOut, TransactionUpdate

router = APIRouter(prefix="/statements/{statement_id}/transactions", tags=["transactions"])


@router.get("", response_model=list[TransactionOut])
def list_transactions(statement: Statement = Depends(get_statement_or_404)) -> list[Transaction]:
    return statement.transactions


@router.patch("/{txn_id}", response_model=TransactionOut)
def update_transaction(
    txn_id: uuid.UUID,
    payload: TransactionUpdate,
    statement: Statement = Depends(get_statement_or_404),
    db: Session = Depends(get_db),
) -> Transaction:
    txn = next((t for t in statement.transactions if t.id == txn_id), None)
    if txn is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(txn, field, value)

    db.commit()
    db.refresh(txn)
    return txn
