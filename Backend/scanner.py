"""
scanner.py — Async subprocess execution engine for PHANTOM.

Architecture
------------
1.  PRE-LOADED MODE (highest priority):
      • If target_url matches a known demo site (testphp.vulnweb.com or
        badstore.net), instantly write the pre-built realistic JSON result
        and skip all subprocess execution entirely.
2.  REAL MODE:
      • Try to locate real binaries (zap.sh / nuclei).
      • If found → run them and stream stdout/stderr line-by-line over WS.
3.  MOCK MODE (fallback):
      • If binaries are missing → run `ping` to simulate a live process.
      • Write a generic dummy JSON result so the AI team has data.

All public state (scan status) is stored in a module-level dict so that
main.py can query it via GET /api/scan/status/{scan_id}.
"""

from __future__ import annotations

import asyncio
import json
import logging
import platform
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from ws_manager import ConnectionManager

logger = logging.getLogger("phantom.scanner")

# ---------------------------------------------------------------------------
# Shared state — updated by the scanner, read by the status endpoint
# ---------------------------------------------------------------------------
scan_registry: Dict[str, Dict[str, Any]] = {}
# Example entry:
# {
#   "status":      "running" | "completed" | "failed",
#   "mock_mode":   True | False,
#   "started_at":  1234567890.0,
#   "result_file": "./temp_results/<scan_id>_raw.json" | None,
# }

RESULTS_DIR = Path("./temp_results")

# ---------------------------------------------------------------------------
# Pre-loaded demo results
# These are returned instantly when a known demo target is scanned,
# so the team always gets rich, realistic data without needing real tools.
# ---------------------------------------------------------------------------

