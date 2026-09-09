"""Text out of an uploaded job description, with OCR as the fallback."""

import io

from pypdf import PdfReader
import pypdfium2
import pytesseract
from app.config import config, log

MIN_TEXT = 50
MIN_PER_PAGE = 100



def ocr(raw):

    if config.tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = config.tesseract_cmd

    pages = []
    for page in pypdfium2.PdfDocument(raw):
        image = page.render(scale=3).to_pil()
        pages.append(pytesseract.image_to_string(image))

    return "\n".join(pages)


def extract_text(raw, filename):
    if not (filename or "").lower().endswith(".pdf"):
        return raw.decode("utf-8", errors="ignore").strip()

    reader = PdfReader(io.BytesIO(raw))
    text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()

    if len(text) >= MIN_PER_PAGE * len(reader.pages):
        return text

    log("pdf", str(len(text)) + " chars over " + str(len(reader.pages))
        + " pages - trying OCR")

    try:
        scanned = ocr(raw).strip()
    except Exception as error:
        log("pdf", "OCR failed: " + type(error).__name__ + " - " + str(error))
        return ""

    return scanned if len(scanned) > len(text) else text
