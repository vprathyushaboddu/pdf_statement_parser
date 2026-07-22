"""Reference/template statement-type parser.

This is NOT a validated parser for any real bank — the actual list of
supported statement types is still open (see docs/requirements.md, "Supported
Banks"). It exists to give the StatementTypeParser interface a concrete,
working implementation to copy when the first real statement type is added,
and to make the API/services layer testable end-to-end before real sample
statements are available.

It assumes a fairly generic tabular layout: one table per page with a header
row containing Date / Description / Debit / Credit / Balance columns (in any
order, matched by name), and treats rows with no parseable date as a
continuation of the previous row's description (multi-line narration).

Once a real sample statement exists, copy this folder, rename
`statement_type_key` / `display_name`, tune `detect.py`'s signature phrases,
and adjust `_HEADER_ALIASES` / `_DATE_FORMATS` / the opening-closing balance
regexes to match that statement type's actual wording.
"""

import re
from decimal import Decimal

from app.parsers.base import ParsedStatement, ParsedTransaction, StatementTypeParser
from app.parsers.common.normalize import parse_amount, parse_date
from app.parsers.common.pdf_text import PageContent, full_text, load_pages
from app.parsers.example_statement_type.detect import confidence

_DATE_FORMATS = ["%d/%m/%Y", "%d-%m-%Y", "%d-%b-%Y", "%d %b %Y"]

_HEADER_ALIASES: dict[str, tuple[str, ...]] = {
    "date": ("date", "txn date", "value date"),
    "description": ("description", "narration", "particulars", "details"),
    "debit": ("debit", "withdrawal", "withdrawal amt", "dr"),
    "credit": ("credit", "deposit", "deposit amt", "cr"),
    "balance": ("balance", "closing balance", "running balance"),
}

_OPENING_BALANCE_RE = re.compile(r"opening balance[:\s]*[₹]?\s*([\d,]+\.\d{2})", re.IGNORECASE)
_CLOSING_BALANCE_RE = re.compile(r"closing balance[:\s]*[₹]?\s*([\d,]+\.\d{2})", re.IGNORECASE)


def _map_header(header_row: list[str | None]) -> dict[str, int]:
    column_index: dict[str, int] = {}
    for idx, cell in enumerate(header_row):
        if not cell:
            continue
        normalized = cell.strip().lower()
        for field, aliases in _HEADER_ALIASES.items():
            if field in column_index:
                continue
            if any(alias in normalized for alias in aliases):
                column_index[field] = idx
    return column_index


class ExampleStatementTypeParser(StatementTypeParser):
    statement_type_key = "example_statement_type"
    display_name = "Example Bank (template)"

    def detect(self, pdf_text: str) -> float:
        return confidence(pdf_text)

    def parse(self, pdf_path: str) -> ParsedStatement:
        pages = load_pages(pdf_path)
        text = full_text(pages)

        transactions = self._extract_transactions(pages)
        opening = self._match_balance(_OPENING_BALANCE_RE, text)
        closing = self._match_balance(_CLOSING_BALANCE_RE, text)

        if opening is None and transactions:
            first = transactions[0]
            delta = (first.credit or Decimal(0)) - (first.debit or Decimal(0))
            if first.balance is not None:
                opening = first.balance - delta
        if closing is None and transactions:
            closing = transactions[-1].balance

        return ParsedStatement(
            opening_balance=opening,
            closing_balance=closing,
            transactions=transactions,
        )

    def _match_balance(self, pattern: re.Pattern[str], text: str) -> Decimal | None:
        match = pattern.search(text)
        if not match:
            return None
        return parse_amount(match.group(1))

    def _extract_transactions(self, pages: list[PageContent]) -> list[ParsedTransaction]:
        transactions: list[ParsedTransaction] = []
        column_index: dict[str, int] = {}
        row_number = 0

        for page in pages:
            for table in page.tables:
                if not table:
                    continue

                data_rows = table
                header_map = _map_header(table[0])
                if header_map:
                    column_index = header_map
                    data_rows = table[1:]

                if not column_index:
                    # No header seen yet on any page — can't map columns safely.
                    continue

                for raw_row in data_rows:
                    txn = self._row_to_transaction(raw_row, column_index, row_number + 1)
                    if txn is not None:
                        transactions.append(txn)
                        row_number += 1
                    elif transactions:
                        # No parseable date: treat as a wrapped continuation
                        # line of the previous transaction's description.
                        continuation = self._cell(raw_row, column_index.get("description"))
                        if continuation:
                            transactions[-1].description = (
                                f"{transactions[-1].description} {continuation}".strip()
                            )

        return transactions

    @staticmethod
    def _cell(row: list[str | None], index: int | None) -> str:
        if index is None or index >= len(row) or row[index] is None:
            return ""
        return str(row[index]).strip()

    def _row_to_transaction(
        self, row: list[str | None], column_index: dict[str, int], row_number: int
    ) -> ParsedTransaction | None:
        date_str = self._cell(row, column_index.get("date"))
        txn_date = parse_date(date_str, _DATE_FORMATS) if date_str else None
        if txn_date is None:
            return None

        return ParsedTransaction(
            row_number=row_number,
            txn_date=txn_date,
            description=self._cell(row, column_index.get("description")),
            debit=parse_amount(self._cell(row, column_index.get("debit")) or None),
            credit=parse_amount(self._cell(row, column_index.get("credit")) or None),
            balance=parse_amount(self._cell(row, column_index.get("balance")) or None),
        )
