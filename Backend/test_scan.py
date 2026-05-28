"""
test_scan.py — End-to-end PHANTOM scan tester.

Steps:
  1. POST /api/scan/start  → get scan_id
  2. Connect to WS /ws/stream/{scan_id} → print live output
  3. GET /api/scan/status/{scan_id}      → print final status
  4. Read temp_results JSON              → pretty-print findings
"""

import asyncio
import json
import sys
from pathlib import Path

import httpx
import websockets


BASE = "http://localhost:8000"
WS_BASE = "ws://localhost:8000"
TARGET = "http://testphp.vulnweb.com"

DIVIDER = "─" * 70


def banner(text: str) -> None:
    print(f"\n{DIVIDER}")
    print(f"  {text}")
    print(DIVIDER)


async def main() -> None:
    # ------------------------------------------------------------------ #
    # STEP 1 — Start the scan
    # ------------------------------------------------------------------ #
    banner("STEP 1 — Starting scan via POST /api/scan/start")
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{BASE}/api/scan/start",
            json={"target_url": TARGET, "scan_mode": "quick"},
        )
        resp.raise_for_status()

    data = resp.json()
    scan_id = data["scan_id"]

    print(f"  scan_id : {scan_id}")
    print(f"  status  : {data['status']}")
    print(f"  message : {data['message']}")

    # ------------------------------------------------------------------ #
    # STEP 2 — Stream WebSocket output
    # ------------------------------------------------------------------ #
    banner(f"STEP 2 — Streaming live output  ws/stream/{scan_id}")
    ws_url = f"{WS_BASE}/ws/stream/{scan_id}"
    print(f"  Connecting to {ws_url} …\n")

    lines_received = 0
    try:
        async with websockets.connect(ws_url, ping_interval=None) as ws:
            while True:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=30)
                    print(f"  ▶  {msg}")
                    lines_received += 1
                    # Scanner sends a "completed" or "failed" line as last message
                    if "✅ Scan completed" in msg or "❌ Scan failed" in msg:
                        break
                except asyncio.TimeoutError:
                    print("  ⚠  No output for 30 s — assuming scan finished.")
                    break
    except Exception as exc:
        print(f"  ⚠  WebSocket error: {exc}")

    print(f"\n  Total lines received: {lines_received}")

    # ------------------------------------------------------------------ #
    # STEP 3 — Final status
    # ------------------------------------------------------------------ #
    banner(f"STEP 3 — GET /api/scan/status/{scan_id}")
    await asyncio.sleep(1)          # give background task a moment to flush
    async with httpx.AsyncClient(timeout=10) as client:
        status_resp = await client.get(f"{BASE}/api/scan/status/{scan_id}")
        status_resp.raise_for_status()

    status_data = status_resp.json()
    mode_label  = "🟡  MOCK MODE" if status_data.get("mock_mode") else "🟢  REAL MODE"
    print(f"  scan_id     : {status_data['scan_id']}")
    print(f"  status      : {status_data['status'].upper()}")
    print(f"  mode        : {mode_label}")
    print(f"  result_file : {status_data.get('result_file', 'N/A')}")

    # ------------------------------------------------------------------ #
    # STEP 4 — Read and pretty-print the JSON output
    # ------------------------------------------------------------------ #
    banner("STEP 4 — Scan findings from result file")

    result_path_str = status_data.get("result_file")
    if not result_path_str:
        # Fallback: search temp_results for any file matching the scan_id
        candidates = list(Path("./temp_results").glob(f"{scan_id}*.json"))
        if candidates:
            result_path_str = str(candidates[0])

    if not result_path_str:
        print("  ⚠  No result file found.")
        return

    result_path = Path(result_path_str)
    if not result_path.exists():
        # Try relative from script location
        result_path = Path(__file__).parent / result_path_str
    if not result_path.exists():
        print(f"  ⚠  File not found: {result_path_str}")
        return

    raw = json.loads(result_path.read_text(encoding="utf-8"))

    print(f"\n  Full path : {result_path.resolve()}\n")

    # --- Meta ---
    meta = raw.get("meta", {})
    print(f"  Generated : {meta.get('generated_at', 'N/A')}")
    print(f"  Target    : {meta.get('target', TARGET)}")
    print(f"  Mode      : {meta.get('mode', 'real')}")

    # --- Summary ---
    summary = raw.get("summary", {})
    if summary:
        print(f"\n  {'─'*30}  SUMMARY  {'─'*30}")
        print(f"  Total findings : {summary.get('total_findings', '?')}")
        by_sev = summary.get("by_severity", {})
        for sev, count in by_sev.items():
            bar = "█" * count if count else ""
            print(f"    {sev:<15} {count:>3}  {bar}")

    # --- Nuclei findings ---
    nuclei = raw.get("nuclei_findings", [])
    if nuclei:
        print(f"\n  {'─'*28}  NUCLEI FINDINGS ({len(nuclei)})  {'─'*28}")
        for i, f in enumerate(nuclei, 1):
            sev = f.get("severity", "?").upper()
            print(f"\n  [{i}] {f.get('name', '?')}  [{sev}]")
            print(f"       Template  : {f.get('template_id', '?')}")
            print(f"       URL       : {f.get('matched_url', '?')}")
            print(f"       Desc      : {f.get('description', '')[:120]}")
            if "remediation" in f:
                print(f"       Fix       : {f['remediation']}")

    # --- ZAP findings ---
    zap = raw.get("zap_findings", [])
    if zap:
        print(f"\n  {'─'*29}  ZAP FINDINGS ({len(zap)})  {'─'*29}")
        for i, f in enumerate(zap, 1):
            risk = f.get("risk", "?").upper()
            print(f"\n  [{i}] {f.get('alert', '?')}  [{risk}]")
            print(f"       URL       : {f.get('url', '?')}")
            print(f"       Desc      : {f.get('description', '')[:120]}")
            print(f"       Solution  : {f.get('solution', '')[:120]}")

    # --- Raw file dump (collapsed) ---
    banner("STEP 5 — Raw JSON (full file)")
    print(json.dumps(raw, indent=2))

    print(f"\n{DIVIDER}")
    print("  ✅  Test complete.")
    print(DIVIDER)


if __name__ == "__main__":
    asyncio.run(main())
