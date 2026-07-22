from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.statement import Statement


class StatementType(Base):
    __tablename__ = "statement_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    parser_key: Mapped[str] = mapped_column(String(50), unique=True)

    statements: Mapped[list["Statement"]] = relationship(back_populates="statement_type")

    @property
    def has_parser(self) -> bool:
        """Whether a StatementTypeParser is registered under this parser_key.

        Lets a StatementType exist (created via the API) before its parser is
        written — the row and the code link up automatically once someone
        implements a parser with a matching `statement_type_key`.
        """
        from app.parsers.registry import get_parser

        return get_parser(self.parser_key) is not None
