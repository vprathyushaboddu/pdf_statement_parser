from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass
class ParsedTransaction:
    row_number: int
    txn_date: date
    description: str
    debit: Decimal | None
    credit: Decimal | None
    balance: Decimal | None


@dataclass
class ParsedStatement:
    opening_balance: Decimal | None
    closing_balance: Decimal | None
    transactions: list[ParsedTransaction]


class StatementTypeParser(ABC):
    """Contract every statement-type-specific parser implements.

    A "statement type" is a specific bank + layout combination (a bank could
    have more than one, e.g. savings vs. credit card). Adding support for a
    new one means adding a new module implementing this interface and
    registering it in `registry.py` — existing parsers, the API layer, and
    the Excel generator should never need to change.
    """

    #: Unique key stored in StatementType.parser_key and used by the registry.
    statement_type_key: str
    #: Human-readable name shown in the UI's statement-type list/selector.
    display_name: str

    @abstractmethod
    def detect(self, pdf_text: str) -> float:
        """Return a confidence score in [0, 1] that this PDF matches this statement type.

        Should be cheap (regex/substring checks against known header text,
        account-statement phrasing, IFSC prefixes, etc.) — full parsing
        happens only after a parser is selected.
        """
        raise NotImplementedError

    @abstractmethod
    def parse(self, pdf_path: str) -> ParsedStatement:
        """Extract every transaction plus opening/closing balance from the PDF.

        Implementations own reconstructing multi-line transactions, stripping
        headers/footers/page-break artifacts, and normalizing dates/amounts —
        callers only ever see fully-normalized ParsedTransaction rows.
        """
        raise NotImplementedError
