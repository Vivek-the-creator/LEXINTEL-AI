"""
Document text extraction utilities.
Handles: native PDF text, scanned PDFs (OCR), and images.
PaddleOCR is imported lazily so the server starts even if it is not installed.
"""
import io
import os
import hashlib
from typing import Tuple, Optional

from app.ai.logging.logger import AILogger
from app.core.config import settings

logger = AILogger("doc_intel.extractor")


def _extract_pdf_native(path: str) -> Tuple[str, int]:
    """Extract selectable text from a PDF using pypdf. Returns (text, page_count)."""
    try:
        import pypdf
        reader = pypdf.PdfReader(path)
        pages = []
        for page in reader.pages[:settings.MAX_PDF_PAGES]:
            t = page.extract_text() or ""
            pages.append(t)
        return "\n".join(pages).strip(), len(reader.pages)
    except Exception as e:
        logger.warning("pypdf extraction failed", error=str(e))
        return "", 0


def _extract_with_ocr(path: str) -> str:
    """Run PaddleOCR on a file (PDF or image). Returns concatenated text."""
    try:
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(
            use_angle_cls=True,
            lang=settings.OCR_LANGUAGE,
            use_gpu=settings.OCR_USE_GPU,
            show_log=False,
        )
        result = ocr.ocr(path, cls=True)
        lines = []
        if result:
            for page_result in result:
                if page_result:
                    for line in page_result:
                        if line and len(line) >= 2 and line[1]:
                            lines.append(line[1][0])
        return "\n".join(lines).strip()
    except ImportError:
        logger.warning("PaddleOCR not installed — OCR skipped")
        return ""
    except Exception as e:
        logger.warning("OCR failed", error=str(e))
        return ""


def _extract_image_text(path: str) -> str:
    """Extract text from an image file via OCR."""
    return _extract_with_ocr(path)


def extract_text_from_file(path: str) -> Tuple[str, int, bool]:
    """
    Main entry point for text extraction.
    Returns (text, page_count, ocr_used).
    Strategy:
      1. Try native PDF extraction.
      2. If text is too short (likely scanned), fall back to OCR.
      3. For images, go straight to OCR.
    """
    ext = os.path.splitext(path)[1].lower()
    ocr_used = False

    if ext == ".pdf":
        text, pages = _extract_pdf_native(path)
        if len(text) < settings.MIN_TEXT_LENGTH_FOR_OCR and settings.OCR_ENABLED:
            logger.info("PDF text too short, running OCR", chars=len(text))
            ocr_text = _extract_with_ocr(path)
            if ocr_text:
                text = ocr_text
                ocr_used = True
        return text, pages, ocr_used

    if ext in {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}:
        text = _extract_image_text(path)
        return text, 1, True

    # Fallback: try reading as plain text
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read().strip(), 1, False
    except Exception:
        return "", 0, False


def file_hash(path: str) -> str:
    """SHA-256 hash of a file for duplicate detection."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
