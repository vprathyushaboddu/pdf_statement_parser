from dataclasses import dataclass

import pdfplumber

#: Below this many characters of extracted text, treat the PDF as having no
#: usable text layer (i.e. a scanned image) rather than trying to parse it.
MIN_TEXT_LENGTH_FOR_DIGITAL_PDF = 20


@dataclass
class PageContent:
    text: str
    tables: list[list[list[str | None]]]


def load_pages(pdf_path: str) -> list[PageContent]:
    pages: list[PageContent] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            pages.append(
                PageContent(
                    text=page.extract_text() or "",
                    tables=[t for t in (page.extract_tables() or []) if t],
                )
            )
    return pages


def full_text(pages: list[PageContent]) -> str:
    return "\n".join(p.text for p in pages)


def has_extractable_text(pdf_path: str) -> bool:
    """Cheap check used to reject scanned/image-only PDFs (FR-3)."""
    pages = load_pages(pdf_path)
    return len(full_text(pages).strip()) >= MIN_TEXT_LENGTH_FOR_DIGITAL_PDF
