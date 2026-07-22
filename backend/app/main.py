from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import statement_types, statements, transactions
from app.db.session import SessionLocal
from app.services.statement_type_sync_service import sync_statement_types


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    try:
        sync_statement_types(db)
    finally:
        db.close()
    yield


app = FastAPI(title="Bank Statement Parser", lifespan=lifespan)

app.include_router(statements.router)
app.include_router(transactions.router)
app.include_router(statement_types.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
