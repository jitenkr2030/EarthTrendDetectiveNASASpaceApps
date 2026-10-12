from __future__ import annotations

import base64
import html
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_FILE = ROOT / "data/analysis/earthtrend_final_evidence.json"
OUTPUT_FILE = ROOT / "reports/earthtrend_scientific_report.html"
FIGURE_DIR = ROOT / "data/analysis/figures"

FIGURES = [
    ("Study timeline", "earthtrend_when_timeline.png"),
    ("Rainfall and soil-moisture spatial relationship",
     "earthtrend_where_rainfall_link.png"),
    ("Soil-moisture extreme events", "earthtrend_extreme_events.png"),
    ("Rainfall association", "earthtrend_rainfall_link.png"),
    ("Final scientific finding", "earthtrend_final_finding.png"),
]


def esc(value) -> str:
    return html.escape(str(value))


def display_value(value) -> str:
    if isinstance(value, float):
        return f"{value:.6g}"
    if value is None:
        return "Not reported"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, indent=2)
    return str(value)


def render_data(value, depth=0) -> str:
    """Render nested evidence as readable HTML without assuming its schema."""
    if isinstance(value, dict):
        if not value:
            return "<p><em>No details supplied.</em></p>"
        rows = []
        for key, item in value.items():
            label = esc(str(key).replace("_", " ").replace("-", " ").title())
            if isinstance(item, dict):
                content = render_data(item, depth + 1)
            elif isinstance(item, list):
                if item and all(not isinstance(x, (dict, list)) for x in item):
                    content = "<ul>" + "".join(
                        f"<li>{esc(display_value(x))}</li>" for x in item
                    ) + "</ul>"
                else:
                    content = render_data(
                        {f"Item {i + 1}": x for i, x in enumerate(item)},
                        depth + 1,
                    )
            else:
                content = esc(display_value(item))
            rows.append(f"<tr><th>{label}</th><td>{content}</td></tr>")
        return '<table class="data-table"><tbody>' + "".join(rows) + "</tbody></table>"

    if isinstance(value, list):
        return render_data(
            {f"Item {i + 1}": item for i, item in enumerate(value)}, depth + 1
        )

    return f"<p>{esc(display_value(value))}</p>"


def figure_html(title: str, filename: str) -> str:
    path = FIGURE_DIR / filename
    if not path.is_file():
        return (
            '<div class="missing-figure"><strong>'
            f"{esc(title)}</strong><p>Figure not available: "
            f"{esc(filename)}</p></div>"
        )

    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return (
        '<figure class="figure">'
        f'<img src="data:{mime};base64,{encoded}" alt="{esc(title)}">'
        f"<figcaption>{esc(title)}</figcaption></figure>"
    )


