"""
run_and_test.py — Self-contained PHANTOM launcher + end-to-end tester.

  1. Spawns the uvicorn server as a subprocess
  2. Waits until it responds to HTTP
  3. Runs the full scan test against http://testphp.vulnweb.com
  4. Kills the server when done
"""

import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path

import httpx
import websockets

BASE    = "http://localhost:8000"
WS_BASE = "ws://localhost:8000"
TARGET  = "http://testphp.vulnweb.com"
SEP     = "=" * 72


# ── helpers ────────────────────────────────────────────────────────────────

def log(msg: str) -> None:
    print(msg, flush=True)

def section(title: str) -> None:
    log(f"\n{SEP}\n  {title}\n{SEP}")


async def wait_for_server(url: str, timeout: float = 20.0) -> bool:
    deadline = time.monotonic() + timeout
    async with httpx.AsyncClient() as client:
        while time.monotonic() < deadline:
            try:
                r = await client.get(url, timeout=2)
                if r.status_code < 500:
                    return True
            except Exception:
                pass
            await asyncio.sleep(0.5)
    return False


# ── main ───────────────────────────────────────────────────────────────────

async def main() -> None:
    # ------------------------------------------------------------------ #
    # Start server
    # ------------------------------------------------------------------ #
    section("Starting PHANTOM uvicorn server on :8000")
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app",
         "--host", "0.0.0.0", "--port", "8000", "--log-level", "warning"],
        cwd=str(Path(__file__).parent),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    log(f"  Server PID: {server.pid}")

    ready = await wait_for_server(f"{BASE}/api/health")
    if not ready:
        log("  ERROR: server didn't start within 20 s — aborting.")
        server.terminate()
        return
    log("  Server is ready!")

    try:
        await run_test()
    finally:
        log("\n  Shutting down server…")
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
        log("  Done.")


async def run_test() -> None:
    # ------------------------------------------------------------------ #
    # STEP 1 — Start scan
    # ------------------------------------------------------------------ #
    section("STEP 1 — POST /api/scan/start")
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{BASE}/api/scan/start",
            json={"target_url": TARGET, "scan_mode": "quick"},
        )
        resp.raise_for_status()

    data    = resp.json()
    scan_id = data["scan_id"]

    log(f"  scan_id : {scan_id}")
    log(f"  status  : {data['status']}")
    log(f"  message : {data['message']}")

    # ------------------------------------------------------------------ #
    # STEP 2 — WebSocket live stream
    # ------------------------------------------------------------------ #
    section(f"STEP 2 — Streaming  ws://localhost:8000/ws/stream/{scan_id}")
    ws_url = f"{WS_BASE}/ws/stream/{scan_id}"
    log(f"  Connecting to {ws_url} ...\n")

    lines = 0
    try:
        async with websockets.connect(ws_url, ping_interval=None) as ws:
            while True:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=45)
                    log(f"  >> {msg}")
                    lines += 1
                    if "[PHANTOM]" in msg and ("completed" in msg or "failed" in msg):
                        break
                except asyncio.TimeoutError:
                    log("  (no output for 45 s — assuming finished)")
                    break
    except Exception as exc:
        log(f"  WebSocket error: {exc}")

    log(f"\n  Total lines streamed: {lines}")

    # ------------------------------------------------------------------ #
    # STEP 3 — Final status
    # ------------------------------------------------------------------ #
    section(f"STEP 3 — GET /api/scan/status/{scan_id}")
    await asyncio.sleep(1)
    async with httpx.AsyncClient(timeout=10) as client:
        sr = await client.get(f"{BASE}/api/scan/status/{scan_id}")
        sr.raise_for_status()

    st = sr.json()
    mode = "MOCK MODE" if st.get("mock_mode") else "REAL MODE"
    log(f"  Status      : {st['status'].upper()}")
    log(f"  Mode        : {mode}")
    log(f"  Result file : {st.get('result_file', 'N/A')}")

    # ------------------------------------------------------------------ #
    # STEP 4 — Read & display JSON findings
    # ------------------------------------------------------------------ #
    section("STEP 4 — Findings from result JSON")

    result_str = st.get("result_file")
    if not result_str:
        candidates = list(Path("./temp_results").glob(f"{scan_id}*.json"))
        result_str = str(candidates[0]) if candidates else None

    if not result_str:
        log("  No result file found.")
        return

    rp = Path(result_str)
    if not rp.exists():
        rp = Path(__file__).parent / result_str
    if not rp.exists():
        log(f"  File not found: {result_str}")
        return

    raw = json.loads(rp.read_text(encoding="utf-8"))
    log(f"\n  Full path : {rp.resolve()}\n")

    meta = raw.get("meta", {})
    log(f"  Generated : {meta.get('generated_at', 'N/A')}")
    log(f"  Target    : {meta.get('target', TARGET)}")
    log(f"  Mode      : {meta.get('mode', 'real')}")

    summary = raw.get("summary", {})
    if summary:
        log(f"\n  --- SUMMARY ---")
        log(f"  Total findings : {summary.get('total_findings', '?')}")
        for sev, cnt in summary.get("by_severity", {}).items():
            log(f"    {sev:<15} {cnt:>3}")

    nuclei = raw.get("nuclei_findings", [])
    if nuclei:
        log(f"\n  --- NUCLEI FINDINGS ({len(nuclei)}) ---")
        for i, f in enumerate(nuclei, 1):
            log(f"\n  [{i}] {f.get('name')}  [SEVERITY: {f.get('severity','?').upper()}]")
            log(f"       Template  : {f.get('template_id')}")
            log(f"       URL       : {f.get('matched_url')}")
            log(f"       Desc      : {str(f.get('description',''))[:110]}")
            log(f"       Fix       : {f.get('remediation','')}")

    zap = raw.get("zap_findings", [])
    if zap:
        log(f"\n  --- ZAP FINDINGS ({len(zap)}) ---")
        for i, f in enumerate(zap, 1):
            log(f"\n  [{i}] {f.get('alert')}  [RISK: {f.get('risk','?').upper()}]")
            log(f"       URL      : {f.get('url')}")
            log(f"       Desc     : {str(f.get('description',''))[:110]}")
            log(f"       Fix      : {str(f.get('solution',''))[:110]}")

    section("STEP 5 — Full raw JSON")
    log(json.dumps(raw, indent=2))

    log(f"\n{SEP}")
    log("  SCAN COMPLETE")
    log(f"  Mode        : {mode}")
    log(f"  Findings    : {summary.get('total_findings', '?')} total")
    log(f"  Result file : {rp.resolve()}")
    log(SEP)


if __name__ == "__main__":
    asyncio.run(main())
