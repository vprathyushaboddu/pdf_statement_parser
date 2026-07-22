from sqlalchemy.orm import Session

from app.models.statement_type import StatementType
from app.parsers.registry import all_parsers


def sync_statement_types(db: Session) -> None:
    """Keep the `statement_types` table in sync with registered parsers on startup.

    The registry (code) is the source of truth for which statement types are
    supported; this just mirrors it into rows the API/UI can query and
    statements can foreign-key against.
    """
    existing = {st.parser_key: st for st in db.query(StatementType).all()}

    for parser in all_parsers():
        statement_type = existing.get(parser.statement_type_key)
        if statement_type is None:
            db.add(
                StatementType(name=parser.display_name, parser_key=parser.statement_type_key)
            )
        elif statement_type.name != parser.display_name:
            statement_type.name = parser.display_name

    db.commit()