def main() -> None:
    if not EVIDENCE_FILE.is_file():
        raise SystemExit(f"Evidence file not found: {EVIDENCE_FILE}")

    evidence = json.loads(EVIDENCE_FILE.read_text(encoding="utf-8"))
    if not isinstance(evidence, dict):
        raise SystemExit("Evidence JSON must contain a JSON object.")

    interpretation = evidence.get("INTERPRETATION", {})
    final_finding = (
        interpretation.get("final_finding")
        if isinstance(interpretation, dict)
        else None
    )
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    sections = []
    for key in ("DATA", "EVIDENCE", "INTERPRETATION", "LIMITATIONS"):
        value = evidence.get(key)
        if value is not None:
            title = key.replace("_", " ").title()
            if key == "EVIDENCE" and isinstance(value, dict):
                subsections = []
                for name, result in value.items():
                    subsections.append(
                        f"<section><h3>{esc(name.replace('_', ' ').title())}</h3>"
                        f"{render_data(result)}</section>"
                    )
                content = "".join(subsections)
            else:
                content = render_data(value)
            sections.append(
                f"<section class='report-section'><h2>{esc(title)}</h2>"
                f"{content}</section>"
            )

    figures = "".join(figure_html(title, filename)
                      for title, filename in FIGURES)

    project = esc(evidence.get("project", "EarthTrend Detective"))
    case = esc(evidence.get("case", "Soil-moisture and rainfall analysis"))
    status = esc(evidence.get("status", "Not specified"))
    final_html = (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>{project} — Scientific Report</title>"
        "<style>"
        ":root{color-scheme:light}"
        "body{font-family:Arial,Helvetica,sans-serif;line-height:1.6;"
        "max-width:1000px;margin:auto;padding:24px;color:#202938;background:#fff}"
        "header{border-bottom:3px solid #176b87;padding-bottom:18px;margin-bottom:28px}"
        "h1{font-size:2.1rem;margin-bottom:8px;color:#124559}"
        "h2{color:#124559;border-bottom:1px solid #d5e0e5;padding-bottom:8px}"
        "h3{color:#176b87;margin-top:24px}"
        ".meta{color:#52616b;font-size:.95rem}"
        ".status{display:inline-block;padding:4px 10px;border-radius:6px;"
        "background:#e4f4eb;color:#155d38;font-weight:bold}"
        ".finding{padding:18px;background:#f0f7fa;border-left:4px solid #176b87;"
        "border-radius:4px}"
        ".data-table{width:100%;border-collapse:collapse;margin:12px 0 24px;"
        "overflow-wrap:anywhere}"
        ".data-table th,.data-table td{padding:9px;border:1px solid #dce4e8;"
        "text-align:left;vertical-align:top}"
        ".data-table th{width:28%;background:#f4f7f8}"
        ".data-table pre{white-space:pre-wrap;overflow-wrap:anywhere}"
        ".figure{margin:24px 0;text-align:center;page-break-inside:avoid}"
        ".figure img{max-width:100%;height:auto;border:1px solid #dce4e8;"
        "border-radius:6px}"
        "figcaption{margin-top:8px;color:#52616b;font-size:.95rem}"
        ".missing-figure{padding:12px;border:1px dashed #999;margin:12px 0}"
        "footer{border-top:1px solid #d5e0e5;margin-top:36px;padding-top:14px;"
        "font-size:.9rem;color:#52616b}"
        "@media print{body{max-width:none;padding:0}h2,h3{page-break-after:avoid}}"
        "</style></head><body>"
        f"<header><h1>{project}</h1><h2>{case}</h2>"
        f"<p class='meta'>Generated: {esc(generated)}</p>"
        f"<p>Evidence status: <span class='status'>{status}</span></p></header>"
        "<main>"
        "<section class='report-section'><h2>Executive Summary</h2>"
        f"<div class='finding'>{esc(final_finding or 'See detailed findings below.')}</div>"
        "<p><strong>Scientific caution:</strong> Association does not establish "
        "causation. Interpret conclusions within the documented data coverage, "
        "methods, and limitations.</p></section>"
        "<section class='report-section'><h2>Scientific Methodology</h2>"
        "<h3>Study coverage and data alignment</h3>"
        "<p>Monthly NASA SMAP soil-moisture observations cover Jharkhand "
        "from April 2015 through September 2026. The NASA GPM IMERG rainfall "
        "comparison covers the common period April 2015 through September "
        "2025. SMAP cells are matched to nearby GPM grid cells. The datasets "
        "have different spatial resolutions, and matched observations are "
        "not fully independent.</p>"
        "<h3>Trend analysis</h3>"
        "<p>Sen's slope summarizes trend magnitude, and a Kendall/"
        "Mann–Kendall-style test evaluates monotonic trend evidence. Seasonal "
        "and cell-level results are examined separately. The Benjamini–"
        "Hochberg false-discovery-rate procedure is used for documented "
        "multiple-comparison analyses.</p>"
        "<h3>Extreme-event screening</h3>"
        "<p>Standardized soil-moisture anomalies screen unusually dry and "
        "wet cell-months. A candidate month requires at least 5% of the "
        "984 cells (50 or more cells) to reach z ≤ −2 for dry conditions "
        "or z ≥ +2 for wet conditions. These are screening definitions, "
        "not proof of impacts or causes.</p>"
        "<h3>Rainfall association</h3>"
        "<p>Pearson correlation measures linear association between "
        "standardized rainfall and soil-moisture anomalies; Spearman "
        "correlation provides a rank-based comparison. Lagged and seasonal "
        "associations are also examined. An effective-sample-size adjustment "
        "addresses temporal autocorrelation in the reported overall rainfall "
        "association. Correlation does not establish causality.</p>"
        "<h3>Interpretation safeguards</h3>"
        "<p>A non-significant trend does not prove that no change occurred. "
        "The primary trend test is not a fully seasonality- and "
        "autocorrelation-corrected trend model, and the seasonal analysis "
        "is not a fully autocorrelation-corrected Seasonal Mann–Kendall "
        "implementation. Spatial dependence, grid-resolution differences, "
        "small seasonal samples, and event-threshold choices limit "
        "interpretation. This report reproduces saved evidence; it does not "
        "recalculate statistical results.</p></section>"
        + "".join(sections)
        + "<section class='report-section'><h2>Figures</h2>"
        + figures
        + "</section></main>"
        "<footer>Generated from the project's evidence JSON. "
        "Values and conclusions are reported from that file; this exporter "
        "does not recalculate statistical results. Review the source data and "
        "methodology before using this report for formal decisions.</footer>"
        "</body></html>"
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(final_html, encoding="utf-8")

    print("PASS: Scientific report generated.")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Evidence status: {evidence.get('status', 'Not specified')}")
    print(f"Embedded figures available: {sum((FIGURE_DIR / f).is_file() for _, f in FIGURES)}/{len(FIGURES)}")
    print(f"Report size: {OUTPUT_FILE.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
