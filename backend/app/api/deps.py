import uuid

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.statement import Statement


def get_statement_or_404(statement_id: uuid.UUID, db: Session = Depends(get_db)) -> Statement:
    statement = db.get(Statement, statement_id)
    if statement is None:
        raise HTTPException(status_code=404, detail="Statement not found")
    return statement
