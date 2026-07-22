import re

from sqlalchemy.orm import Session

from app.models.statement_type import StatementType


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")
    return slug or "statement_type"


def _unique_parser_key(db: Session, base_slug: str) -> str:
    candidate = base_slug
    suffix = 2
    while db.query(StatementType).filter(StatementType.parser_key == candidate).first() is not None:
        candidate = f"{base_slug}_{suffix}"
        suffix += 1
    return candidate


def create_statement_type(db: Session, name: str) -> StatementType:
    """Register a new statement type ahead of its parser being written.

    Derives `parser_key` from `name` (slugified, de-duplicated) — that's the
    key you later set as `statement_type_key` on the real StatementTypeParser
    subclass to link the two up, at which point `has_parser` flips to true.
    """
    parser_key = _unique_parser_key(db, _slugify(name))
    statement_type = StatementType(name=name, parser_key=parser_key)
    db.add(statement_type)
    db.commit()
    db.refresh(statement_type)
    return statement_type
