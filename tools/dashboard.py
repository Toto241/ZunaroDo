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
    "playstore":     "Play-Store-Sync",
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

nav.toc {
  display: flex; gap: 8px; flex-wrap: wrap;
  padding: 10px 24px; background: var(--surface-muted);
  border-bottom: 1px solid var(--border);
  font-size: 13px; font-weight: 500;
  position: sticky; top: 0; z-index: 10;
}

/* ---- Build-Center ---- */
.build-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 14px;
}
.build-card {
  display: flex; flex-direction: column; gap: 10px;
  padding: 16px; border: 1px solid var(--border);
  border-radius: 10px; background: var(--surface);
}
.build-card.ready  { border-color: var(--go); }
.build-card.notyet { border-color: var(--hold); }
.build-card .head {
  display: flex; align-items: center; justify-content: space-between;
}
.build-card .head .icon { font-size: 24px; }
.build-card .head h4 {
  margin: 0; font-size: 16px; font-weight: 600;
  flex: 1; padding: 0 8px;
}
.build-card .tool { font-size: 12px; color: var(--text-muted); }
.build-card .cmdbox {
  display: flex; align-items: stretch; gap: 0;
  border: 1px solid var(--border); border-radius: 6px;
  background: var(--surface-muted); overflow: hidden;
}
.build-card .cmdbox code {
  flex: 1; padding: 8px 10px; background: transparent;
  border: none; font-family: var(--mono); font-size: 12px;
  color: var(--text); overflow-x: auto; white-space: nowrap;
}
.build-card .cmdbox button {
  border: none; border-left: 1px solid var(--border);
  background: var(--surface); color: var(--primary); font-weight: 600;
  padding: 0 14px; cursor: pointer; font-size: 12px;
}
.build-card .cmdbox button:hover { background: var(--bg); }
.build-card .actions {
  display: flex; gap: 8px; flex-wrap: wrap;
}
.build-card .actions a, .build-card .actions button {
  display: inline-block; padding: 6px 12px;
  border: 1px solid var(--border); border-radius: 6px;
  background: var(--surface); color: var(--primary);
  text-decoration: none; font-size: 12px; font-weight: 500;
  cursor: pointer;
}
.build-card .actions a.primary, .build-card .actions button.primary {
  background: var(--primary); color: #ffffff; border-color: var(--primary);
}
.build-card .actions a:hover { background: var(--surface-muted); }
.build-card details { font-size: 12px; }
.build-card details summary { cursor: pointer; color: var(--text-muted); }
.build-card details ul { padding-left: 18px; margin: 6px 0; }
.build-card .artifact {
  font-size: 12px; padding: 8px 10px; border-radius: 6px;
  background: var(--surface-muted); border: 1px dashed var(--border);
}
.build-card .artifact.none { color: var(--text-muted); }
.build-card .artifact .meta {
  display: flex; gap: 12px; flex-wrap: wrap;
  font-family: var(--mono); color: var(--text-muted);
}
nav.toc a {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 4px 10px; border-radius: 6px;
  color: var(--text-muted); text-decoration: none;
  border: 1px solid transparent;
}
nav.toc a:hover { color: var(--primary); background: var(--surface);
                  border-color: var(--border); }

.artifacts-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 12px;
}
.artifact-link {
  display: flex; flex-direction: column; gap: 4px;
  padding: 14px; border: 1px solid var(--border);
  border-radius: 8px; background: var(--surface);
  color: var(--text); text-decoration: none;
  transition: transform 120ms ease, border-color 120ms ease;
}
.artifact-link:hover { transform: translateY(-1px);
                        border-color: var(--primary); }
.artifact-link .icon { font-size: 18px; line-height: 1; }
.artifact-link .name { font-weight: 600; font-size: 14px; }
.artifact-link .desc { font-size: 12px; color: var(--text-muted); }
.artifact-link.missing { opacity: 0.55; pointer-events: none; }
.artifact-link.missing .desc::after {
  content: " (nicht gefunden)"; color: var(--block);
}