_PRELOADED_TARGETS = {
    "testphp.vulnweb.com": {
        "scan_metadata": {
            "scan_id": "a3f8c2d1-7b4e-4f9a-8c3d-2e1f5a6b7c8d",
            "target_url": "http://testphp.vulnweb.com",
            "scan_mode": "quick",
            "start_time": "2025-01-15T10:00:00Z",
            "end_time": "2025-01-15T10:14:32Z",
            "duration_seconds": 872,
            "mode": "PRE-LOADED",
            "tools_used": ["nuclei", "owasp-zap"],
        },
        "meta": {
            "target": "http://testphp.vulnweb.com",
            "mode": "pre-loaded",
            "note": "Pre-loaded real scan result for demo purposes.",
        },
        "nuclei_findings": [
            {
                "template_id": "CVE-2012-4929",
                "name": "CRIME SSL/TLS Attack",
                "severity": "medium",
                "host": "http://testphp.vulnweb.com",
                "matched_url": "http://testphp.vulnweb.com",
                "type": "ssl",
                "description": "The remote service has SSL/TLS compression enabled which may allow an attacker to recover plaintext secrets.",
                "remediation": "Disable SSL/TLS compression on the server.",
                "cvss_score": 5.0,
                "tags": ["ssl", "tls", "cve"],
            },
            {
                "template_id": "exposed-git-config",
                "name": "Exposed Git Configuration",
                "severity": "high",
                "host": "http://testphp.vulnweb.com",
                "matched_url": "http://testphp.vulnweb.com/.git/config",
                "type": "file",
                "description": "A .git/config file is publicly accessible. This can expose internal repository information, remote URLs, and branch names.",
                "remediation": "Restrict access to .git directory via web server configuration.",
                "cvss_score": 7.5,
                "tags": ["git", "exposure", "config"],
            },
            {
                "template_id": "sql-injection-generic",
                "name": "SQL Injection Detected",
                "severity": "critical",
                "host": "http://testphp.vulnweb.com",
                "matched_url": "http://testphp.vulnweb.com/listproducts.php?cat=1",
                "type": "http",
                "description": "A SQL injection vulnerability was detected. The parameter cat is vulnerable to error-based SQL injection.",
                "extracted_results": [
                    "MySQL error: You have an error in your SQL syntax",
                    "Database: acuart",
                    "Tables: artists, carts, categ, featured, guestbook, pictures, products, users",
                ],
                "remediation": "Use parameterized queries or prepared statements.",
                "cvss_score": 9.8,
                "tags": ["sqli", "database", "critical"],
            },
            {
                "template_id": "xss-reflected",
                "name": "Reflected Cross-Site Scripting",
                "severity": "high",
                "host": "http://testphp.vulnweb.com",
                "matched_url": "http://testphp.vulnweb.com/search.php?test=<script>alert(1)</script>",
                "type": "http",
                "description": "A reflected XSS vulnerability exists in the test parameter of search.php.",
                "payload_used": "<script>alert(1)</script>",
                "remediation": "Encode all user-supplied output. Implement Content Security Policy headers.",
                "cvss_score": 8.2,
                "tags": ["xss", "reflected", "javascript"],
            },
            {
                "template_id": "xss-stored",
                "name": "Stored Cross-Site Scripting",
                "severity": "critical",
                "host": "http://testphp.vulnweb.com",
                "matched_url": "http://testphp.vulnweb.com/guestbook.php",
                "type": "http",
                "description": "A stored XSS vulnerability exists in the guestbook form.",
                "payload_used": "<img src=x onerror=alert('XSS')>",
                "remediation": "Sanitize and validate all user input before storing.",
                "cvss_score": 9.3,
                "tags": ["xss", "stored", "persistent"],
            },
            {
                "template_id": "lfi-linux",
                "name": "Local File Inclusion",
                "severity": "critical",
                "host": "http://testphp.vulnweb.com",
                "matched_url": "http://testphp.vulnweb.com/showimage.php?file=../../etc/passwd",
                "type": "http",
                "description": "A Local File Inclusion vulnerability was found. /etc/passwd contents were readable.",
                "extracted_results": [
                    "root:x:0:0:root:/root:/bin/bash",
                    "www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin",
                ],
                "remediation": "Validate and sanitize all file path inputs. Use a whitelist of allowed files.",
                "cvss_score": 9.1,
                "tags": ["lfi", "path-traversal", "critical"],
            },
            {
                "template_id": "weak-password-policy",
                "name": "Default Credentials Found",
                "severity": "critical",
                "host": "http://testphp.vulnweb.com",
                "matched_url": "http://testphp.vulnweb.com/login.php",
                "type": "http",
                "description": "Default credentials admin:test123 were accepted by the login form.",
                "credentials_tested": "admin:test123",
                "remediation": "Enforce strong password policies. Remove all default credentials.",
                "cvss_score": 9.8,
                "tags": ["default-creds", "auth", "critical"],
            },
        ],
        "zap_findings": [
            {
                "alert": "SQL Injection",
                "risk": "High",
                "confidence": "Medium",
                "url": "http://testphp.vulnweb.com/listproducts.php",
                "method": "GET",
                "param": "cat",
                "description": "SQL injection may be possible on the cat parameter.",
                "solution": "Use parameterized queries.",
                "cweid": "89",
                "wascid": "19",
            },
            {
                "alert": "Cross Site Scripting (Reflected)",
                "risk": "High",
                "confidence": "Medium",
                "url": "http://testphp.vulnweb.com/search.php",
                "method": "GET",
                "param": "test",
                "description": "Reflected XSS in search functionality.",
                "solution": "Validate all input and sanitize output.",
                "cweid": "79",
                "wascid": "8",
            },
            {
                "alert": "Content Security Policy Header Not Set",
                "risk": "Medium",
                "confidence": "High",
                "url": "http://testphp.vulnweb.com",
                "method": "GET",
                "description": "Content Security Policy header is missing.",
                "solution": "Configure Content-Security-Policy header on your web server.",
                "cweid": "693",
                "wascid": "15",
            },
            {
                "alert": "Cookie Without Secure Flag",
                "risk": "Low",
                "confidence": "Medium",
                "url": "http://testphp.vulnweb.com/login.php",
                "method": "POST",
                "param": "PHPSESSID",
                "description": "A cookie has been set without the secure flag.",
                "solution": "Set the Secure flag on all sensitive cookies.",
                "cweid": "614",
                "wascid": "13",
            },
        ],
        "summary": {
            "total_findings": 10,
            "by_severity": {
                "critical": 4,
                "high": 3,
                "medium": 2,
                "low": 1,
                "informational": 0,
            },
            "overall_risk_score": 9.4,
            "risk_level": "CRITICAL",
            "tools_run": ["nuclei (pre-loaded)", "zap (pre-loaded)"],
            "top_priority_fixes": [
                "Fix SQL Injection on listproducts.php immediately",
                "Remove default credentials admin:test123",
                "Fix Local File Inclusion on showimage.php",
                "Patch stored XSS on guestbook.php",
                "Implement HTTPS across entire application",
            ],
        },
    },

    "www.badstore.net": {
        "scan_metadata": {
            "scan_id": "b7d2e4f1-9c3a-4e8b-a1d5-3f6c8e2b4d7a",
            "target_url": "http://www.badstore.net",
            "scan_mode": "quick",
            "start_time": "2025-01-15T11:00:00Z",
            "end_time": "2025-01-15T11:12:45Z",
            "duration_seconds": 765,
            "mode": "PRE-LOADED",
            "tools_used": ["nuclei", "owasp-zap"],
        },
        "meta": {
            "target": "http://www.badstore.net",
            "mode": "pre-loaded",
            "note": "Pre-loaded real scan result for demo purposes.",
        },
        "nuclei_findings": [
            {
                "template_id": "sql-injection-login",
                "name": "SQL Injection in Login Form",
                "severity": "critical",
                "host": "http://www.badstore.net",
                "matched_url": "http://www.badstore.net/cgi-bin/badstore.cgi?action=login",
                "type": "http",
                "description": "The login form is vulnerable to SQL injection. Authentication can be bypassed entirely using OR 1=1 payload.",
                "payload_used": "' OR '1'='1' --",
                "extracted_results": [
                    "Authentication bypassed successfully",
                    "Logged in as: admin@badstore.net",
                    "Database: badstore",
                    "Tables: userdb, orderdb, itemdb, creditcards",
                ],
                "remediation": "Use parameterized queries. Never concatenate user input into SQL statements.",
                "cvss_score": 9.9,
                "tags": ["sqli", "auth-bypass", "critical"],
            },
            {
                "template_id": "command-injection",
                "name": "OS Command Injection",
                "severity": "critical",
                "host": "http://www.badstore.net",
                "matched_url": "http://www.badstore.net/cgi-bin/badstore.cgi?action=trackinput&tracknum=1234;ls+-la",
                "type": "http",
                "description": "The order tracking field is vulnerable to OS command injection. Appending shell commands executes them on the server.",
                "payload_used": "1234; cat /etc/passwd",
                "extracted_results": [
                    "root:x:0:0:root:/root:/bin/bash",
                    "www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin",
                ],
                "remediation": "Never pass user input to shell commands. Implement strict input validation.",
                "cvss_score": 10.0,
                "tags": ["command-injection", "rce", "critical"],
            },
            {
                "template_id": "cleartext-credit-card",
                "name": "Credit Card Data Stored in Cleartext",
                "severity": "critical",
                "host": "http://www.badstore.net",
                "matched_url": "http://www.badstore.net/cgi-bin/badstore.cgi?action=viewcart",
                "type": "http",
                "description": "Credit card numbers are stored and transmitted in plaintext. PCI-DSS violation.",
                "extracted_results": [
                    "Card Number: 4111111111111111",
                    "Expiry: 12/26",
                    "CVV: 123",
                    "Cardholder: John Doe",
                ],
                "remediation": "Encrypt all PAN data at rest using AES-256. Tokenize card data.",
                "cvss_score": 10.0,
                "tags": ["pci-dss", "cleartext", "credit-card", "critical"],
            },
            {
                "template_id": "exposed-backup-files",
                "name": "Backup Files Publicly Accessible",
                "severity": "high",
                "host": "http://www.badstore.net",
                "matched_url": "http://www.badstore.net/backup/",
                "type": "file",
                "description": "Backup directory is publicly accessible containing database dumps and source code.",
                "exposed_files": [
                    "/backup/badstore_db.sql",
                    "/backup/badstore_src.tar.gz",
                    "/backup/config_backup.txt",
                ],
                "remediation": "Remove backup files from web-accessible directories.",
                "cvss_score": 8.6,
                "tags": ["backup", "exposure", "sensitive-data"],
            },
            {
                "template_id": "weak-session-token",
                "name": "Weak Sequential Session Token",
                "severity": "high",
                "host": "http://www.badstore.net",
                "matched_url": "http://www.badstore.net/cgi-bin/badstore.cgi?action=login",
                "type": "http",
                "description": "Session tokens are sequential integers making them trivially predictable and brute-forceable.",
                "evidence": "Set-Cookie: SESSIONID=1042; path=/",
                "remediation": "Use cryptographically secure random session tokens of at least 128 bits.",
                "cvss_score": 8.1,
                "tags": ["session", "weak-token", "hijack"],
            },
        ],
        "zap_findings": [
            {
                "alert": "SQL Injection",
                "risk": "High",
                "confidence": "High",
                "url": "http://www.badstore.net/cgi-bin/badstore.cgi",
                "method": "POST",
                "param": "email",
                "description": "SQL injection confirmed in login email field. Authentication fully bypassable.",
                "solution": "Use prepared statements and parameterized queries.",
                "cweid": "89",
                "wascid": "19",
            },
            {
                "alert": "Cross Site Scripting (Reflected)",
                "risk": "High",
                "confidence": "Medium",
                "url": "http://www.badstore.net/cgi-bin/badstore.cgi",
                "method": "GET",
                "param": "searchquery",
                "description": "Reflected XSS in search functionality.",
                "solution": "HTML-encode all user-supplied data before rendering.",
                "cweid": "79",
                "wascid": "8",
            },
            {
                "alert": "Sensitive Data Exposed in URL",
                "risk": "Medium",
                "confidence": "High",
                "url": "http://www.badstore.net/cgi-bin/badstore.cgi?action=login",
                "method": "GET",
                "param": "password",
                "description": "Login credentials passed as GET parameters visible in logs and browser history.",
                "solution": "Always use POST for login forms. Never pass credentials in URL parameters.",
                "cweid": "598",
                "wascid": "13",
            },
            {
                "alert": "Cookie Without Secure Flag",
                "risk": "Low",
                "confidence": "Medium",
                "url": "http://www.badstore.net/cgi-bin/badstore.cgi?action=login",
                "method": "POST",
                "param": "SESSIONID",
                "description": "Session cookie transmitted without Secure flag.",
                "solution": "Set Secure flag on all session cookies.",
                "cweid": "614",
                "wascid": "13",
            },
        ],
        "summary": {
            "total_findings": 9,
            "by_severity": {
                "critical": 3,
                "high": 4,
                "medium": 1,
                "low": 1,
                "informational": 0,
            },
            "overall_risk_score": 9.8,
            "risk_level": "CRITICAL",
            "tools_run": ["nuclei (pre-loaded)", "zap (pre-loaded)"],
            "top_priority_fixes": [
                "Fix SQL Injection in login form immediately",
                "Remove OS command injection in order tracking",
                "Encrypt all credit card data — PCI-DSS violation",
                "Remove publicly accessible backup directory",
                "Replace sequential session tokens with cryptographically secure tokens",
            ],
        },
    },
}


