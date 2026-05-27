"""
main.py — PHANTOM Core API entry point.

How to start the server
-----------------------
From inside the /backend directory:

    pip install -r requirements.txt
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload

Then open:
    REST API docs → http://localhost:8000/docs
    Start a scan  → POST http://localhost:8000/api/scan/start
    Live stream   → ws://localhost:8000/ws/stream/{scan_id}
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict

from fastapi import (
    BackgroundTasks,
    FastAPI,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware

from models import ScanRequest, ScanResponse, ScanStatusResponse
from scanner import run_security_tools, scan_registry
from ws_manager import ConnectionManager

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger("phantom.main")

# ---------------------------------------------------------------------------
# App + middleware
# ---------------------------------------------------------------------------
app = FastAPI(
    title="PHANTOM — Core API & Tool Engine",
    description=(
        "Module 2 of the PHANTOM autonomous penetration-testing orchestrator. "
        "Accepts scan requests, runs Nuclei / OWASP ZAP asynchronously, and "
        "streams live terminal output to the React frontend via WebSockets."
    ),
    version="1.0.0",
)

# Allow the React frontend (or any origin during development) to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Single shared WebSocket manager (created once per process)
ws_manager = ConnectionManager()

# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------


@app.post(
    "/api/scan/start",
    response_model=ScanResponse,
    summary="Start a new security scan",
    tags=["Scans"],
)
async def start_scan(
    body: ScanRequest,
    background_tasks: BackgroundTasks,
) -> ScanResponse:
    """
    Accepts a `ScanRequest` (target_url + scan_mode), generates a unique
    `scan_id`, fires the scanning task in the background, and immediately
    returns a `ScanResponse` so the caller doesn't block.

    Connect to **ws://host/ws/stream/{scan_id}** to receive live output.
    """
    scan_id = str(uuid.uuid4())
    target_url = str(body.target_url)

    logger.info("New scan request | id=%s | target=%s | mode=%s", scan_id, target_url, body.scan_mode)

    # Fire-and-forget: the HTTP response is returned immediately while the
    # scanner runs in the background event loop.
    background_tasks.add_task(
        run_security_tools,
        scan_id=scan_id,
        target_url=target_url,
        scan_mode=body.scan_mode.value,
        ws_manager=ws_manager,
    )

    return ScanResponse(
        scan_id=scan_id,  # type: ignore[arg-type]
        status="queued",
        message=(
            f"Scan queued for {target_url} in {body.scan_mode.value} mode. "
            f"Connect to ws://localhost:8000/ws/stream/{scan_id} for live output."
        ),
    )


@app.get(
    "/api/scan/status/{scan_id}",
    response_model=ScanStatusResponse,
    summary="Get scan status",
    tags=["Scans"],
)
async def get_scan_status(scan_id: str) -> ScanStatusResponse:
    """
    Returns the current lifecycle status of a scan:
    `queued` → `running` → `completed` | `failed`.
    """
    entry: Dict[str, Any] | None = scan_registry.get(scan_id)

    if entry is None:
        raise HTTPException(status_code=404, detail=f"Scan '{scan_id}' not found.")

    return ScanStatusResponse(
        scan_id=scan_id,  # type: ignore[arg-type]
        status=entry["status"],
        mock_mode=entry.get("mock_mode", False),
        result_file=entry.get("result_file"),
    )


@app.get("/api/health", tags=["Meta"], summary="Health check")
async def health() -> dict:
    """Simple liveness probe — returns 200 OK with a timestamp."""
    from datetime import datetime, timezone
    return {"status": "ok", "service": "phantom-core-api", "timestamp": datetime.now(timezone.utc).isoformat()}


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------


@app.websocket("/ws/stream/{scan_id}")
async def websocket_stream(websocket: WebSocket, scan_id: str) -> None:
    """
    Live terminal output stream for *scan_id*.

    The React frontend connects here immediately after calling
    POST /api/scan/start and receives text frames line-by-line as the
    underlying CLI tools produce output.
    """
    await ws_manager.connect(scan_id, websocket)
    logger.info("WebSocket opened | scan_id=%s", scan_id)

    try:
        # Keep the connection alive; the scanner pushes data to the client.
        # We still need to listen for incoming frames so that the server
        # detects a disconnect (the client closing the tab, etc.).
        while True:
            data = await websocket.receive_text()
            # Clients can optionally send pings; log and ignore them.
            logger.debug("WS recv | scan_id=%s | data=%s", scan_id, data)
    except WebSocketDisconnect:
        logger.info("WebSocket closed | scan_id=%s", scan_id)
    finally:
        await ws_manager.disconnect(scan_id, websocket)
