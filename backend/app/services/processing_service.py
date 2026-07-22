import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.statement import Statement, StatementStatus
from app.models.statement_type import StatementType
from app.models.transaction import Transaction
from app.parsers.base import ParsedStatement
from app.parsers.common.pdf_text import has_extractable_text
from app.parsers.registry import get_parser
from app.services import excel_service
from app.services.exceptions import ParsingError
from app.services.reconciliation_service import reconcile
from app.storage.file_store import output_path


def process_statement_task(statement_id: uuid.UUID, statement_type_id: int) -> None:
    """Background-task entrypoint: owns its own DB session.

    Must not reuse the request-scoped session from a route's `Depends(get_db)`
    — that session's lifetime isn't guaranteed to outlast a BackgroundTask,
    so this opens and closes a dedicated one instead.
    """
    db = SessionLocal()
    try:
        process_statement(db, statement_id, statement_type_id)
    finally:
        db.close()


def process_statement(db: Session, statement_id: uuid.UUID, statement_type_id: int) -> None:
    """Orchestrates parse -> reconcile -> persist -> generate xlsx.

    There is no auto-detection: `statement_type_id` is a required, caller-
    supplied choice, and exactly that type's registered parser is used — never
    a best-guess match. Never leaves a statement looking like it succeeded
    when it didn't (FR-18): any failure sets status=failed with a specific
    error_message.
    """
    statement = db.get(Statement, statement_id)
    if statement is None:
        return

    statement.status = StatementStatus.PARSING
    db.commit()

    try:
        parsed, statement_type = _parse_with_statement_type(db, statement, statement_type_id)
        _persist_result(db, statement, parsed, statement_type)
    except ParsingError as exc:
        statement.status = StatementStatus.FAILED
        statement.error_message = str(exc)
        db.commit()
    except Exception as exc:  # noqa: BLE001 - last resort, must not fail silently
        statement.status = StatementStatus.FAILED
        statement.error_message = f"Unexpected error while processing: {exc}"
        db.commit()


def _parse_with_statement_type(
    db: Session, statement: Statement, statement_type_id: int
) -> tuple[ParsedStatement, StatementType]:
    if not has_extractable_text(statement.pdf_path):
        raise ParsingError(
            "No extractable text layer found — this looks like a scanned PDF, "
            "which isn't supported (only digital/text-based statements are)."
        )

    statement_type = db.get(StatementType, statement_type_id)
    if statement_type is None:
        raise ParsingError(f"Statement type id {statement_type_id} not found.")

    parser = get_parser(statement_type.parser_key)
    if parser is None:
        raise ParsingError(f"No parser registered for statement type '{statement_type.name}'.")

    parsed = parser.parse(statement.pdf_path)
    if not parsed.transactions:
        raise ParsingError("Parser ran but found zero transactions — statement layout may have changed.")

    return parsed, statement_type


def _persist_result(
    db: Session, statement: Statement, parsed: ParsedStatement, statement_type: StatementType
) -> None:
    statement.statement_type_id = statement_type.id
    statement.opening_balance = parsed.opening_balance
    statement.closing_balance = parsed.closing_balance
    statement.reconciliation_passed = reconcile(parsed)

    # Clear any prior transactions (relevant on reprocess).
    for existing in list(statement.transactions):
        db.delete(existing)
    db.flush()

    for txn in parsed.transactions:
        db.add(
            Transaction(
                statement_id=statement.id,
                row_number=txn.row_number,
                txn_date=txn.txn_date,
                description=txn.description,
                debit=txn.debit,
                credit=txn.credit,
                balance=txn.balance,
            )
        )
    db.flush()
    db.refresh(statement)

    xlsx_path = output_path(statement.id, f"{statement.id}.xlsx")
    excel_service.save_workbook(statement.transactions, xlsx_path)
    statement.xlsx_path = xlsx_path

    statement.status = (
        StatementStatus.DONE if statement.reconciliation_passed else StatementStatus.NEEDS_REVIEW
    )
    statement.processed_at = datetime.now(timezone.utc)
    db.commit()
