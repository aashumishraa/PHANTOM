"""
report_generator.py — Generates a professional PDF report from PHANTOM scan results.

Takes the structured JSON produced by scanner.py (nuclei_findings + zap_findings)
and produces a polished, multi-section PDF using fpdf2.

Usage (standalone):
    python report_generator.py <scan_id>

Usage (from FastAPI):
    from core.report_generator import build_pdf_report
    pdf_path = build_pdf_report(scan_data_dict, scan_id)
"""

from __future__ import annotations

import json
import os
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from fpdf import FPDF

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
DARK_BLUE   = (30,  58, 138)
MID_BLUE    = (37,  99, 235)
LIGHT_BG    = (248, 250, 252)
TEXT_DARK   = (15,  23,  42)
TEXT_MID    = (71,  85, 105)
TEXT_LIGHT  = (148, 163, 184)
RED_BG      = (254, 226, 226)
RED_TEXT    = (153,  27,  27)
ORANGE_BG   = (255, 237, 213)
ORANGE_TEXT = (154,  52,  18)
YELLOW_BG   = (254, 249, 195)
YELLOW_TEXT = (133, 100,   4)
GREEN_BG    = (220, 252, 231)
GREEN_TEXT  = ( 22, 101,  52)
BLUE_BG     = (219, 234, 254)
BLUE_TEXT   = ( 30,  64, 175)
LINE_COLOR  = (226, 232, 240)
WHITE       = (255, 255, 255)

SEVERITY_COLORS: Dict[str, tuple] = {
    "critical": (RED_BG,    RED_TEXT,    (239,  68,  68)),
    "high":     (ORANGE_BG, ORANGE_TEXT, (249, 115,  22)),
    "medium":   (YELLOW_BG, YELLOW_TEXT, (234, 179,   8)),
    "low":      (BLUE_BG,   BLUE_TEXT,   ( 59, 130, 246)),
    "info":     (LIGHT_BG,  TEXT_MID,    (148, 163, 184)),
    "High":     (ORANGE_BG, ORANGE_TEXT, (249, 115,  22)),
    "Medium":   (YELLOW_BG, YELLOW_TEXT, (234, 179,   8)),
    "Low":      (BLUE_BG,   BLUE_TEXT,   ( 59, 130, 246)),
    "Info":     (LIGHT_BG,  TEXT_MID,    (148, 163, 184)),
}


# ---------------------------------------------------------------------------
# Helper: safe multi_cell text (strips None, normalises newlines)
# ---------------------------------------------------------------------------
def _safe(text: Any, maxlen: int = 800) -> str:
    if text is None:
        return ""
    s = str(text).replace("\r\n", "\n").replace("\r", "\n")
    return s[:maxlen]


def _wrap(text: str, width: int = 95) -> List[str]:
    """Wrap long strings so fpdf never overflows."""
    lines = []
    for paragraph in text.split("\n"):
        if paragraph.strip():
            lines.extend(textwrap.wrap(paragraph, width=width) or [paragraph])
        else:
            lines.append("")
    return lines