def _get_preloaded_key(target_url: str) -> str | None:
    """
    Return the matching key from _PRELOADED_TARGETS if target_url
    matches a known demo site, otherwise return None.
    Matching is done on the hostname only so http/https and trailing
    slashes don't matter.
    """
    from urllib.parse import urlparse
    host = urlparse(target_url).hostname or target_url.lower()
    for key in _PRELOADED_TARGETS:
        if host == key or host.endswith("." + key):
            return key
    return None


def _write_preloaded_results(scan_id: str, target_url: str, key: str) -> Path:
    """
    Write the pre-loaded JSON for *key* into temp_results and return its path.
    Injects the live scan_id so every file has a unique name.
    """
    payload = dict(_PRELOADED_TARGETS[key])          # shallow copy
    payload["meta"] = dict(payload["meta"])           # decouple nested dict
    payload["meta"]["scan_id"] = scan_id
    payload["meta"]["generated_at"] = datetime.now(timezone.utc).isoformat()

    out_path = RESULTS_DIR / f"{scan_id}_raw.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.info("[%s] Pre-loaded results written → %s", scan_id, out_path)
    return out_path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _binary_available(name: str) -> bool:
    """Return True if *name* is on PATH."""
    return shutil.which(name) is not None


async def _stream_process(
    scan_id: str,
    cmd: str,
    ws_manager: ConnectionManager,
    tag: str = "",
) -> int:
    """
    Launch *cmd* as an async subprocess, stream every stdout/stderr line to
    the WebSocket, and return the process exit code.
    """
    logger.info("[%s] Running: %s", scan_id, cmd)
    prefix = f"[{tag}] " if tag else ""

    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,  # merge stderr into stdout
    )

    # Read lines until EOF
    assert proc.stdout is not None
    while True:
        raw = await proc.stdout.readline()
        if not raw:
            break
        line = raw.decode(errors="replace").rstrip()
        msg = f"{prefix}{line}"
        logger.debug(msg)
        await ws_manager.broadcast(scan_id, msg)

    await proc.wait()
    return proc.returncode


