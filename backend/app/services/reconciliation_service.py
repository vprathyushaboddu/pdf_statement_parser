from decimal import Decimal

from app.parsers.base import ParsedStatement

#: Small tolerance for rounding differences in the source PDF's own figures.
TOLERANCE = Decimal("0.01")


def reconcile(parsed: ParsedStatement) -> bool:
    """Check opening + total credits - total debits == closing balance (FR-16).

    Returns False (and lets the caller mark the statement as needs_review)
    when balances are missing or don't reconcile, rather than assuming success.
    """
    if parsed.opening_balance is None or parsed.closing_balance is None:
        return False

    total_credit = sum((t.credit or Decimal(0) for t in parsed.transactions), Decimal(0))
    total_debit = sum((t.debit or Decimal(0) for t in parsed.transactions), Decimal(0))

    expected_closing = parsed.opening_balance + total_credit - total_debit
    return abs(expected_closing - parsed.closing_balance) <= TOLERANCE
