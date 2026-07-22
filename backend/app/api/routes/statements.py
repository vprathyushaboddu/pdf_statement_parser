import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_statement_or_404
from app.db.session import get_db
from app.models.statement import Statement, StatementStatus
from app.models.statement_type import StatementType
from app.schemas.statement import ReprocessRequest, StatementDetail, StatementSummary
from app.services.processing_service import process_statement_task
from app.services.statement_service import create_statement, ensure_current_workbook
from app.storage.file_store import delete_statement_files

router = APIRouter(prefix="/statements", tags=["statements"])


@router.post("", response_model=list[StatementSummary], status_code=202)
def upload_statements(
    background_tasks: BackgroundTasks,
    files: list[UploadFile],
    statement_type_id: int = Form(...),
    db: Session = Depends(get_db),
) -> list[Statement]:
    """Upload one or more PDFs, all as a single, explicitly chosen statement type.

    There is no auto-detection: the caller must say up front which statement
    type these files are, and that exact type's parser is what gets used —
    never a guessed/best-match one.
    """
    statement_type = db.get(StatementType, statement_type_id)
    if statement_type is None:
        raise HTTPException(status_code=404, detail=f"Statement type id {statement_type_id} not found")

    return [create_statement(db, f, statement_type_id, background_tasks) for f in files]


@router.get("", response_model=list[StatementSummary])
def list_statements(
    status: StatementStatus | None = None, db: Session = Depends(get_db)
) -> list[Statement]:
    query = db.query(Statement).order_by(Statement.uploaded_at.desc())
    if status is not None:
        query = query.filter(Statement.status == status)
    return query.all()


@router.get("/{statement_id}", response_model=StatementDetail)
def get_statement(statement: Statement = Depends(get_statement_or_404)) -> Statement:
    return statement


@router.post("/{statement_id}/reprocess", response_model=StatementDetail)
def reprocess_statement(
    background_tasks: BackgroundTasks,
    payload: ReprocessRequest,
    statement: Statement = Depends(get_statement_or_404),
    db: Session = Depends(get_db),
) -> Statement:
    """Re-run parsing, optionally against a different statement type.

    Omit `statement_type_id` to re-run with the statement's existing type
    (e.g. after fixing that type's parser code); pass it to explicitly
    re-categorize the statement to a different type instead.
    """
    statement_type_id = payload.statement_type_id or statement.statement_type_id

    statement_type = db.get(StatementType, statement_type_id)
    if statement_type is None:
        raise HTTPException(status_code=404, detail=f"Statement type id {statement_type_id} not found")

    statement.statement_type_id = statement_type_id
    statement.status = StatementStatus.QUEUED
    statement.error_message = None
    db.commit()

    background_tasks.add_task(process_statement_task, statement.id, statement_type_id)
    return statement


@router.get("/{statement_id}/download")
def download_statement(
    statement: Statement = Depends(get_statement_or_404), db: Session = Depends(get_db)
) -> FileResponse:
    if statement.status not in (StatementStatus.DONE, StatementStatus.NEEDS_REVIEW):
        raise HTTPException(status_code=409, detail=f"Statement is not ready (status={statement.status.value})")

    path = ensure_current_workbook(db, statement)
    filename = f"{statement.original_filename.rsplit('.', 1)[0]}.xlsx"
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename,
    )


@router.delete("/{statement_id}", status_code=204)
def delete_statement(
    statement: Statement = Depends(get_statement_or_404), db: Session = Depends(get_db)
) -> None:
    delete_statement_files(statement.pdf_path, statement.xlsx_path)
    db.delete(statement)
    db.commit()