/* ---- Aufklappbare Testzeilen ---- */
details.test-item { border-bottom: 1px solid var(--border); }
details.test-item:last-child { border-bottom: none; }
details.test-item > summary {
  display: grid; grid-template-columns: 92px 1fr auto 70px;
  align-items: center; gap: 12px; padding: 8px 12px;
  cursor: pointer; list-style: none; font-family: var(--mono);
  font-size: 12px;
}
details.test-item > summary::-webkit-details-marker { display: none; }
details.test-item > summary:hover { background: var(--surface-muted); }
details.test-item[open] > summary { background: var(--surface-muted); }
.test-item .t-id { color: var(--text); word-break: break-all; }
.test-item .t-time { color: var(--text-muted); text-align: right;
                     font-variant-numeric: tabular-nums; }
.test-item .t-reqs { display: flex; gap: 4px; flex-wrap: wrap; justify-content: flex-end; }
.req-tag {
  font-family: var(--mono); font-size: 10px; font-weight: 600;
  padding: 1px 6px; border-radius: 5px; background: var(--surface-muted);
  color: var(--text-muted); border: 1px solid var(--border);
}
.test-body {
  padding: 4px 14px 14px 14px; background: var(--bg);
  display: flex; flex-direction: column; gap: 8px;
}
.test-body .t-meta {
  font-family: var(--mono); font-size: 12px; color: var(--text-muted);
  display: flex; gap: 14px; flex-wrap: wrap;
}
.test-body .t-doc {
  font-size: 13px; line-height: 1.5; color: var(--text);
  border-left: 3px solid var(--primary); padding: 4px 0 4px 10px;
  white-space: pre-wrap;
}
.test-body .t-fail {
  background: var(--block-bg); border: 1px solid var(--block);
  border-radius: 6px; padding: 8px 10px; color: var(--block);
  font-family: var(--mono); font-size: 12px; white-space: pre-wrap;
  overflow-x: auto;
}
.test-body pre.t-src {
  margin: 0; padding: 12px; background: var(--surface);
  border: 1px solid var(--border); border-radius: 6px;
  font-family: var(--mono); font-size: 12px; line-height: 1.45;
  overflow-x: auto; white-space: pre; color: var(--text);
}
.test-body .t-src-missing { font-size: 12px; color: var(--text-muted); }

