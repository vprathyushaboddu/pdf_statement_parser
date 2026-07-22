from datetime import date, datetime
from decimal import Decimal, InvalidOperation


def parse_date(raw: str, formats: list[str]) -> date | None:
    raw = raw.strip()
    for fmt in formats:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def parse_amount(raw: str | None) -> Decimal | None:
    """Normalize a bank-statement amount string to a Decimal.

    Strips thousands separators, currency symbols, and whitespace. Returns
    None for blank/dash placeholders banks use to mean "no value".
    """
    if raw is None:
        return None

    cleaned = raw.strip().replace(",", "").replace("₹", "").replace("Rs.", "").strip()
    if cleaned in ("", "-", "--", "NA", "N/A"):
        return None

    negative = False
    if cleaned.startswith("(") and cleaned.endswith(")"):
        negative = True
        cleaned = cleaned[1:-1]
    if cleaned.upper().endswith("CR") or cleaned.upper().endswith("DR"):
        cleaned = cleaned[:-2].strip()

    try:
        value = Decimal(cleaned)
    except InvalidOperation:
        return None

    return -value if negative else value
