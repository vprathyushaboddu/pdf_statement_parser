from datetime import date
from decimal import Decimal

from app.parsers.base import ParsedStatement, ParsedTransaction
from app.services.reconciliation_service import reconcile


def _txn(row, debit=None, credit=None, balance=None) -> ParsedTransaction:
    return ParsedTransaction(
        row_number=row,
        txn_date=date(2026, 1, row),
        description=f"txn {row}",
        debit=Decimal(debit) if debit is not None else None,
        credit=Decimal(credit) if credit is not None else None,
        balance=Decimal(balance) if balance is not None else None,
    )


def test_reconcile_passes_when_balances_match():
    parsed = ParsedStatement(
        opening_balance=Decimal("1000.00"),
        closing_balance=Decimal("1300.00"),
        transactions=[
            _txn(1, debit="200.00", balance="800.00"),
            _txn(2, credit="500.00", balance="1300.00"),
        ],
    )
    assert reconcile(parsed) is True


def test_reconcile_fails_when_a_transaction_is_missing():
    parsed = ParsedStatement(
        opening_balance=Decimal("1000.00"),
        closing_balance=Decimal("1300.00"),
        transactions=[_txn(1, credit="100.00", balance="1100.00")],
    )
    assert reconcile(parsed) is False


def test_reconcile_fails_when_balances_missing():
    parsed = ParsedStatement(opening_balance=None, closing_balance=None, transactions=[])
    assert reconcile(parsed) is False