# ---------------------------------------------------------------------------
# Mock data generator
# ---------------------------------------------------------------------------

def _write_mock_results(scan_id: str, target_url: str) -> Path:
    """
    Write a realistic-looking fake scan result JSON and return its path.
    The structure mirrors what a real Nuclei + ZAP combined report would
    contain, giving the AI team actual data shapes to work with.
    """
    now = datetime.now(timezone.utc).isoformat()

    payload = {
        "meta": {
            "scan_id": scan_id,
            "target": target_url,
            "generated_at": now,
            "mode": "mock",
            "note": "Mock data — real tools were unavailable at scan time.",
        },
        "nuclei_findings": [
            {
                "template_id": "exposed-git-config",
                "name": "Exposed .git Configuration",
                "severity": "high",
                "description": (
                    "The /.git/config file is publicly accessible. "
                    "This can leak repository metadata, remote URLs, and branch names."
                ),
                "matched_url": f"{target_url}/.git/config",
                "curl_command": f"curl -X GET {target_url}/.git/config",
                "timestamp": now,
                "tags": ["exposure", "git", "config"],
                "references": [
                    "https://owasp.org/www-project-web-security-testing-guide/",
                ],
                "remediation": "Block access to /.git/ via web-server configuration.",
            },
            {
                "template_id": "http-missing-security-headers",
                "name": "Missing Security Headers",
                "severity": "medium",
                "description": (
                    "The server response is missing several recommended HTTP security headers."
                ),
                "matched_url": target_url,
                "missing_headers": [
                    "Strict-Transport-Security",
                    "X-Frame-Options",
                    "X-Content-Type-Options",
                    "Content-Security-Policy",
                    "Referrer-Policy",
                ],
                "timestamp": now,
                "tags": ["headers", "hardening"],
                "references": [
                    "https://securityheaders.com/",
                ],
                "remediation": "Add the missing headers in your web server or application middleware.",
            },
            {
                "template_id": "open-redirect",
                "name": "Open Redirect",
                "severity": "medium",
                "description": (
                    "A redirect parameter accepts arbitrary URLs, enabling phishing attacks."
                ),
                "matched_url": f"{target_url}/login?redirect=https://evil.com",
                "timestamp": now,
                "tags": ["redirect", "owasp-top10"],
                "remediation": "Validate and allowlist redirect targets on the server side.",
            },
        ],
        "zap_findings": [
            {
                "alert": "X-Frame-Options Header Not Set",
                "risk": "Medium",
                "confidence": "Medium",
                "description": (
                    "X-Frame-Options header is not included in the HTTP response "
                    "to protect against Clickjacking attacks."
                ),
                "url": target_url,
                "solution": "Most modern Web servers can be configured to set this header.",
                "reference": "https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Frame-Options",
                "cweid": "1021",
                "wascid": "15",
            },
            {
                "alert": "Cookie Without SameSite Attribute",
                "risk": "Low",
                "confidence": "Medium",
                "description": (
                    "A cookie has been set without the SameSite attribute, which means "
                    "that the cookie can be sent as a result of a cross-site request."
                ),
                "url": target_url,
                "solution": "Ensure that the SameSite attribute is set to either 'lax' or ideally 'strict'.",
                "reference": "https://tools.ietf.org/html/draft-ietf-httpbis-cookie-same-site",
                "cweid": "1275",
                "wascid": "13",
            },
            {
                "alert": "Server Leaks Version Information via 'Server' HTTP Response Header",
                "risk": "Low",
                "confidence": "High",
                "description": (
                    "The web/application server is leaking version information via the 'Server' "
                    "HTTP response header. Access to such information may facilitate attackers "
                    "identifying other vulnerabilities your version of software is subject to."
                ),
                "url": target_url,
                "solution": "Ensure that your web server, application server, etc. is configured to suppress the 'Server' header.",
                "reference": "https://httpd.apache.org/docs/current/mod/core.html#servertokens",
                "cweid": "200",
                "wascid": "13",
            },
        ],
        "summary": {
            "total_findings": 6,
            "by_severity": {
                "critical": 0,
                "high": 1,
                "medium": 3,
                "low": 2,
                "informational": 0,
            },
            "tools_run": ["nuclei (mock)", "zap (mock)"],
        },
    }

    out_path = RESULTS_DIR / f"{scan_id}_raw.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.info("[%s] Mock results written → %s", scan_id, out_path)
    return out_path


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def run_security_tools(
    scan_id: str,
    target_url: str,
    scan_mode: str,
    ws_manager: ConnectionManager,
) -> None:
    """
    Orchestrate the full scan for *scan_id*.

    Called as a background task — never awaited by the HTTP handler.
    Updates `scan_registry[scan_id]` throughout execution.
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    scan_registry[scan_id] = {
        "status": "running",
        "mock_mode": False,
        "started_at": time.time(),
        "result_file": None,
    }

    await ws_manager.broadcast(scan_id, f"[PHANTOM] Scan {scan_id} started — mode={scan_mode}")
    await ws_manager.broadcast(scan_id, f"[PHANTOM] Target: {target_url}")

    # ------------------------------------------------------------------
    # 1. PRE-LOADED MODE (Highest Priority)
    # ------------------------------------------------------------------
    preloaded_key = _get_preloaded_key(target_url)
    
    if preloaded_key:
        await ws_manager.broadcast(scan_id, f"[PHANTOM] 🎯 Known demo target detected: {target_url}")
        await ws_manager.broadcast(scan_id, "[PHANTOM] ⚡ Engaging PRE-LOADED MODE. Injecting real scan data...")
        
        # Simulate a slight processing delay so the frontend terminal looks realistic
        await asyncio.sleep(3) 

        # Write the preloaded file and update registry
        result_file = _write_preloaded_results(scan_id, target_url, preloaded_key)
        scan_registry[scan_id]["result_file"] = str(result_file)
        
        scan_registry[scan_id]["status"] = "completed"
        await ws_manager.broadcast(scan_id, "[PHANTOM] ✅ Scan completed successfully (Pre-loaded).")
        
        return  # EXIT EARLY! Do not run tools or mock pings.

    # ------------------------------------------------------------------
    # 2. Determine whether real tools are available (Fallback)
    # ------------------------------------------------------------------
    has_zap = _binary_available("zap.sh") or _binary_available("zap")
    has_nuclei = _binary_available("nuclei")
    use_mock = not (has_zap and has_nuclei)

    if use_mock:
        await ws_manager.broadcast(
            scan_id,
            "[PHANTOM] ⚠️  Real tools (ZAP / Nuclei) not found — engaging MOCK MODE.",
        )
        scan_registry[scan_id]["mock_mode"] = True

    try:
        if use_mock:
            # ------------------------------------------------------------------
            # MOCK MODE — use ping to simulate a live streaming process
            # ------------------------------------------------------------------
            is_windows = platform.system().lower() == "windows"
            from urllib.parse import urlparse
            parsed = urlparse(target_url)
            host = parsed.hostname or target_url

            if is_windows:
                ping_cmd = f"ping -n 5 {host}"
            else:
                ping_cmd = f"ping -c 5 {host}"

            await ws_manager.broadcast(scan_id, f"[MOCK] Running: {ping_cmd}")
            rc = await _stream_process(scan_id, ping_cmd, ws_manager, tag="MOCK/ping")

            await ws_manager.broadcast(
                scan_id,
                f"[MOCK] Ping finished (exit={rc}). Generating dummy findings…",
            )

            result_file = _write_mock_results(scan_id, target_url)
            scan_registry[scan_id]["result_file"] = str(result_file)

            await ws_manager.broadcast(
                scan_id,
                f"[MOCK] Results saved → {result_file}",
            )

        else:
            # ------------------------------------------------------------------
            # REAL MODE — ZAP then Nuclei
            # ------------------------------------------------------------------
            zap_out = RESULTS_DIR / f"{scan_id}_zap.json"
            nuclei_out = RESULTS_DIR / f"{scan_id}_nuclei.json"

            zap_bin = shutil.which("zap") or shutil.which("zap.sh") or "zap"

            # --- ZAP ---
            zap_cmd = (
                f'"{zap_bin}" -cmd -quickurl {target_url} '
                f"-quickout {zap_out} -quickprogress"
            )
            await ws_manager.broadcast(scan_id, f"[ZAP] Starting passive scan… ({zap_bin})")
            zap_rc = await _stream_process(scan_id, zap_cmd, ws_manager, tag="ZAP")
            await ws_manager.broadcast(scan_id, f"[ZAP] Finished (exit={zap_rc}).")

            # --- Nuclei ---
            nuclei_cmd = f"nuclei -u {target_url} -j -o {nuclei_out}"
            await ws_manager.broadcast(scan_id, "[NUCLEI] Starting template scan…")
            nuclei_rc = await _stream_process(scan_id, nuclei_cmd, ws_manager, tag="NUCLEI")
            await ws_manager.broadcast(scan_id, f"[NUCLEI] Finished (exit={nuclei_rc}).")

            scan_registry[scan_id]["result_file"] = str(nuclei_out)

        # ------------------------------------------------------------------
        # Done
        # ------------------------------------------------------------------
        scan_registry[scan_id]["status"] = "completed"
        await ws_manager.broadcast(scan_id, "[PHANTOM] ✅ Scan completed successfully.")

    except Exception as exc:  # noqa: BLE001
        logger.exception("[%s] Unhandled error during scan", scan_id)
        scan_registry[scan_id]["status"] = "failed"
        await ws_manager.broadcast(scan_id, f"[PHANTOM] ❌ Scan failed: {exc}")