"""
PDF Parser Utility
Extracts clean text from PDF files using PyMuPDF (fitz) with pdfplumber fallback.
"""

import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any

logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_path: str) -> Tuple[str, List[Dict]]:
    """
    Extract text from a PDF file.
    Returns:
        full_text (str): Combined text from all pages
        pages_text (List[Dict]): Per-page text with metadata
    """
    pages_text: List[Dict] = []
    full_text = ""

    # ── Try PyMuPDF first (fastest) ───────────────────────────────────────
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            if text.strip():
                pages_text.append({
                    "page": page_num + 1,
                    "text": text,
                    "char_count": len(text),
                })
                full_text += f"\n\n[PAGE {page_num + 1}]\n{text}"
        doc.close()

        if full_text.strip():
            logger.info(f"PyMuPDF extracted {len(full_text)} chars from {len(pages_text)} pages")
            return full_text.strip(), pages_text

    except ImportError:
        logger.warning("PyMuPDF not available, trying pdfplumber...")
    except Exception as e:
        logger.warning(f"PyMuPDF failed: {e}, trying pdfplumber...")

    # ── Fallback: pdfplumber ──────────────────────────────────────────────
    try:
        import pdfplumber

        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                if text.strip():
                    pages_text.append({
                        "page": page_num + 1,
                        "text": text,
                        "char_count": len(text),
                    })
                    full_text += f"\n\n[PAGE {page_num + 1}]\n{text}"

        if full_text.strip():
            logger.info(f"pdfplumber extracted {len(full_text)} chars")
            return full_text.strip(), pages_text

    except ImportError:
        logger.warning("pdfplumber not available")
    except Exception as e:
        logger.error(f"pdfplumber failed: {e}")

    # ── Last resort: PyPDF2 ───────────────────────────────────────────────
    try:
        import PyPDF2

        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                if text.strip():
                    pages_text.append({
                        "page": page_num + 1,
                        "text": text,
                        "char_count": len(text),
                    })
                    full_text += f"\n\n[PAGE {page_num + 1}]\n{text}"

    except Exception as e:
        logger.error(f"All PDF parsers failed: {e}")

    return full_text.strip(), pages_text


def get_pdf_metadata(pdf_path: str) -> Dict[str, Any]:
    """Extract metadata from a PDF file."""
    meta: Dict[str, Any] = {}

    try:
        import fitz
        doc = fitz.open(pdf_path)
        raw_meta = doc.metadata
        meta = {
            "title": raw_meta.get("title", ""),
            "author": raw_meta.get("author", ""),
            "subject": raw_meta.get("subject", ""),
            "creator": raw_meta.get("creator", ""),
            "pages": len(doc),
            "format": doc.metadata.get("format", "PDF"),
        }
        doc.close()
    except Exception:
        try:
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                meta["pages"] = len(pdf.pages)
        except Exception:
            meta["pages"] = 0

    return meta


def clean_extracted_text(text: str) -> str:
    """Clean and normalise extracted PDF text."""
    import re

    # Remove excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    # Remove non-printable characters (keep standard unicode)
    text = "".join(c for c in text if c.isprintable() or c in "\n\t")
    return text.strip()
