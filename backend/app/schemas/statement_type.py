from pydantic import BaseModel, ConfigDict, Field


class StatementTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    parser_key: str
    has_parser: bool


class StatementTypeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class StatementTypeUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
