"""
Statisches HTML-Dashboard fuer das Release- und Compliance-Center.

Konsumiert das vom Testprotokoll-Generator erzeugte
`tests/concept/reports/protocol.json` und rendert daraus eine
eigenstaendige HTML-Datei mit:

  * Header inkl. Projekt/Branch/Versions-Code/Generation-Zeit
  * Release-Reifegrad-Card mit Status-Pill (GO/HOLD/BLOCK)
  * KPI-Karten: Tests, Crash-Free (Platzhalter), Privacy, Security,
    Negative, Members, Release-Gate
  * Bereichstabelle mit allen Markern (passed/failed/error/skipped)
  * Fehlerbericht-Liste (sofern vorhanden)
  * Vollstaendige Testliste mit Statusfarbe und Suchfeld

Die HTML-Datei ist self-contained (kein externes CSS/JS), funktioniert
offline und kann als CI-Artefakt ausgeliefert werden. Sie ist die
direkt nutzbare Vorab-Visualisierung des in UI_CONCEPT.md beschriebenen
QA-Cockpits.

Aufruf:

    python -m tools.dashboard                       # Default-Pfade
    python -m tools.dashboard --json path.json      # alternative Eingabe
    python -m tools.dashboard --out  path.html      # alternatives Ziel
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import platform
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON = REPO_ROOT / "tests" / "concept" / "reports" / "protocol.json"
DEFAULT_HTML = REPO_ROOT / "tests" / "concept" / "reports" / "dashboard.html"


# Konzept-Bereiche aus UI_CONCEPT.md / TESTING.md
MARKER_LABEL = {
    "members":       "Mitglieder-Szenarien",
    "roles":         "Rollen / Berechtigungen",
    "combinatorics": "Pairwise-Matrix",
    "property":      "Property-Tests",
    "negative":      "Negativtests",
    "privacy":       "Datenschutztests",
    "security":      "Security-Negativ",
    "release_gate":  "Release-Gate (J + J2)",
}


# ---------------------------------------------------------------------------
# Status-Helfer
# ---------------------------------------------------------------------------
def _bucket_status(bucket: dict) -> str:
    if not isinstance(bucket, dict):
        return "unknown"
    if bucket.get("failed", 0) or bucket.get("error", 0):
        return "block"
    if bucket.get("count", 0) == 0:
        return "unknown"
    if bucket.get("skipped", 0) > bucket.get("passed", 0):
        return "hold"
    return "go"


def _decision_status(decision: str) -> str:
    return {
        "GO": "go", "go": "go",
        "NO-GO": "block", "no-go": "block",
        "HOLD": "hold", "hold": "hold",
    }.get(decision, "unknown")


def _coverage_pct(b: dict) -> int:
    n = b.get("count", 0)
    if not n:
        return 0
    return int(round(100 * b.get("passed", 0) / n))


# ---------------------------------------------------------------------------
# HTML-Bausteine
# ---------------------------------------------------------------------------
CSS = """
:root {
  --bg: #f7f8fa;
  --surface: #ffffff;
  --surface-muted: #f1f3f7;
  --border: #e1e4ea;
  --text: #131720;
  --text-muted: #54607a;
  --primary: #0b5fff;
  --go: #1b873b;
  --hold: #b54708;
  --block: #b42318;
  --unknown: #6b7280;
  --go-bg: #e7f5ec;
  --hold-bg: #fdf2e3;
  --block-bg: #fdecea;
  --unknown-bg: #eef0f4;
  --shadow: 0 1px 2px rgba(16, 24, 40, 0.06),
            0 1px 3px rgba(16, 24, 40, 0.08);
  --radius: 12px;
  --mono: 'SFMono-Regular', ui-monospace, 'Cascadia Mono', 'JetBrains Mono', Menlo, Consolas, monospace;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0f1115;
    --surface: #161a23;
    --surface-muted: #1d2230;
    --border: #2a3041;
    --text: #e9edf6;
    --text-muted: #98a2b8;
    --primary: #79a6ff;
    --go: #34a853;
    --hold: #f9a825;
    --block: #f87171;
    --unknown: #9ca3af;
    --go-bg: #0e2818;
    --hold-bg: #2a1c08;
    --block-bg: #2a0f0f;
    --unknown-bg: #1d2230;
  }
}

* { box-sizing: border-box; }
body {
  background: var(--bg); color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
  font-size: 14px; line-height: 1.5; margin: 0; padding: 0;
}
header {
  display: flex; align-items: center; justify-content: space-between;
  gap: 12px; padding: 14px 24px; background: var(--surface);
  border-bottom: 1px solid var(--border);
}
header .logo { font-weight: 700; font-size: 16px; }
header .meta { color: var(--text-muted); font-size: 13px; font-family: var(--mono); }
main {
  max-width: 1440px; margin: 0 auto; padding: 24px;
  display: flex; flex-direction: column; gap: 18px;
}

