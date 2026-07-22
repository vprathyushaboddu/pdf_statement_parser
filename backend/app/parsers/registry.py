from app.parsers.base import StatementTypeParser
from app.parsers.example_statement_type.parser import ExampleStatementTypeParser

#: Every supported statement-type parser, keyed by StatementType.parser_key.
#: Add a new statement type by implementing StatementTypeParser in its own
#: module under app/parsers/<statement_type>/ and registering an instance here.
_PARSERS: list[StatementTypeParser] = [
    ExampleStatementTypeParser(),
]

#: Below this confidence, we don't guess — the caller should fail with
#: "unsupported/ambiguous" and ask the user to pick a statement type manually (FR-2, FR-4).
DETECTION_THRESHOLD = 0.5


def get_parser(parser_key: str) -> StatementTypeParser | None:
    return next((p for p in _PARSERS if p.statement_type_key == parser_key), None)


def detect_parser(pdf_text: str) -> tuple[StatementTypeParser, float] | None:
    """Run every registered parser's cheap detect() and return the best match.

    Returns None if no parser clears DETECTION_THRESHOLD.
    """
    scored = [(parser, parser.detect(pdf_text)) for parser in _PARSERS]
    scored.sort(key=lambda pair: pair[1], reverse=True)

    if not scored or scored[0][1] < DETECTION_THRESHOLD:
        return None
    return scored[0]


def all_parsers() -> list[StatementTypeParser]:
    return list(_PARSERS)
