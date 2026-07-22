from datetime import date
from decimal import Decimal

from app.models.transaction import Transaction
from app.services.excel_service import build_workbook


def _txn(row_number, debit=None, credit=None, balance=None) -> Transaction:
    return Transaction(
        row_number=row_number,
        txn_date=date(2026, 1, row_number),
        description=f"txn {row_number}",
        debit=Decimal(debit) if debit is not None else None,
        credit=Decimal(credit) if credit is not None else None,
        balance=Decimal(balance) if balance is not None else None,
    )


def test_build_workbook_writes_header_and_rows_in_order():
    transactions = [
        _txn(2, credit="500.00", balance="1300.00"),
        _txn(1, debit="200.00", balance="800.00"),
    ]

    wb = build_workbook(transactions)
    ws = wb.active

    assert [c.value for c in ws[1]] == ["Date", "Description", "Debit", "Credit", "Balance"]
    # Rows must come out ordered by row_number regardless of input order (FR-12).
    assert ws.cell(row=2, column=2).value == "txn 1"
    assert ws.cell(row=2, column=3).value == 200.0
    assert ws.cell(row=3, column=2).value == "txn 2"
    assert ws.cell(row=3, column=4).value == 500.0