# ---------------------------------------------------------------------------
# PDF class
# ---------------------------------------------------------------------------
class PhantomReport(FPDF):
    def __init__(self, target_url: str, generated_at: str):
        super().__init__()
        self.target_url = target_url
        self.generated_at = generated_at
        self.set_margins(15, 15, 15)
        self.set_auto_page_break(auto=True, margin=20)

    # ── Running header ──────────────────────────────────────────────────────
    def header(self):
        # Top accent bar
        self.set_fill_color(*DARK_BLUE)
        self.rect(0, 0, 210, 10, "F")

        self.set_y(14)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*TEXT_LIGHT)
        self.cell(0, 6, "PHANTOM  ·  Security Assessment Report  ·  CONFIDENTIAL", align="C")
        self.ln(3)
        self.set_draw_color(*LINE_COLOR)
        self.set_line_width(0.3)
        self.line(15, self.get_y(), 195, self.get_y())
        self.ln(4)

    # ── Running footer ──────────────────────────────────────────────────────
    def footer(self):
        self.set_y(-15)
        self.set_draw_color(*LINE_COLOR)
        self.line(15, self.get_y(), 195, self.get_y())
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*TEXT_LIGHT)
        self.cell(0, 10, f"Page {self.page_no()} — Generated {self.generated_at} — PHANTOM v1.0", align="C")

    # ── Section heading ─────────────────────────────────────────────────────
    def section_heading(self, title: str):
        self.ln(4)
        self.set_fill_color(*DARK_BLUE)
        self.set_text_color(*WHITE)
        self.set_font("Helvetica", "B", 11)
        self.cell(0, 9, f"  {title}", ln=True, fill=True)
        self.ln(3)

    # ── Key-value pair ──────────────────────────────────────────────────────
    def kv_row(self, key: str, value: str, shade: bool = False):
        if shade:
            self.set_fill_color(*LIGHT_BG)
        else:
            self.set_fill_color(*WHITE)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*TEXT_MID)
        self.cell(45, 7, key, fill=True)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*TEXT_DARK)
        self.multi_cell(0, 7, _safe(value, 200), fill=True)

    # ── Severity badge ──────────────────────────────────────────────────────
    def severity_badge(self, sev: str):
        colors = SEVERITY_COLORS.get(sev, SEVERITY_COLORS["info"])
        bg, fg, _ = colors
        self.set_fill_color(*bg)
        self.set_text_color(*fg)
        self.set_font("Helvetica", "B", 8)
        self.cell(22, 6, sev.upper(), border=0, fill=True, align="C")
        self.set_text_color(*TEXT_DARK)

    # ── Finding card ────────────────────────────────────────────────────────
    def finding_card(self, index: int, title: str, sev: str, url: str,
                     description: str, remediation: str = "",
                     evidence: List[str] | None = None,
                     tags: List[str] | None = None,
                     cvss: float | None = None,
                     tool: str = ""):

        colors = SEVERITY_COLORS.get(sev, SEVERITY_COLORS["info"])
        _, _, accent = colors

        # Left accent stripe
        start_y = self.get_y()
        self.set_draw_color(*accent)
        self.set_line_width(1.5)

        # Card background
        self.set_fill_color(*LIGHT_BG)
        self.rect(15, start_y, 180, 6, "F")

        # Finding number + title
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*TEXT_DARK)
        title_short = _safe(title, 80)
        self.cell(8, 6, f"{index}.", fill=False)
        self.severity_badge(sev)
        self.set_x(self.get_x() + 2)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*TEXT_DARK)
        self.cell(0, 6, title_short, ln=True)

        # Draw left stripe now we know the height
        self.set_draw_color(*accent)
        self.line(15, start_y, 15, self.get_y())
        self.set_line_width(0.3)

        # Tool + CVSS
        meta_parts = []
        if tool:
            meta_parts.append(f"Tool: {tool}")
        if cvss is not None:
            meta_parts.append(f"CVSS: {cvss}")
        if meta_parts:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(*TEXT_LIGHT)
            self.cell(0, 5, "  " + "   |   ".join(meta_parts), ln=True)

        # URL
        if url:
            self.set_font("Helvetica", "", 8)
            self.set_text_color(*MID_BLUE)
            self.cell(0, 5, "  " + _safe(url, 110), ln=True)

        # Description
        if description:
            self.set_font("Helvetica", "", 9)
            self.set_text_color(*TEXT_DARK)
            for line in _wrap(_safe(description)):
                self.cell(5)
                self.cell(0, 5, line, ln=True)

        # Evidence block
        if evidence:
            self.ln(1)
            self.set_fill_color(15, 23, 42)
            self.set_text_color(134, 239, 172)   # green-300
            self.set_font("Courier", "", 8)
            for ev in evidence[:6]:
                self.set_fill_color(15, 23, 42)
                self.cell(5)
                self.cell(0, 5, _safe(ev, 100), fill=True, ln=True)
            self.set_text_color(*TEXT_DARK)

        # Remediation
        if remediation:
            self.ln(1)
            self.set_font("Helvetica", "B", 8)
            self.set_text_color( 22, 101, 52)   # green
            self.cell(5)
            self.cell(0, 5, "✔ Remediation:", ln=True)
            self.set_font("Helvetica", "", 8)
            for line in _wrap(_safe(remediation)):
                self.cell(8)
                self.cell(0, 5, line, ln=True)
            self.set_text_color(*TEXT_DARK)

        # Tags
        if tags:
            self.ln(1)
            self.set_font("Helvetica", "", 7)
            self.set_text_color(*TEXT_LIGHT)
            self.cell(5)
            self.cell(0, 4, "  ".join(f"[{t}]" for t in tags[:8]), ln=True)

        self.ln(4)
        self.set_draw_color(*LINE_COLOR)
        self.line(15, self.get_y(), 195, self.get_y())
        self.ln(3)
        self.set_line_width(0.3)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_pdf_report(data: dict, scan_id: str, output_dir: str | Path = "./temp_reports") -> Path:
    """
    Build a PDF report from a scan result dict and return the output path.

    Parameters
    ----------
    data       : dict  — the scan result JSON (as parsed by json.load)
    scan_id    : str   — UUID of the scan (used for filename)
    output_dir : path  — where to save the PDF
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # ── Extract fields ──────────────────────────────────────────────────────
    meta        = data.get("meta") or data.get("scan_metadata") or {}
    target_url  = (
        meta.get("target_url") or meta.get("target")
        or data.get("scan_metadata", {}).get("target_url", "Unknown")
    )
    scan_mode   = meta.get("scan_mode", "quick")
    duration    = meta.get("duration_seconds")
    tools_used  = meta.get("tools_used") or data.get("scan_metadata", {}).get("tools_used", [])

    nuclei_findings: List[Dict] = data.get("nuclei_findings") or []
    zap_findings:    List[Dict] = data.get("zap_findings")    or []
    summary:         Dict       = data.get("summary")         or {}

    by_sev      = summary.get("by_severity") or {}
    risk_score  = summary.get("overall_risk_score")
    risk_level  = summary.get("risk_level", "UNKNOWN")
    top_fixes   = summary.get("top_priority_fixes") or []
    total_finds = summary.get("total_findings", len(nuclei_findings) + len(zap_findings))

    # ── Init PDF ────────────────────────────────────────────────────────────
    pdf = PhantomReport(target_url=str(target_url), generated_at=now_str)
    pdf.add_page()

    # ══════════════════════════════════════════════════════════════════════
    # COVER BLOCK
    # ══════════════════════════════════════════════════════════════════════
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*DARK_BLUE)
    pdf.cell(0, 12, "PHANTOM", ln=True, align="C")
    pdf.set_font("Helvetica", "", 13)
    pdf.set_text_color(*TEXT_MID)
    pdf.cell(0, 8, "Autonomous Security Assessment Report", ln=True, align="C")
    pdf.ln(4)

    pdf.set_draw_color(*DARK_BLUE)
    pdf.set_line_width(0.5)
    pdf.line(40, pdf.get_y(), 170, pdf.get_y())
    pdf.ln(6)

    # Scan meta box
    pdf.set_fill_color(*LIGHT_BG)
    pdf.set_draw_color(*LINE_COLOR)
    pdf.set_line_width(0.3)
    pdf.rect(15, pdf.get_y(), 180, 40, "FD")
    pdf.ln(3)

    pdf.kv_row("Target:", str(target_url), shade=False)
    pdf.kv_row("Scan ID:", scan_id, shade=True)
    pdf.kv_row("Scan Mode:", scan_mode.upper(), shade=False)
    pdf.kv_row("Generated:", now_str, shade=True)
    if duration:
        pdf.kv_row("Duration:", f"{duration} seconds", shade=False)
    if tools_used:
        pdf.kv_row("Tools Used:", ", ".join(tools_used), shade=True)
    pdf.ln(4)

    # ── Risk Score Banner ────────────────────────────────────────────────────
    if risk_score is not None:
        if risk_score >= 9:
            banner_bg, banner_fg = RED_BG, RED_TEXT
        elif risk_score >= 7:
            banner_bg, banner_fg = ORANGE_BG, ORANGE_TEXT
        elif risk_score >= 4:
            banner_bg, banner_fg = YELLOW_BG, YELLOW_TEXT
        else:
            banner_bg, banner_fg = GREEN_BG, GREEN_TEXT

        pdf.set_fill_color(*banner_bg)
        pdf.set_text_color(*banner_fg)
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 13, f"  ⚠  Overall Risk Score: {risk_score} / 10  —  {risk_level}", ln=True, fill=True)
        pdf.ln(4)

    # ══════════════════════════════════════════════════════════════════════
    # EXECUTIVE SUMMARY
    # ══════════════════════════════════════════════════════════════════════
    pdf.section_heading("Executive Summary")

    sev_order = ["critical", "high", "medium", "low", "informational"]
    col_w = 36
    # Severity table header
    pdf.set_fill_color(*DARK_BLUE)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 9)
    for sev in sev_order:
        pdf.cell(col_w, 7, sev.upper(), border=1, align="C", fill=True)
    pdf.cell(0, 7, "TOTAL", border=1, align="C", fill=True)
    pdf.ln()

    # Severity counts
    pdf.set_text_color(*TEXT_DARK)
    pdf.set_font("Helvetica", "B", 11)
    for sev in sev_order:
        count = by_sev.get(sev, 0)
        colors = SEVERITY_COLORS.get(sev, SEVERITY_COLORS["info"])
        pdf.set_fill_color(*colors[0])
        pdf.set_text_color(*colors[1])
        pdf.cell(col_w, 8, str(count), border=1, align="C", fill=True)
    pdf.set_fill_color(*LIGHT_BG)
    pdf.set_text_color(*TEXT_DARK)
    pdf.cell(0, 8, str(total_finds), border=1, align="C", fill=True)
    pdf.ln(8)

    # Top priority fixes
    if top_fixes:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*RED_TEXT)
        pdf.cell(0, 7, "Top Priority Fixes:", ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*TEXT_DARK)
        for i, fix in enumerate(top_fixes[:8], 1):
            pdf.cell(6)
            pdf.cell(0, 6, f"{i}.  {_safe(fix, 120)}", ln=True)
        pdf.ln(4)

    # ══════════════════════════════════════════════════════════════════════
    # NUCLEI FINDINGS
    # ══════════════════════════════════════════════════════════════════════
    if nuclei_findings:
        pdf.section_heading(f"Nuclei Findings  ({len(nuclei_findings)} total)")
        for i, f in enumerate(nuclei_findings, 1):
            pdf.finding_card(
                index       = i,
                title       = f.get("name", f.get("template_id", "Unknown")),
                sev         = f.get("severity", "info"),
                url         = f.get("matched_url") or f.get("host", ""),
                description = f.get("description", ""),
                remediation = f.get("remediation", ""),
                evidence    = f.get("extracted_results"),
                tags        = f.get("tags"),
                cvss        = f.get("cvss_score"),
                tool        = "Nuclei",
            )

    # ══════════════════════════════════════════════════════════════════════
    # OWASP ZAP FINDINGS
    # ══════════════════════════════════════════════════════════════════════
    if zap_findings:
        pdf.section_heading(f"OWASP ZAP Findings  ({len(zap_findings)} total)")
        for i, f in enumerate(zap_findings, 1):
            pdf.finding_card(
                index       = i,
                title       = f.get("alert", "Unknown"),
                sev         = f.get("risk", "info"),
                url         = f.get("url", ""),
                description = f.get("description", ""),
                remediation = f.get("solution", ""),
                tags        = [f"CWE-{f['cweid']}"] if f.get("cweid") else None,
                tool        = f"ZAP  |  Method: {f.get('method','')}  |  Param: {f.get('param','')}",
            )

    # ══════════════════════════════════════════════════════════════════════
    # DISCLAIMER
    # ══════════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.section_heading("Legal Disclaimer")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*TEXT_MID)
    disclaimer = (
        "This report was generated automatically by the PHANTOM autonomous penetration-testing "
        "orchestrator. All findings are based on automated scanning and should be validated by "
        "a qualified security professional before any remediation action is taken. "
        "This document is CONFIDENTIAL and intended solely for the authorised recipient. "
        "Redistribution or use outside its intended scope is strictly prohibited.\n\n"
        f"Scan performed against: {target_url}\n"
        f"Report generated: {now_str}\n"
        f"Scan ID: {scan_id}"
    )
    for line in _wrap(disclaimer, 100):
        pdf.cell(0, 6, line, ln=True)

    # ── Save ─────────────────────────────────────────────────────────────
    out_path = output_dir / f"{scan_id}_report.pdf"
    pdf.output(str(out_path))
    return out_path


# ---------------------------------------------------------------------------
# Standalone CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python report_generator.py <scan_id>")
        print("       Reads  temp_results/<scan_id>_raw.json")
        print("       Writes temp_reports/<scan_id>_report.pdf")
        sys.exit(1)

    sid = sys.argv[1]
    raw_path = Path("../temp_results") / f"{sid}_raw.json"
    if not raw_path.exists():
        print(f"ERROR: {raw_path} not found.")
        sys.exit(1)

    scan_data = json.loads(raw_path.read_text(encoding="utf-8"))
    pdf_path = build_pdf_report(scan_data, sid, output_dir="../temp_reports")
    print(f"✅  Report saved → {pdf_path}")