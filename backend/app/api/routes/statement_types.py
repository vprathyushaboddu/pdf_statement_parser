from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.statement import Statement
from app.models.statement_type import StatementType
from app.schemas.statement_type import StatementTypeCreate, StatementTypeOut, StatementTypeUpdate
from app.services import statement_type_service

router = APIRouter(prefix="/statement-types", tags=["statement-types"])


@router.get("", response_model=list[StatementTypeOut])
def list_statement_types(db: Session = Depends(get_db)) -> list[StatementType]:
    return db.query(StatementType).order_by(StatementType.name).all()


@router.post("", response_model=StatementTypeOut, status_code=201)
def create_statement_type(
    payload: StatementTypeCreate, db: Session = Depends(get_db)
) -> StatementType:
    existing = db.query(StatementType).filter(StatementType.name == payload.name).first()
    if existing is not None:
        raise HTTPException(status_code=409, detail=f"Statement type '{payload.name}' already exists.")

    return statement_type_service.create_statement_type(db, payload.name)


@router.patch("/{statement_type_id}", response_model=StatementTypeOut)
def rename_statement_type(
    statement_type_id: int, payload: StatementTypeUpdate, db: Session = Depends(get_db)
) -> StatementType:
    statement_type = db.get(StatementType, statement_type_id)
    if statement_type is None:
        raise HTTPException(status_code=404, detail="Statement type not found")

    statement_type.name = payload.name
    db.commit()
    db.refresh(statement_type)
    return statement_type


@router.delete("/{statement_type_id}", status_code=204)
def delete_statement_type(statement_type_id: int, db: Session = Depends(get_db)) -> None:
    statement_type = db.get(StatementType, statement_type_id)
    if statement_type is None:
        raise HTTPException(status_code=404, detail="Statement type not found")

    in_use = db.query(Statement).filter(Statement.statement_type_id == statement_type_id).first()
    if in_use is not None:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete a statement type that has statements referencing it.",
        )

    db.delete(statement_type)
    db.commit()
