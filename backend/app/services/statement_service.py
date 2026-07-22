import uuid

from fastapi import BackgroundTasks, UploadFile
from sqlalchemy.orm import Session

from app.models.statement import Statement
from app.services.processing_service import process_statement_task
from app.storage.file_store import output_path, save_upload
from app.services import excel_service


def create_statement(
    db: Session,
    upload: UploadFile,
    statement_type_id: int,
    background_tasks: BackgroundTasks,
) -> Statement:
    """Create a statement for an explicitly chosen statement type.

    There is no auto-detection step: the caller (API layer) has already
    validated that `statement_type_id` refers to a real StatementType, and
    that exact type's parser is the one `process_statement_task` will use —
    never a guessed/best-match one.
    """
    statement = Statement(
        id=uuid.uuid4(),
        statement_type_id=statement_type_id,
        original_filename=upload.filename or "statement.pdf",
        pdf_path="",  # filled in below once we know the id-based path
    )
    statement.pdf_path = save_upload(statement.id, upload)
    db.add(statement)
    db.commit()
    db.refresh(statement)

    background_tasks.add_task(process_statement_task, statement.id, statement_type_id)
    return statement


def ensure_current_workbook(db: Session, statement: Statement) -> str:
    """Regenerate the .xlsx from current DB rows if it's missing/stale.

    Keeps Postgres as the source of truth: if a transaction was PATCHed
    after the initial export, the download should reflect that edit rather
    than serving a now-stale file (architecture.md §10).
    """
    path = statement.xlsx_path or output_path(statement.id, f"{statement.id}.xlsx")
    excel_service.save_workbook(statement.transactions, path)
    if statement.xlsx_path != path:
        statement.xlsx_path = path
        db.commit()
    return path
