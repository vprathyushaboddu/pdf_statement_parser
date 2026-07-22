#: Text expected to appear in this bank's statement header/footer.
#: Replace with real signatures (bank name, IFSC prefix, statement title
#: wording, etc.) once a real sample statement is available.
SIGNATURE_PHRASES = ["Example Bank", "Example Bank Ltd"]


def confidence(pdf_text: str) -> float:
    hits = sum(1 for phrase in SIGNATURE_PHRASES if phrase.lower() in pdf_text.lower())
    if hits == 0:
        return 0.0
    return min(1.0, hits / len(SIGNATURE_PHRASES))
