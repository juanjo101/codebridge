"""GET /usage endpoint."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from codebridge.telemetry.storage import get_telemetry

router = APIRouter()


@router.get("/usage")
async def usage() -> JSONResponse:
    """GET /usage — local telemetry snapshot."""
    telemetry = get_telemetry()
    data = telemetry.snapshot()
    return JSONResponse(content=data)