.row { display: flex; gap: 18px; flex-wrap: wrap; }
.col { flex: 1 1 240px; min-width: 240px; }

.card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); box-shadow: var(--shadow);
  padding: 16px; display: flex; flex-direction: column; gap: 10px;
}
.card .title {
  display: flex; align-items: center; justify-content: space-between;
  gap: 8px;
}
.card .title h3 { margin: 0; font-size: 14px; font-weight: 600; }
.card .value   { font-size: 28px; font-weight: 700; line-height: 1.1; }
.card .sub     { font-size: 12px; color: var(--text-muted); }
.card.span-2   { flex: 2 1 520px; }
.card.span-3   { flex: 3 1 780px; }

.pill {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 3px 10px; border-radius: 999px;
  font-size: 12px; font-weight: 600; letter-spacing: 0.02em;
}
.pill::before {
  content: ""; width: 8px; height: 8px; border-radius: 50%;
  background: currentColor;
}
.pill.go      { color: var(--go);      background: var(--go-bg); }
.pill.hold    { color: var(--hold);    background: var(--hold-bg); }
.pill.block   { color: var(--block);   background: var(--block-bg); }
.pill.unknown { color: var(--unknown); background: var(--unknown-bg); }

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 14px;
}

.bar { height: 6px; border-radius: 3px; background: var(--surface-muted); overflow: hidden; }
.bar > div { height: 100%; background: var(--go); }
.bar.hold > div { background: var(--hold); }
.bar.block > div { background: var(--block); }

table {
  width: 100%; border-collapse: collapse; background: var(--surface);
  border: 1px solid var(--border); border-radius: var(--radius);
  overflow: hidden;
}
th, td {
  text-align: left; padding: 10px 12px;
  border-bottom: 1px solid var(--border); font-size: 13px;
}
th { background: var(--surface-muted); color: var(--text-muted);
     font-weight: 600; text-transform: uppercase; font-size: 11px;
     letter-spacing: 0.04em; }
tr:last-child td { border-bottom: none; }
td.num { text-align: right; font-variant-numeric: tabular-nums; }
td.id  { font-family: var(--mono); font-size: 12px; color: var(--text-muted); word-break: break-all; }

.searchbar {
  display: flex; gap: 8px; align-items: center;
}
.searchbar input {
  width: 100%; padding: 8px 12px; border: 1px solid var(--border);
  border-radius: 8px; background: var(--surface); color: var(--text);
  font-size: 13px;
}

.list { display: flex; flex-direction: column; gap: 0; }
.list > .row-item {
  display: grid; grid-template-columns: 100px 1fr 80px;
  align-items: center; gap: 12px;
  padding: 8px 12px; border-bottom: 1px solid var(--border);
  font-family: var(--mono); font-size: 12px;
}
.list > .row-item:last-child { border-bottom: none; }
.list .col-status { display: flex; }
.list .col-name { color: var(--text); word-break: break-all; }
.list .col-time { color: var(--text-muted); text-align: right;
                  font-variant-numeric: tabular-nums; }

details.failure {
  background: var(--block-bg); border-left: 4px solid var(--block);
  border-radius: 6px; padding: 10px 14px;
}
details.failure summary { cursor: pointer; font-weight: 600; color: var(--block); }
details.failure pre {
  margin: 8px 0 0 0; padding: 10px; background: var(--surface);
  border: 1px solid var(--border); border-radius: 6px;
  font-family: var(--mono); font-size: 12px; overflow-x: auto;
  white-space: pre-wrap;
}

