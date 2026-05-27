"""
models.py — Pydantic schemas for PHANTOM scan requests and responses.
"""

from enum import Enum
from uuid import UUID

from pydantic import BaseModel, HttpUrl


class ScanMode(str, Enum):
    quick = "quick"
    deep = "deep"


class ScanRequest(BaseModel):
    """
    Payload expected by POST /api/scan/start.

    Fields
    ------
    target_url : HttpUrl
        The full URL of the target (e.g. https://example.com).
    scan_mode : ScanMode
        Either "quick" (lightweight) or "deep" (full suite).
    """
    target_url: HttpUrl
    scan_mode: ScanMode = ScanMode.quick


class ScanResponse(BaseModel):
    """
    Immediate response returned by POST /api/scan/start.

    Fields
    ------
    scan_id : UUID
        Unique identifier for this scan session.
    status  : str
        Initial status — always "queued" right after creation.
    message : str
        Human-readable description of what was started.
    """
    scan_id: UUID
    status: str
    message: str


class ScanStatusResponse(BaseModel):
    """
    Payload returned by GET /api/scan/status/{scan_id}.
    """
    scan_id: UUID
    status: str          # "queued" | "running" | "completed" | "failed"
    mock_mode: bool      # True when real tools were unavailable
    result_file: str | None = None  # path to saved JSON, once available
