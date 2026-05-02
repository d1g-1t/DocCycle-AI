"""Extract text from uploaded files (PDF, DOCX, HTML, TXT)."""
from __future__ import annotations

import io
from pathlib import Path

import structlog

log = structlog.get_logger(__name__)


class FileExtractor:
    """Extract plain text from various document formats."""

    SUPPORTED_TYPES = {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/html", "text/plain"}

    @staticmethod
    async def extract(data: bytes, content_type: str, filename: str = "") -> str:
        """Extract text from file bytes based on content type."""
        import asyncio

        ext = Path(filename).suffix.lower() if filename else ""

        if content_type == "application/pdf" or ext == ".pdf":
            return await asyncio.to_thread(FileExtractor._extract_pdf, data)
        elif content_type.endswith("wordprocessingml.document") or ext == ".docx":
            return await asyncio.to_thread(FileExtractor._extract_docx, data)
        elif "html" in content_type or ext in (".html", ".htm"):
            return data.decode("utf-8", errors="replace")
        else:
            return data.decode("utf-8", errors="replace")

    @staticmethod
    def _extract_pdf(data: bytes) -> str:
        """Extract text from PDF using pdfplumber."""
        try:
            import pdfplumber

            text_parts: list[str] = []
            with pdfplumber.open(io.BytesIO(data)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            return "\n\n".join(text_parts)
        except ImportError:
            log.warning("file_extractor.pdfplumber_not_installed")
            return "[PDF extraction requires pdfplumber]"
        except Exception as exc:
            log.error("file_extractor.pdf_error", error=str(exc))
            return ""

    @staticmethod
    def _extract_docx(data: bytes) -> str:
        """Extract text from DOCX using python-docx."""
        try:
            from docx import Document

            doc = Document(io.BytesIO(data))
            return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except ImportError:
            log.warning("file_extractor.python_docx_not_installed")
            return "[DOCX extraction requires python-docx]"
        except Exception as exc:
            log.error("file_extractor.docx_error", error=str(exc))
            return ""
