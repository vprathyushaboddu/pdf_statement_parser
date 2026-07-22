class ParsingError(Exception):
    """Raised when a statement can't be safely parsed (FR-3, FR-4, FR-17).

    Callers must turn this into a `failed` status + error_message rather than
    letting the statement look like it succeeded (FR-18).
    """
