from datetime import date
from decimal import Decimal

from app.parsers.common.normalize import parse_amount, parse_date


def test_parse_amount_strips_thousands_separators():
    assert parse_amount("1,234.56") == Decimal("1234.56")


def test_parse_amount_blank_returns_none():
    assert parse_amount("") is None
    assert parse_amount("-") is None
    assert parse_amount(None) is None


def test_parse_amount_handles_dr_cr_suffix():
    assert parse_amount("500.00 CR") == Decimal("500.00")


def test_parse_amount_handles_parentheses_as_negative():
    assert parse_amount("(100.00)") == Decimal("-100.00")


def test_parse_date_tries_multiple_formats():
    formats = ["%d/%m/%Y", "%d-%b-%Y"]
    assert parse_date("05/01/2026", formats) == date(2026, 1, 5)
    assert parse_date("05-Jan-2026", formats) == date(2026, 1, 5)


def test_parse_date_returns_none_when_no_format_matches():
    assert parse_date("not-a-date", ["%d/%m/%Y"]) is None