footer {
  color: var(--text-muted); font-size: 12px; padding: 20px 24px;
  text-align: center;
}
"""


JS_SEARCH = """
function attachSearch(inputId, listId) {
  const input = document.getElementById(inputId);
  const list = document.getElementById(listId);
  if (!input || !list) return;
  input.addEventListener('input', () => {
    const q = input.value.trim().toLowerCase();
    let visible = 0;
    list.querySelectorAll('.row-item').forEach(row => {
      const txt = row.dataset.searchKey || '';
      const show = !q || txt.indexOf(q) !== -1;
      row.style.display = show ? 'grid' : 'none';
      if (show) visible++;
    });
    const c = document.getElementById('search-count');
    if (c) c.textContent = visible + ' Tests sichtbar';
  });
}
document.addEventListener('DOMContentLoaded', () => {
  attachSearch('test-filter', 'test-list');
});
"""


def _esc(value) -> str:
    return html.escape("" if value is None else str(value))


def _pill(state: str, label: str) -> str:
    return f'<span class="pill {state}">{_esc(label)}</span>'


# ---------------------------------------------------------------------------
# Karten-Builder
# ---------------------------------------------------------------------------
def _release_card(data: dict) -> str:
    decision = data.get("decision", "UNKNOWN")
    state = _decision_status(decision)
    reasons = data.get("reasons") or []
    totals = data.get("totals", {}) or {}
    elapsed = data.get("elapsed_s") or 0
    by_marker = data.get("by_marker", {}) or {}

    must_have = ["members", "roles", "release_gate", "negative",
                 "privacy", "security"]
    checks: list[str] = []
    for m in must_have:
        b = by_marker.get(m, {})
        s = _bucket_status(b)
        label = MARKER_LABEL.get(m, m)
        v = f"{b.get('passed', 0)}/{b.get('count', 0)}"
        checks.append(
            f'<li>{_pill(s, label)} <span class="sub">{_esc(v)}</span></li>')
    reason_html = ""
    if reasons:
        reason_html = (
            "<div class='sub'><strong>Begründung:</strong>"
            + "<ul>"
            + "".join(f"<li>{_esc(r)}</li>" for r in reasons)
            + "</ul></div>"
        )
    return f"""
    <div class="card span-3">
      <div class="title">
        <h3>Release-Reifegrad</h3>
        {_pill(state, decision)}
      </div>
      <div class="value">{_esc(decision)}</div>
      <div class="sub">
        {totals.get('passed', 0)} grün ·
        {totals.get('failed', 0)} failed ·
        {totals.get('error', 0)} error ·
        {totals.get('skipped', 0)} skip ·
        Dauer {elapsed:.1f}s
      </div>
      <ul style="list-style:none;padding:0;margin:6px 0 0 0;
                  display:flex;flex-direction:column;gap:6px;">
        {''.join(checks)}
      </ul>
      {reason_html}
    </div>
    """


def _kpi_card(marker: str, data: dict) -> str:
    by_marker = data.get("by_marker", {}) or {}
    b = by_marker.get(marker, {}) or {}
    label = MARKER_LABEL.get(marker, marker)
    n = b.get("count", 0)
    p = b.get("passed", 0)
    pct = _coverage_pct(b)
    state = _bucket_status(b)
    bar_class = "bar"
    if state == "hold":
        bar_class += " hold"
    if state == "block":
        bar_class += " block"
    return f"""
    <div class="card">
      <div class="title">
        <h3>{_esc(label)}</h3>
        {_pill(state, state.upper())}
      </div>
      <div class="value">{p}/{n}</div>
      <div class="{bar_class}"><div style="width:{pct}%"></div></div>
      <div class="sub">{pct}% bestanden · Dauer {b.get('duration_s', 0):.1f}s</div>
    </div>
    """


def _marker_table(data: dict) -> str:
    by_marker = data.get("by_marker", {}) or {}
    rows: list[str] = []
    for marker, label in MARKER_LABEL.items():
        b = by_marker.get(marker, {}) or {}
        if not b.get("count"):
            continue
        state = _bucket_status(b)
        rows.append(
            "<tr>"
            f"<td>{_pill(state, state.upper())}</td>"
            f"<td>{_esc(label)}</td>"
            f"<td class='num'>{b.get('count', 0)}</td>"
            f"<td class='num'>{b.get('passed', 0)}</td>"
            f"<td class='num'>{b.get('failed', 0)}</td>"
            f"<td class='num'>{b.get('error', 0)}</td>"
            f"<td class='num'>{b.get('skipped', 0)}</td>"
            f"<td class='num'>{b.get('duration_s', 0):.1f}s</td>"
            "</tr>"
        )
    if not rows:
        rows.append("<tr><td colspan='8'>Keine Bereichsstatistik vorhanden.</td></tr>")
    return f"""
    <div class="card span-3">
      <div class="title">
        <h3>Abdeckung nach Konzept-Bereich</h3>
      </div>
      <table>
        <thead><tr>
          <th>Status</th><th>Bereich</th><th>Tests</th>
          <th>passed</th><th>failed</th><th>error</th>
          <th>skipped</th><th>Dauer</th>
        </tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
    """


def _failures_card(records: list[dict]) -> str:
    fails = [r for r in records if r.get("status") in ("failed", "error")]
    if not fails:
        return f"""
        <div class="card span-3">
          <div class="title">
            <h3>Fehlgeschlagene Tests</h3>
            {_pill('go', 'KEINE')}
          </div>
          <div class="sub">Alle Tests grün - kein Eingriff nötig.</div>
        </div>
        """
    blocks: list[str] = []
    for r in fails[:50]:
        blocks.append(
            f"<details class='failure'>"
            f"<summary>{_esc(r.get('id'))}</summary>"
            f"<pre>{_esc((r.get('message') or '')[:4000])}</pre>"
            f"</details>"
        )
    if len(fails) > 50:
        blocks.append(
            f"<div class='sub'>… und {len(fails) - 50} weitere "
            "Fehler (siehe protocol.md)</div>")
    return f"""
    <div class="card span-3">
      <div class="title">
        <h3>Fehlgeschlagene Tests ({len(fails)})</h3>
        {_pill('block', 'BLOCK')}
      </div>
      <div style="display:flex;flex-direction:column;gap:8px;">
        {''.join(blocks)}
      </div>
    </div>
    """


def _test_list(records: list[dict]) -> str:
    rows: list[str] = []
    # nach Status sortiert: fail/error zuerst, dann skipped, dann passed
    order = {"failed": 0, "error": 1, "skipped": 2, "passed": 3, "running": 4}
    sorted_records = sorted(records,
                             key=lambda r: (order.get(r.get("status", ""), 9),
                                              r.get("id", "")))
    for r in sorted_records:
        status = r.get("status", "unknown")
        state = {"passed": "go", "failed": "block", "error": "block",
                 "skipped": "hold", "running": "hold"}.get(status, "unknown")
        rid = r.get("id", "")
        rows.append(
            f"<div class='row-item' "
            f"data-search-key='{_esc(rid.lower())} {_esc(status)}'>"
            f"<div class='col-status'>{_pill(state, status)}</div>"
            f"<div class='col-name'>{_esc(rid)}</div>"
            f"<div class='col-time'>{r.get('time_s', 0):.3f}s</div>"
            f"</div>"
        )
    return f"""
    <div class="card span-3">
      <div class="title">
        <h3>Vollständige Test-Liste</h3>
        <span class="sub" id="search-count">{len(records)} Tests sichtbar</span>
      </div>
      <div class="searchbar">
        <input id="test-filter" type="search"
               placeholder="Filter (Test-ID oder Status, z. B. 'privacy' oder 'failed')…">
      </div>
      <div class="list" id="test-list">
        {''.join(rows)}
      </div>
    </div>
    """


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------
def render_dashboard(data: dict, source_path: Path) -> str:
    records = data.get("records") or []
    generated = data.get("generated_at") \
        or dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    by_marker = data.get("by_marker", {}) or {}

    kpi_markers = [m for m in MARKER_LABEL if m in by_marker]
    kpi_html = "".join(_kpi_card(m, data) for m in kpi_markers)

    return f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Release- & Compliance-Center · {_esc(generated)}</title>
  <style>{CSS}</style>
</head>
<body>
  <header>
    <div class="logo">QA / Release / Compliance · Cockpit</div>
    <div class="meta">
      generiert: {_esc(generated)} ·
      host: {_esc(platform.node())} ·
      quelle: {_esc(source_path.name)}
    </div>
  </header>
  <main>
    <section class="row">
      {_release_card(data)}
    </section>
    <section>
      <div class="kpi-grid">
        {kpi_html}
      </div>
    </section>
    <section class="row">
      {_marker_table(data)}
    </section>
    <section class="row">
      {_failures_card(records)}
    </section>
    <section class="row">
      {_test_list(records)}
    </section>
  </main>
  <footer>
    Statisches Dashboard - generiert von <code>tools/dashboard.py</code>.
    Datenquelle: <code>{_esc(source_path)}</code>.
    Layout-/Architektur-Konzept: <code>UI_CONCEPT.md</code>.
  </footer>
  <script>{JS_SEARCH}</script>
</body>
</html>"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="HTML-Dashboard aus protocol.json erzeugen.")
    parser.add_argument("--json", default=str(DEFAULT_JSON),
                        help="Pfad zur protocol.json (Default: tests/concept/reports/protocol.json)")
    parser.add_argument("--out", default=str(DEFAULT_HTML),
                        help="Zielpfad fuer die HTML-Ausgabe")
    args = parser.parse_args(argv)
    src = Path(args.json)
    if not src.is_file():
        print(f"FEHLER: {src} nicht gefunden. Zuerst "
              "'python -m tools.test_protocol' ausfuehren.",
              file=sys.stderr)
        return 2
    data = json.loads(src.read_text(encoding="utf-8"))
    html_text = render_dashboard(data, src)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html_text, encoding="utf-8")
    print(f"Dashboard geschrieben: {out}")
    print(f"  Quelle: {src}")
    print(f"  Status: {data.get('decision')} · "
          f"Tests: {data.get('totals', {}).get('count')} · "
          f"groesse: {os.path.getsize(out)} Bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
