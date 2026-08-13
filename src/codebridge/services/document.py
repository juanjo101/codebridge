"""
Document service - PDF, Office, and HTML document conversion via MarkItDown.
"""

import logging
from pathlib import Path
from typing import Any
import tempfile
import os

logger = logging.getLogger(__name__)


class DocumentService:
    """Service to convert documents (PDF, DOCX, XLSX, PPTX, HTML, etc.) into Markdown."""

    def __init__(self) -> None:
        self._converter: Any = None

    def _get_converter(self) -> Any:
        if self._converter is None:
            try:
                from markitdown import MarkItDown
                self._converter = MarkItDown()
            except ImportError as err:
                raise RuntimeError(
                    "markitdown package is not installed. Install it with `pip install markitdown`."
                ) from err
        return self._converter

    def convert_file(self, file_path: str | Path) -> str:
        """Convert a local document file to Markdown text."""
        path = Path(file_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        converter = self._get_converter()
        logger.info(f"Converting document to Markdown: {path.name}")
        result = converter.convert(str(path))
        return result.text_content

    def convert_bytes(self, content: bytes, filename: str) -> str:
        """Convert binary bytes content with a given filename/extension to Markdown."""
        suffix = Path(filename).suffix if filename else ".tmp"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            return self.convert_file(tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


_document_service: DocumentService | None = None


def get_document_service() -> DocumentService:
    """Singleton getter for DocumentService."""
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service
