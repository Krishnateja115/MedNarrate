"""Real, minimal documents for upload tests.

Uploads are structurally validated (page-count / pixel budgets), so fixtures
must be genuine files rather than magic-byte stubs.
"""

import fitz  # PyMuPDF


def _build_pdf() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Synthetic test report")
    data = doc.tobytes()
    doc.close()
    return data


VALID_PDF = _build_pdf()