/* ---- Anforderungs-Abdeckungsmatrix ---- */
.req-row td.req-id { font-family: var(--mono); font-weight: 700; }
.req-row td.req-label { color: var(--text); }
.req-row.gap td { background: var(--block-bg); }
.req-row.thin td { background: var(--hold-bg); }
"""


JS_COPY = """
function copyText(btn, text) {
  const ok = (msg) => {
    const orig = btn.textContent;
    btn.textContent = msg;
    setTimeout(() => { btn.textContent = orig; }, 1200);
  };
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(text).then(() => ok('Kopiert'),
                                              () => ok('Fehlgeschlagen'));
  } else {
    const ta = document.createElement('textarea');
    ta.value = text; document.body.appendChild(ta); ta.select();
    try { document.execCommand('copy'); ok('Kopiert'); }
    catch (e) { ok('Fehlgeschlagen'); }
    document.body.removeChild(ta);
  }
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
    list.querySelectorAll('.test-item').forEach(row => {
      const txt = row.dataset.searchKey || '';
      const show = !q || txt.indexOf(q) !== -1;
      row.style.display = show ? 'block' : 'none';
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


def _render_companion_docs(source_path: Path) -> dict[str, Path]:
    """Konvertiert die Markdown-Dokus in HTML neben das Dashboard.

    Liefert Mapping `md-Quellname -> erzeugte HTML-Datei`, sodass die
    Artefakt-Karten direkt auf die gerenderte Variante verlinken
    koennen. Im Browser zeigt das einen formatierten Lesetext statt
    rohem Markdown.
    """
    from tools.md_to_html import render_doc

    base = source_path.parent                       # tests/concept/reports
    repo = base.parent.parent.parent
    targets = {
        "TESTING.md":     repo / "TESTING.md",
        "UI_CONCEPT.md":  repo / "UI_CONCEPT.md",
        "PLAYSTORE.md":   repo / "PLAYSTORE.md",
        "protocol.md":    base / "protocol.md",
    }
    out_map: dict[str, Path] = {}
    for name, md_path in targets.items():
        if not md_path.is_file():
            continue
        html_out = base / md_path.with_suffix(".html").name
        back = "dashboard.html"
        try:
            content = render_doc(
                title=md_path.stem, markdown_text=md_path.read_text(
                    encoding="utf-8", errors="replace"),
                back_link=back,
                back_label="← zurueck zum Dashboard")
        except Exception:
            continue
        html_out.write_text(content, encoding="utf-8")
        out_map[name] = html_out
    return out_map


def _artifact_card(source_path: Path,
                    rendered_docs: dict[str, Path]) -> str:
    """Liste der bekannten Begleit-Artefakte mit klickbaren Links.

    Pfade sind relativ zum Speicherort der dashboard.html. Wenn eine
    HTML-Renderung der Markdown-Quelle existiert (siehe
    _render_companion_docs), wird ZUERST darauf verlinkt - sonst auf
    die Roh-Quelle.
    """
    base = source_path.parent
    repo = base.parent.parent.parent
    items = [
        ("Test-Konzept",
         "TESTING.md", repo / "TESTING.md",
         "📘",
         "Test- und Compliance-Konzept (Teil I + II, ~3000 Zeilen)"),
        ("UI-/Cockpit-Konzept",
         "UI_CONCEPT.md", repo / "UI_CONCEPT.md",
         "🧭",
         "Admin-Panel-Architektur, Datenmodelle, Workflows"),
        ("Play-Store-Anleitung",
         "PLAYSTORE.md", repo / "PLAYSTORE.md",
         "🚀",
         "Schritt-fuer-Schritt Veroeffentlichung in der Play Console"),
        ("Audit-Protokoll",
         "protocol.md", base / "protocol.md",
         "📑",
         "Markdown-Auditbericht aller Tests des letzten Laufs"),
        ("Maschinen-Protokoll",
         None, base / "protocol.json",
         "🧾",
         "JSON-Quelle fuer dieses Dashboard und CI-Integrationen"),
        ("JUnit-XML",
         None, base / "junit.xml",
         "🧪",
         "Roher pytest-Bericht fuer CI-Tools (GitHub Actions etc.)"),
        ("Pairwise-Matrix",
         None, base / "pairwise-matrix.tsv",
         "🧮",
         "Kombinatorische Testmatrix (Anhang C, 196 Faelle)"),
        ("Protokoll-Generator",
         None, repo / "tools" / "test_protocol.py",
         "⚙️",
         "Skript, das aus JUnit-XML dieses Protokoll erzeugt"),
        ("Dashboard-Generator",
         None, repo / "tools" / "dashboard.py",
         "🖥️",
         "Dieses Dashboard - reproduzierbar generiert"),
    ]

    cells: list[str] = []
    for label, md_name, raw_target, icon, desc in items:
        # Bevorzugt die gerenderte HTML-Datei verlinken (lesbar im Browser)
        rendered = rendered_docs.get(md_name) if md_name else None
        target = rendered if rendered is not None else raw_target
        try:
            rel = os.path.relpath(target, start=base).replace(os.sep, "/")
        except ValueError:
            rel = str(target)
        exists = target.is_file()
        klass = "artifact-link" + ("" if exists else " missing")
        cells.append(
            f"<a class='{klass}' href='{_esc(rel)}'>"
            f"<span class='icon'>{icon}</span>"
            f"<span class='name'>{_esc(label)}</span>"
            f"<span class='desc'>{_esc(desc)}</span>"
            f"</a>"
        )
    return f"""
    <div class="card span-3" id="artefakte">
      <div class="title">
        <h3>Artefakte &amp; Dokumente</h3>
        <span class="sub">Klick oeffnet die Datei direkt im Browser</span>
      </div>
      <div class="artifacts-grid">
        {''.join(cells)}
      </div>
    </div>
    """


def _build_center(source_path: Path) -> str:
    """Liste der Build-Plattformen Android/iOS/PC.

    Liest tools/build_status.py und rendert pro Plattform eine Karte
    mit Status, Befehl, kopierbarem Code und (falls vorhanden) Link
    zum Build-Skript.
    """
    try:
        from tools.build_status import gather, to_dict
        items = to_dict(gather())
    except Exception as exc:                              # noqa: BLE001
        return (f"<div class='card span-3'>"
                f"<h3>Build-Center nicht verfuegbar</h3>"
                f"<p class='sub'>{_esc(exc)}</p></div>")

    base = source_path.parent
    repo = base.parent.parent.parent
    cards: list[str] = []
    for it in items:
        ready = "ready" if it["available"] else "notyet"
        state = "go" if it["available"] else "hold"
        status_label = "bereit" if it["available"] else "nicht verfuegbar"
        # Skript-Link (relative auf reports/-Verzeichnis bezogen)
        script_html = ""
        if it.get("script_path"):
            try:
                full = repo / it["script_path"]
                rel = os.path.relpath(full, start=base).replace(os.sep, "/")
                primary = "primary" if it["available"] else ""
                script_html = (
                    f"<a class='{primary}' href='{_esc(rel)}'>"
                    f"Build-Skript oeffnen</a>")
            except ValueError:
                pass
        # Artefakt-Block
        art = it.get("artifact")
        if art:
            size_kb = (art.get("size_bytes") or 0) / 1024
            unit = "KB"
            if size_kb > 1024:
                size_kb /= 1024
                unit = "MB"
            art_html = (
                "<div class='artifact'>"
                f"<div><strong>Letztes Artefakt:</strong> "
                f"<code>{_esc(art['path'])}</code></div>"
                f"<div class='meta'>"
                f"<span>{size_kb:.1f} {unit}</span>"
                f"<span>{_esc(art.get('mtime_iso', ''))}</span>"
                + (f"<span>v{_esc(art.get('version_guess', ''))}</span>"
                    if art.get('version_guess') else "")
                + "</div></div>"
            )
        else:
            art_html = ("<div class='artifact none'>"
                         "noch kein Build-Artefakt vorhanden</div>")
        # Vorbedingungen als <details>
        prereqs_html = "".join(f"<li>{_esc(p)}</li>"
                                for p in it.get("prereqs") or [])
        # Befehl + Copy-Button
        cmd = it.get("command") or ""
        # JS-String-Escape
        js_cmd = (cmd.replace("\\", "\\\\").replace("'", "\\'")
                       .replace("\n", "\\n"))
        cards.append(f"""
        <div class='build-card {ready}'>
          <div class='head'>
            <span class='icon'>{_esc(it.get('icon') or '⚙')}</span>
            <h4>{_esc(it['label'])}</h4>
            {_pill(state, status_label)}
          </div>
          <div class='tool'>Werkzeug: {_esc(it['tool'])}</div>
          <div class='cmdbox'>
            <code>{_esc(cmd)}</code>
            <button onclick="copyText(this, '{js_cmd}')">Copy</button>
          </div>
          {art_html}
          <div class='actions'>
            {script_html}
          </div>
          <details>
            <summary>Voraussetzungen + Hinweise</summary>
            <ul>{prereqs_html}</ul>
            <div class='sub'>{_esc(it.get('notes', ''))}</div>
          </details>
        </div>
        """)
    return f"""
    <div class='card span-3' id='build'>
      <div class='title'>
        <h3>Build-Center  -  Android / iOS / PC</h3>
        <span class='sub'>App fuer jede Zielplattform erzeugen</span>
      </div>
      <div class='build-grid'>
        {''.join(cards)}
      </div>
    </div>
    """


def _req_tags_html(reqs: list[str]) -> str:
    return "".join(f"<span class='req-tag' title='{_esc(REQ_TITLE.get(rid, rid))}'>"
                   f"{_esc(rid)}</span>" for rid in reqs)


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
        reqs = r.get("requirements", []) or []
        file_ = r.get("file", "")
        lineno = r.get("lineno", 0)
        doc = r.get("doc", "")
        source = r.get("source", "")
        message = r.get("message", "")
        module = r.get("module", "")

        # Suchschluessel enthaelt ID, Status, Anforderungen, Modul
        search_key = " ".join([rid.lower(), status,
                               " ".join(reqs).lower(), module.lower()])

        meta_bits = []
        if file_:
            loc = f"{file_}:{lineno}" if lineno else file_
            meta_bits.append(f"<span>📄 {_esc(loc)}</span>")
        if module:
            meta_bits.append(f"<span>🧩 {_esc(module)}</span>")
        if reqs:
            meta_bits.append("<span>🎯 " + ", ".join(
                _esc(f"{rid} {REQ_TITLE.get(rid, '')}") for rid in reqs)
                + "</span>")
        meta_html = ("<div class='t-meta'>" + "".join(meta_bits) + "</div>"
                     if meta_bits else "")
        doc_html = (f"<div class='t-doc'>{_esc(doc)}</div>" if doc else "")
        fail_html = (f"<div class='t-fail'>{_esc(message[:4000])}</div>"
                     if message and status in ("failed", "error") else "")
        if source:
            src_html = f"<pre class='t-src'>{_esc(source)}</pre>"
        else:
            src_html = ("<div class='t-src-missing'>Quelltext nicht "
                        "aufloesbar (z. B. dynamisch erzeugter Test).</div>")

        rows.append(
            f"<details class='test-item' data-search-key='{_esc(search_key)}'>"
            f"<summary>"
            f"<span class='col-status'>{_pill(state, status)}</span>"
            f"<span class='t-id'>{_esc(rid)}</span>"
            f"<span class='t-reqs'>{_req_tags_html(reqs)}</span>"
            f"<span class='t-time'>{r.get('time_s', 0):.3f}s</span>"
            f"</summary>"
            f"<div class='test-body'>{meta_html}{doc_html}{fail_html}{src_html}</div>"
            f"</details>"
        )
    return f"""
    <div class="card span-3">
      <div class="title">
        <h3>Vollständige Test-Liste — Zeile anklicken zeigt den Testfall</h3>
        <span class="sub" id="search-count">{len(records)} Tests sichtbar</span>
      </div>
      <div class="searchbar">
        <input id="test-filter" type="search"
               placeholder="Filter (Test-ID, Status, Anforderung z. B. 'R5', oder Modul)…">
      </div>
      <div class="list" id="test-list">
        {''.join(rows)}
      </div>
    </div>
    """


REQ_TITLE: dict[str, str] = {}


def _requirement_matrix(data: dict) -> str:
    """Abdeckungsmatrix Anforderung (R1..R10) -> Tests, mit Lueckenmarkierung."""
    reqs = data.get("requirements", {}) or {}
    by_req = data.get("by_requirement", {}) or {}
    REQ_TITLE.update(reqs)
    rows: list[str] = []
    for rid in reqs:
        b = by_req.get(rid, {}) or {}
        n = b.get("count", 0)
        p = b.get("passed", 0)
        f = b.get("failed", 0)
        e = b.get("error", 0)
        sk = b.get("skipped", 0)
        files = b.get("files", []) or []
        if f or e:
            state, klass = "block", "req-row gap"
        elif n == 0:
            state, klass = "unknown", "req-row gap"
        elif n < 5:
            state, klass = "hold", "req-row thin"
        else:
            state, klass = "go", "req-row"
        rows.append(
            f"<tr class='{klass}'>"
            f"<td class='req-id'>{_esc(rid)}</td>"
            f"<td class='req-label'>{_esc(reqs.get(rid, ''))}</td>"
            f"<td>{_pill(state, state.upper())}</td>"
            f"<td class='num'>{n}</td>"
            f"<td class='num'>{p}</td>"
            f"<td class='num'>{f}</td>"
            f"<td class='num'>{e}</td>"
            f"<td class='num'>{sk}</td>"
            f"<td class='id'>{_esc(', '.join(files)) if files else '—'}</td>"
            "</tr>"
        )
    return f"""
    <div class="card span-3" id="anforderungen">
      <div class="title">
        <h3>Anforderungs-Abdeckung (Traceability R1–R10)</h3>
        <span class="sub">Rot = Lücke/Fehlschlag · Gelb = dünn (&lt;5 Tests)</span>
      </div>
      <table>
        <thead><tr>
          <th>ID</th><th>Anforderung</th><th>Status</th><th>Tests</th>
          <th>passed</th><th>failed</th><th>error</th><th>skipped</th>
          <th>Test-Dateien</th>
        </tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
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
    # Anforderungs-Titel global verfuegbar machen (fuer Tags in der Testliste)
    REQ_TITLE.update(data.get("requirements", {}) or {})

    kpi_markers = [m for m in MARKER_LABEL if m in by_marker]
    kpi_html = "".join(_kpi_card(m, data) for m in kpi_markers)

    decision = data.get("decision", "UNKNOWN")
    state = _decision_status(decision)
    totals = data.get("totals", {}) or {}

    # Begleit-Dokumente als HTML neben das Dashboard schreiben, damit die
    # Artefakt-Karten auf gerenderte Seiten verlinken statt auf rohes Markdown
    rendered_docs = _render_companion_docs(source_path)

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
    <div style="display:flex;align-items:center;gap:12px;">
      {_pill(state, decision)}
      <span class="sub" style="color:var(--text-muted);font-size:13px;">
        {totals.get('passed', 0)}/{totals.get('count', 0)} grün
      </span>
    </div>
    <div class="meta">
      generiert: {_esc(generated)} ·
      host: {_esc(platform.node())}
    </div>
  </header>
  <nav class="toc">
    <a href="#uebersicht">Übersicht</a>
    <a href="#artefakte">Artefakte</a>
    <a href="#build">Build</a>
    <a href="#kpis">KPIs</a>
    <a href="#anforderungen">Anforderungen</a>
    <a href="#bereiche">Bereiche</a>
    <a href="#fehler">Fehler</a>
    <a href="#tests">Test-Liste</a>
  </nav>
  <main>
    <section id="uebersicht" class="row">
      {_release_card(data)}
    </section>
    <section id="artefakte" class="row">
      {_artifact_card(source_path, rendered_docs)}
    </section>
    <section id="build" class="row">
      {_build_center(source_path)}
    </section>
    <section id="kpis">
      <div class="kpi-grid">
        {kpi_html}
      </div>
    </section>
    <section id="anforderungen" class="row">
      {_requirement_matrix(data)}
    </section>
    <section id="bereiche" class="row">
      {_marker_table(data)}
    </section>
    <section id="fehler" class="row">
      {_failures_card(records)}
    </section>
    <section id="tests" class="row">
      {_test_list(records)}
    </section>
  </main>
  <footer>
    Statisches Dashboard - generiert von <code>tools/dashboard.py</code>.
    Datenquelle: <code>{_esc(source_path)}</code>.
    Layout-/Architektur-Konzept: <code>UI_CONCEPT.md</code>.
  </footer>
  <script>{JS_COPY}{JS_SEARCH}</script>
</body>
</html>"""


def _index_build_center() -> str:
    """Build-Center fuer die index.html.

    Wie `_build_center`, aber Pfade sind relativ zum Projekt-Root,
    nicht zu tests/concept/reports/.
    """
    try:
        from tools.build_status import gather, to_dict
        items = to_dict(gather())
    except Exception as exc:                            # noqa: BLE001
        return (f"<div class='card span-3'><h3>Build-Center"
                f" nicht verfuegbar</h3>"
                f"<p class='sub'>{_esc(exc)}</p></div>")

    cards: list[str] = []
    for it in items:
        ready = "ready" if it["available"] else "notyet"
        state = "go" if it["available"] else "hold"
        status_label = "bereit" if it["available"] else "nicht verfuegbar"
        script_html = ""
        if it.get("script_path"):
            primary = "primary" if it["available"] else ""
            script_html = (
                f"<a class='{primary}' href='{_esc(it['script_path'])}'>"
                f"Build-Skript oeffnen</a>")
        art = it.get("artifact")
        if art:
            size_kb = (art.get("size_bytes") or 0) / 1024
            unit = "KB"
            if size_kb > 1024:
                size_kb /= 1024
                unit = "MB"
            art_html = (
                "<div class='artifact'>"
                f"<div><strong>Letztes Artefakt:</strong> "
                f"<code>{_esc(art['path'])}</code></div>"
                f"<div class='meta'>"
                f"<span>{size_kb:.1f} {unit}</span>"
                f"<span>{_esc(art.get('mtime_iso', ''))}</span>"
                + (f"<span>v{_esc(art.get('version_guess', ''))}</span>"
                    if art.get('version_guess') else "")
                + "</div></div>")
        else:
            art_html = ("<div class='artifact none'>"
                         "noch kein Build-Artefakt vorhanden</div>")
        prereqs_html = "".join(f"<li>{_esc(p)}</li>"
                                for p in it.get("prereqs") or [])
        cmd = it.get("command") or ""
        js_cmd = (cmd.replace("\\", "\\\\").replace("'", "\\'")
                       .replace("\n", "\\n"))
        cards.append(f"""
        <div class='build-card {ready}'>
          <div class='head'>
            <span class='icon'>{_esc(it.get('icon') or '⚙')}</span>
            <h4>{_esc(it['label'])}</h4>
            {_pill(state, status_label)}
          </div>
          <div class='tool'>Werkzeug: {_esc(it['tool'])}</div>
          <div class='cmdbox'>
            <code>{_esc(cmd)}</code>
            <button onclick="copyText(this, '{js_cmd}')">Copy</button>
          </div>
          {art_html}
          <div class='actions'>{script_html}</div>
          <details>
            <summary>Voraussetzungen + Hinweise</summary>
            <ul>{prereqs_html}</ul>
            <div class='sub'>{_esc(it.get('notes', ''))}</div>
          </details>
        </div>
        """)
    return f"""
    <div class='card span-3' id='build'>
      <div class='title'>
        <h3>Build-Center  -  Android / iOS / PC</h3>
        <span class='sub'>App fuer jede Zielplattform erzeugen</span>
      </div>
      <div class='build-grid'>{''.join(cards)}</div>
    </div>
    """


def _index_landing_html(data: dict, dashboard_rel: str) -> str:
    """Eigenstaendige index.html im Projekt-Root - der eigentliche
    Einstiegspunkt. Zeigt einen kurzen Status-Hub und linkt aufs
    Dashboard sowie die wichtigsten Doku-HTMLs."""
    decision = data.get("decision", "UNKNOWN")
    state = _decision_status(decision)
    totals = data.get("totals", {}) or {}
    by_marker = data.get("by_marker", {}) or {}
    base = REPO_ROOT
    rendered_base = REPO_ROOT / "tests" / "concept" / "reports"

    # Quick-Links (relativ zum Projekt-Root)
    quick = [
        ("📊  Dashboard oeffnen",
         dashboard_rel,
         "Live-Test-Resultate, Bereichsstatistiken, Test-Liste"),
        ("📘  Test-Konzept (HTML)",
         "tests/concept/reports/TESTING.html",
         "Test- und Compliance-Konzept (Teil I + II)"),
        ("🧭  UI-/Cockpit-Konzept (HTML)",
         "tests/concept/reports/UI_CONCEPT.html",
         "Admin-Panel-Architektur, Datenmodelle, Workflows"),
        ("🚀  Play-Store-Anleitung (HTML)",
         "tests/concept/reports/PLAYSTORE.html",
         "Schritt-fuer-Schritt Veroeffentlichung"),
        ("📑  Audit-Protokoll (HTML)",
         "tests/concept/reports/protocol.html",
         "Vollstaendiger Markdown-Auditbericht aller Tests"),
    ]
    qcells: list[str] = []
    for name, href, desc in quick:
        target = base / href
        exists = target.is_file()
        klass = "artifact-link" + ("" if exists else " missing")
        qcells.append(
            f"<a class='{klass}' href='{_esc(href)}'>"
            f"<span class='name' style='font-size:15px;'>{_esc(name)}</span>"
            f"<span class='desc'>{_esc(desc)}</span>"
            f"</a>"
        )

    # KPI-Kuerzeln im Hub
    kpi_quick: list[str] = []
    for marker in ("members", "roles", "combinatorics", "property",
                    "negative", "privacy", "security", "release_gate"):
        b = by_marker.get(marker, {}) or {}
        if not b.get("count"):
            continue
        s = _bucket_status(b)
        kpi_quick.append(
            f"<div class='card' style='min-width:0;'>"
            f"<div class='title'>"
            f"<h3>{_esc(MARKER_LABEL.get(marker, marker))}</h3>"
            f"{_pill(s, s.upper())}</div>"
            f"<div class='value'>{b.get('passed', 0)}/{b.get('count', 0)}</div>"
            f"<div class='sub'>Dauer {b.get('duration_s', 0):.1f}s</div>"
            f"</div>"
        )

    return f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Zunarodo · QA- und Release-Center · Uebersicht</title>
  <style>{CSS}</style>
</head>
<body>
  <header>
    <div class="logo">Zunarodo · QA- und Release-Center</div>
    <div style="display:flex;align-items:center;gap:12px;">
      {_pill(state, decision)}
      <span class="sub" style="font-size:13px;color:var(--text-muted);">
        {totals.get('passed', 0)}/{totals.get('count', 0)} Tests gruen
      </span>
    </div>
    <div class="meta">Einstiegspunkt - waehle ein Modul rechts.</div>
  </header>

  <main>
    <section class="row">
      <div class="card span-3">
        <div class="title">
          <h3>Schnellzugriffe</h3>
          <span class="sub">Klick oeffnet die Seite direkt im Browser</span>
        </div>
        <div class="artifacts-grid">
          {''.join(qcells)}
        </div>
      </div>
    </section>

    <section>
      <div class="kpi-grid">
        {''.join(kpi_quick)}
      </div>
    </section>

    <section class="row">
      {_index_build_center()}
    </section>

    <section class="row">
      <div class="card span-3">
        <div class="title">
          <h3>Was ist das hier?</h3>
        </div>
        <p style="margin:0;font-size:14px;line-height:1.6;color:var(--text);">
          Diese Seite ist der zentrale Einstiegspunkt. Der
          <a href="{_esc(dashboard_rel)}">Test-Dashboard</a> zeigt die
          live-aggregierten Resultate der gesamten Test-Suite
          (Mitglieder, Rollen, Pairwise, Property, Negative,
          Datenschutz, Security, Release-Gate). Die drei Konzept-
          Dokumente
          <a href="tests/concept/reports/TESTING.html">TESTING</a>,
          <a href="tests/concept/reports/UI_CONCEPT.html">UI_CONCEPT</a>
          und
          <a href="tests/concept/reports/PLAYSTORE.html">PLAYSTORE</a>
          sind direkt im Browser lesbar gerendert.
        </p>
        <p style="margin:0;font-size:13px;color:var(--text-muted);">
          Neugenerierung jederzeit:
          <code>python -m tools.test_protocol --all</code> +
          <code>python -m tools.dashboard</code>.
        </p>
      </div>
    </section>
  </main>

  <footer>
    Generiert von <code>tools/dashboard.py</code>.
    Letzter Lauf: {_esc(data.get('generated_at') or '—')}.
  </footer>
  <script>{JS_COPY}</script>
</body>
</html>"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="HTML-Dashboard aus protocol.json erzeugen.")
    parser.add_argument("--json", default=str(DEFAULT_JSON),
                        help="Pfad zur protocol.json (Default: tests/concept/reports/protocol.json)")
    parser.add_argument("--out", default=str(DEFAULT_HTML),
                        help="Zielpfad fuer die HTML-Ausgabe")
    parser.add_argument("--no-index", action="store_true",
                        help="Kein index.html im Projekt-Root erzeugen")
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

    # Projekt-Root-index.html als echter Einstiegspunkt
    if not args.no_index:
        index_path = REPO_ROOT / "index.html"
        try:
            dashboard_rel = os.path.relpath(out, start=REPO_ROOT).replace(
                os.sep, "/")
        except ValueError:
            dashboard_rel = "tests/concept/reports/dashboard.html"
        index_path.write_text(
            _index_landing_html(data, dashboard_rel),
            encoding="utf-8")
        print(f"Einstiegspunkt:        {index_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
