import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings


def save_upload(statement_id: uuid.UUID, upload: UploadFile) -> str:
    statement_dir = settings.uploads_dir / str(statement_id)
    statement_dir.mkdir(parents=True, exist_ok=True)

    filename = upload.filename or "statement.pdf"
    destination = statement_dir / filename
    with destination.open("wb") as out:
        out.write(upload.file.read())

    return str(destination)


def output_path(statement_id: uuid.UUID, filename: str) -> str:
    statement_dir = settings.outputs_dir / str(statement_id)
    statement_dir.mkdir(parents=True, exist_ok=True)
    return str(statement_dir / filename)


def delete_statement_files(pdf_path: str | None, xlsx_path: str | None) -> None:
    for path_str in (pdf_path, xlsx_path):
        if not path_str:
            continue
        path = Path(path_str)
        if path.exists():
            path.unlink()
        parent = path.parent
        if parent.exists() and not any(parent.iterdir()):
            parent.rmdir()
