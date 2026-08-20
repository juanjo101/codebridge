"""OCR Endpoint for processing visually complex documents."""

import tempfile
import pytesseract
from pathlib import Path
from PIL import Image
from pdf2image import convert_from_path
from markitdown import MarkItDown

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from codebridge.security.auth import validate_local_token

router = APIRouter(
    prefix="/ocr",
    tags=["OCR"],
    dependencies=[Depends(validate_local_token)]
)


def extract_text_from_pdf(file_path: str) -> str:
    """Extracts text from a PDF file by converting pages to images and using OCR."""
    try:
        images = convert_from_path(file_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process PDF: {e}")

    texto = ''
    for img in images:
        # Run Tesseract OCR in Spanish
        page_text = pytesseract.image_to_string(img, lang='spa')
        texto += page_text + '\n\n'

    return texto


@router.post("")
async def process_ocr(file: UploadFile = File(...)):
    """
    Receives a PDF file, extracts its pages as images, passes them through Tesseract-OCR,
    and returns the structured Markdown text.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported for OCR")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(await file.read())
        temp_file_path = temp_file.name

    try:
        # Extract text via OCR
        raw_text = extract_text_from_pdf(temp_file_path)
        
        # Structure as markdown (we can format it properly, for now we just wrap it)
        # Using markitdown conceptually if we had a raw text parser, but since Tesseract 
        # gives us plain text, we'll format it as a markdown block or simple markdown.
        markdown_text = f"## Document OCR Result: {file.filename}\n\n```text\n{raw_text}\n```"
        
        return {"filename": file.filename, "markdown": markdown_text, "raw_text": raw_text}
        
    finally:
        # Cleanup
        Path(temp_file_path).unlink(missing_ok=True)
