"""
ws_manager.py — WebSocket connection manager for PHANTOM.

Each scan session (identified by scan_id) can have multiple WebSocket
clients listening. The ConnectionManager stores them in a dict keyed by
scan_id, broadcasts messages, and handles graceful disconnection.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Dict, List

from fastapi import WebSocket

logger = logging.getLogger("phantom.ws_manager")


class ConnectionManager:
    """
    Manages all active WebSocket connections, grouped by scan_id.

    Usage
    -----
    Instantiate once at application level and inject into route handlers
    and the scanner module.
    """

    def __init__(self) -> None:
        # scan_id -> list of connected WebSocket clients
        self._active: Dict[str, List[WebSocket]] = defaultdict(list)
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    async def connect(self, scan_id: str, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket client for *scan_id*."""
        await websocket.accept()
        async with self._lock:
            self._active[scan_id].append(websocket)
        logger.info("WS connected  | scan_id=%s | total=%d", scan_id, len(self._active[scan_id]))

    async def disconnect(self, scan_id: str, websocket: WebSocket) -> None:
        """Remove *websocket* from the active pool for *scan_id*."""
        async with self._lock:
            try:
                self._active[scan_id].remove(websocket)
            except ValueError:
                pass  # already removed
        logger.info("WS disconnected | scan_id=%s | remaining=%d", scan_id, len(self._active[scan_id]))

    # ------------------------------------------------------------------
    # Messaging
    # ------------------------------------------------------------------

    async def broadcast(self, scan_id: str, message: str) -> None:
        """
        Send *message* to every client listening on *scan_id*.

        Clients that have closed their connection mid-stream are silently
        removed so they don't block subsequent broadcasts.
        """
        dead: List[WebSocket] = []

        async with self._lock:
            clients = list(self._active[scan_id])  # shallow copy for safe iteration

        for ws in clients:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)

        if dead:
            async with self._lock:
                for ws in dead:
                    try:
                        self._active[scan_id].remove(ws)
                    except ValueError:
                        pass

    async def send_json(self, scan_id: str, payload: dict) -> None:
        """Convenience wrapper — sends a JSON-serialisable *payload* dict."""
        import json
        await self.broadcast(scan_id, json.dumps(payload))

    def has_listeners(self, scan_id: str) -> bool:
        """Return True if at least one client is connected for *scan_id*."""
        return bool(self._active.get(scan_id))

    def active_scans(self) -> List[str]:
        """Return the list of scan_ids that currently have active listeners."""
        return [sid for sid, clients in self._active.items() if clients]
