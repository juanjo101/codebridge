"""POST /v1/documents/convert endpoint for converting PDF/Office files to Markdown."""

from __future__ import annotations

import logging
from typing import Any, Optional
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse

from codebridge.security.auth import validate_local_token
from codebridge.services.document import get_document_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/v1/documents/convert", dependencies=[Depends(validate_local_token)])
async def convert_document(
    request: Request,
    file: Optional[UploadFile] = File(None),
) -> Any:
    """
    POST /v1/documents/convert — Convert a document (PDF, Office, HTML) to Markdown.
    Supports either file upload via multipart/form-data or a JSON body with file_path.
    """
    service = get_document_service()

    try:
        content_type = request.headers.get("content-type", "")

        if file is not None and file.filename:
            content = await file.read()
            text_content = service.convert_bytes(content, file.filename)
            return JSONResponse(
                content={
                    "status": "success",
                    "filename": file.filename,
                    "markdown": text_content,
                }
            )

        if "application/json" in content_type:
            body = await request.json()
            file_path = body.get("file_path") if isinstance(body, dict) else None
            if file_path:
                text_content = service.convert_file(file_path)
                return JSONResponse(
                    content={
                        "status": "success",
                        "file_path": str(Path(file_path).resolve()),
                        "markdown": text_content,
                    }
                )

        raise HTTPException(
            status_code=400,
            detail="Must provide either a file upload or a file_path in JSON body.",
        )
    except HTTPException:
        raise
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Error converting document: %s", exc)
        raise HTTPException(
            status_code=500, detail=f"Failed to convert document: {exc}"
        ) from exc
