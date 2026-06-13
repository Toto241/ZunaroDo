"""
Test-Protokoll-Generator.

Fuehrt die komplette Konzept-Test-Suite (Marker 'concept') aus, liest
das von pytest erzeugte JUnit-XML, aggregiert die Ergebnisse pro
Konzept-Bereich (Anhang A-K) und schreibt zwei Artefakte:

  tests/concept/reports/junit.xml
  tests/concept/reports/protocol.md
  tests/concept/reports/protocol.json

Aufruf:

  python -m tools.test_protocol                  # Konzept-Tests
  python -m tools.test_protocol --all            # gesamte tests/-Suite
  python -m tools.test_protocol --marker roles   # nur roles-Marker

Exit-Code = 0 bei vollstaendig gruen + erfuelltem Release-Gate, sonst 1.
"""
from __future__ import annotations

import argparse
import importlib
import inspect
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# ---------------------------------------------------------------------------
# Anforderungs-Katalog (Traceability Anforderung <-> Test)
# ---------------------------------------------------------------------------
# Leitet sich aus der Modulbeschreibung der App ab. Jeder Test wird ueber
# seine Datei einem oder mehreren Anforderungsbereichen zugeordnet, sodass
# das Dashboard eine Abdeckungsmatrix und Luecken anzeigen kann.
REQUIREMENTS = {
    "R1":  "Aufgaben- & Tagesplanung (Familie, Rotation, Catch-Up, Kalender)",
    "R2":  "Erinnerungen & Benachrichtigungen (Scheduler, Persistenz, Systemzeit)",
    "R3":  "Kategorien & Prioritaeten (Filter/Sortierung)",
    "R4":  "Suche & Filter (Volltextsuche, grosse Datenmengen)",
    "R5":  "Datenpersistenz & Mehrgeraete-Sync (FileSync/HttpSync, Konflikt, Re-Entry, TLS/Token)",
    "R6":  "Import/Export (CSV, ICS, VCF, PDF)",
    "R7":  "Datenschutz & Sicherheit (Policy, Data-Safety, Consent, SQLCipher, Loeschung)",
    "R8":  "Stabilitaet & Tests (Smoke, Integration, GUI-Boot, Property/Fuzz, Negativ)",
    "R9":  "Play-Store-Release (Check, Store-Listing, Release-Gate, Build/AAB)",
    "R10": "QA / Testuebersicht (Protokoll- & Dashboard-Generatoren)",
}

# Test-Datei (stem) -> Liste von Anforderungs-IDs
FILE_REQUIREMENTS = {
    # --- tests/ (Funktions- und Integrationsebene) ---
    "test_smoke":             ["R1", "R2", "R4", "R5", "R6", "R7", "R8"],
    "test_search_filters":    ["R4"],
    "test_priority_category": ["R3"],
    "test_overview":          ["R1"],
    "test_notifications_permission": ["R2", "R9"],
    "test_compliance_gates":  ["R7", "R9"],
    "test_import_robustness": ["R6"],
    "test_sync_conflict":     ["R5"],
    "test_sync_threadsafety": ["R5"],
    "test_calendar_birthday": ["R1", "R8"],
    "test_persistence_robustness": ["R1", "R5", "R8"],
    "test_mobile_screen_capabilities": ["R1", "R3", "R4"],
    "test_requirements_coverage": ["R8", "R10"],
    "test_ai_studio_contracts": ["R8", "R10"],
    "test_gui_boot_smoke":    ["R8"],
    "test_mobile_boot_smoke": ["R8"],
    "test_presenters":        ["R1", "R3", "R4", "R8"],
    "test_headless_app":      ["R8"],
    "test_profiles":          ["R5", "R7"],
    "test_tls_certs":         ["R5", "R7"],
    "test_ui_text":           ["R8"],
    "test_scheduler_reminders": ["R2"],
    "test_integration":       ["R5", "R6", "R7", "R8"],
    "test_performance":       ["R4", "R8"],
    "test_property":          ["R6", "R8"],
    "test_data_deletion":     ["R7"],
    "test_data_safety":       ["R7", "R9"],
    "test_gui_smoke":         ["R8"],
    "test_i18n":              ["R8"],
    "test_mobile_helpers":    ["R8"],
    "test_legal":             ["R7", "R9"],
    "test_privacy_policy":    ["R7", "R9"],
    "test_playstore_check":   ["R9"],
    "test_store_listing":     ["R9"],
    "test_pairing":           ["R5", "R7"],
    "test_pairing_handshake": ["R5", "R7"],
    # --- tests/concept/ (Konzept-, Negativ-, Compliance-Ebene) ---
    "test_members_scenarios":     ["R1", "R5"],
    "test_roles_permissions":     ["R1", "R7"],
    "test_pairwise_matrix":       ["R1", "R3"],
    "test_properties_concept":    ["R8"],
    "test_negative_inputs":       ["R8"],
    "test_negative_network":      ["R5", "R8"],
    "test_negative_security":     ["R7", "R8"],
    "test_privacy_scan":          ["R7"],
    "test_privacy_data_rights":   ["R7"],
    "test_gitignore_completeness": ["R7"],
    "test_gui_free_tier_boot":    ["R8"],
    "test_gui_refresh_guards":    ["R8"],
    "test_gui_widget_guards":     ["R8"],
    "test_playstore_sync":        ["R9"],
    "test_release_gate":          ["R9"],
    "test_release_gate_extended": ["R9"],
    "test_build_status":          ["R9", "R10"],
    "test_control_panel":         ["R10"],
    "test_dashboard_generator":   ["R10"],
    "test_protocol_generator":    ["R10"],
    "test_md_to_html":            ["R10"],
}


def _module_stem(classname: str) -> str:
    """Liefert den Dateinamen-Stamm (z.B. 'test_smoke') aus dem Classname."""
    for part in reversed(classname.split(".")):
        if part.startswith("test_"):
            return part
    return classname.split(".")[-1]


_SOURCE_CACHE: dict[tuple, dict] = {}


def _resolve_source(classname: str, name: str) -> dict:
    """Loest den Quelltext/Docstring eines Testfalls via Introspection auf.

    Liefert ein Dict mit file/lineno/doc/source. Parametrisierte Namen
    (``test_x[a-b]``) werden auf die Basisfunktion reduziert. Fehler
    werden still verschluckt - dann bleiben die Felder leer.
    """
    base = name.split("[")[0]
    key = (classname, base)
    if key in _SOURCE_CACHE:
        return _SOURCE_CACHE[key]
    info = {"file": "", "lineno": 0, "doc": "", "source": ""}
    obj = None
    parts = classname.split(".")
    try:
        mod = importlib.import_module(classname)
        obj = getattr(mod, base, None)
    except Exception:
        mod = None
    if obj is None and len(parts) >= 2:
        # classname koennte 'modul.Klasse' sein -> Methode in der Klasse
        try:
            m2 = importlib.import_module(".".join(parts[:-1]))
            cls = getattr(m2, parts[-1], None)
            if cls is not None:
                obj = getattr(cls, base, None)
        except Exception:
            obj = None
    if obj is not None:
        try:
            src = inspect.getsource(obj)
            info["source"] = src if len(src) <= 12000 else src[:12000] + "\n# ... (gekuerzt)"
            info["doc"] = (inspect.getdoc(obj) or "")[:800]
            srcfile = inspect.getsourcefile(obj) or inspect.getfile(obj)
            if srcfile:
                try:
                    info["file"] = os.path.relpath(
                        srcfile, REPO_ROOT).replace(os.sep, "/")
                except ValueError:
                    info["file"] = srcfile
            _, lineno = inspect.getsourcelines(obj)
            info["lineno"] = lineno
        except (OSError, TypeError):
            pass
    _SOURCE_CACHE[key] = info
    return info


def _enrich_records(records: list[dict]) -> None:
    """Reichert jeden Test-Record um Modul, Anforderungen und Quelltext an."""
    for r in records:
        stem = _module_stem(r.get("classname", ""))
        r["module"] = stem
        r["requirements"] = FILE_REQUIREMENTS.get(stem, [])
        src = _resolve_source(r.get("classname", ""), r.get("name", ""))
        r["file"] = src["file"]
        r["lineno"] = src["lineno"]
        r["doc"] = src["doc"]
        r["source"] = src["source"]
REPORT_DIR = REPO_ROOT / "tests" / "concept" / "reports"
JUNIT_XML = REPORT_DIR / "junit.xml"
PROTOCOL_MD = REPORT_DIR / "protocol.md"
PROTOCOL_JSON = REPORT_DIR / "protocol.json"


# Marker -> Konzept-Bereich (1-stellig dargestellte Anhang-IDs)
MARKER_SECTIONS = [
    ("members",       "Kapitel 2 / Anhang D - Mitglieder-Szenarien"),
    ("roles",         "Anhang D - Rollen- und Berechtigungsmatrix"),
    ("combinatorics", "Kapitel 3 / Anhang C - Pairwise-Matrix"),
    ("property",      "Kapitel 8 - Property-/Fuzz-Tests"),
    ("negative",      "Teil II Abschnitt 11 - Negativtests"),
    ("privacy",       "Teil II Abschnitt 12 - Datenschutztests"),
    ("security",      "Teil II Abschnitt 11.3 D - Security-Negativtests"),
    ("playstore",     "Play-Store-Sync (tools/playstore_sync.py)"),
    ("release_gate",  "Anhang J + J2 - Release-Gate"),
]


def _console_python() -> str:
    """Liefert einen Konsolen-Interpreter (``python.exe``) fuer den pytest-Lauf.

    Das Control-Panel startet die App – und damit diesen Generator – mit
    ``pythonw.exe`` (kein Konsolenfenster). Unter ``pythonw.exe`` gibt es keine
    gueltigen Stdio-Handles: pytest bricht dann sofort ab bzw. einzelne Tests,
    die Subprozesse starten oder auf die Konsole schreiben, schlagen fehl.
    ``python.exe`` liegt bei CPython-Windows-Installationen stets neben
    ``pythonw.exe`` – wir nutzen es, damit der Lauf identisch zur Konsole ist.
    """
    exe = Path(sys.executable)
    if exe.name.lower() == "pythonw.exe":
        console = exe.with_name("python.exe")
        if console.is_file():
            return str(console)
    return sys.executable


def _run_pytest(target: str, marker: str | None) -> tuple[int, float]:
    """Fuehrt pytest aus, schreibt JUnit-XML, liefert (rc, sekunden).

    pytest laeuft bewusst unter einem Konsolen-Interpreter (siehe
    :func:`_console_python`) und seine Ausgabe wird ueber eine Pipe
    eingesammelt und – sofern ein echtes Stdout existiert – durchgereicht.
    Wuerde pytest stattdessen unter ``pythonw.exe`` die Eltern-Handles erben,
    braeche es sofort mit rc=1 ab, ohne JUnit-XML zu schreiben; ein veraltetes
    gruenes XML wuerde dann als frisches Ergebnis fehlinterpretiert und
    faelschlich ein GO abgeleitet.

    Zusaetzlich wird ein evtl. vorhandenes altes JUnit-XML vorab geloescht,
    damit ein fehlgeschlagener Lauf niemals auf Altdaten ein GO ableiten kann.
    """
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        JUNIT_XML.unlink()
    except FileNotFoundError:
        pass
    args = [_console_python(), "-m", "pytest", target,
            "-q", "--tb=short", "-p", "no:cacheprovider",
            f"--junit-xml={JUNIT_XML}"]
    if marker:
        args += ["-m", marker]
    t0 = time.monotonic()
    print("Running:", " ".join(args))
    proc = subprocess.Popen(args, cwd=REPO_ROOT,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True, bufsize=1)
    assert proc.stdout is not None
    for line in proc.stdout:
        # Live durchreichen, falls ein Stdout vorhanden ist (unter pythonw None)
        if sys.stdout is not None:
            try:
                sys.stdout.write(line)
                sys.stdout.flush()
            except (ValueError, OSError):
                pass
    rc = proc.wait()
    dt = time.monotonic() - t0
    return rc, dt


def _parse_junit(path: Path) -> list[dict]:
    """Eine flache Liste von Test-Records aus dem JUnit-XML."""
    if not path.is_file():
        return []
    tree = ET.parse(path)
    root = tree.getroot()
    # JUnit-Wurzel kann <testsuites> oder <testsuite> sein
    suites = root.findall(".//testsuite") or [root]
    records: list[dict] = []
    for suite in suites:
        for case in suite.findall("testcase"):
            classname = case.attrib.get("classname", "")
            name = case.attrib.get("name", "")
            time_s = float(case.attrib.get("time", "0") or 0)
            status = "passed"
            message = ""
            if case.find("failure") is not None:
                status = "failed"
                fnode = case.find("failure")
                message = (fnode.attrib.get("message", "")
                           if fnode is not None else "")
            elif case.find("error") is not None:
                status = "error"
                enode = case.find("error")
                message = (enode.attrib.get("message", "")
                           if enode is not None else "")
            elif case.find("skipped") is not None:
                status = "skipped"
                snode = case.find("skipped")
                message = (snode.attrib.get("message", "")
                           if snode is not None else "")
            records.append({
                "classname": classname,
                "name": name,
                "id": f"{classname}::{name}",
                "time_s": time_s,
                "status": status,
                "message": message,
            })
    return records


def _classify(records: list[dict]) -> dict[str, dict]:
    """Bucketed Auswertung pro Datei + Gesamtstatistik."""
    by_file: dict[str, dict] = {}
    totals = {"passed": 0, "failed": 0, "error": 0, "skipped": 0,
              "duration_s": 0.0, "count": 0}
    for r in records:
        f = r["classname"].split(".")[-1] or "(unknown)"
        b = by_file.setdefault(f, {"passed": 0, "failed": 0, "error": 0,
                                     "skipped": 0, "duration_s": 0.0,
                                     "count": 0, "tests": []})
        b[r["status"]] += 1
        b["duration_s"] += r["time_s"]
        b["count"] += 1
        b["tests"].append(r)
        totals[r["status"]] += 1
        totals["duration_s"] += r["time_s"]
        totals["count"] += 1
    return {"by_file": by_file, "totals": totals}


def _stats_by_marker(records: list[dict]) -> dict[str, dict]:
    """Approximiert die Marker anhand des Dateinamens."""
    mapping = {
        "test_members_scenarios":     "members",
        "test_roles_permissions":     "roles",
        "test_pairwise_matrix":       "combinatorics",
        "test_properties_concept":    "property",
        "test_release_gate":          "release_gate",
        "test_release_gate_extended": "release_gate",
        "test_protocol_generator":    "release_gate",
        "test_dashboard_generator":   "release_gate",
        "test_md_to_html":            "release_gate",
        "test_playstore_sync":        "playstore",
        "test_build_status":          "release_gate",
        "test_control_panel":         "release_gate",
        "test_gui_refresh_guards":    "release_gate",
        "test_gui_widget_guards":     "release_gate",
        "test_gui_free_tier_boot":    "release_gate",
        "test_gitignore_completeness": "release_gate",
        "test_negative_inputs":       "negative",
        "test_negative_network":      "negative",
        "test_negative_security":     "security",
        "test_privacy_scan":          "privacy",
        "test_privacy_data_rights":   "privacy",
    }
    out: dict[str, dict] = {m: {"passed": 0, "failed": 0, "error": 0,
                                 "skipped": 0, "count": 0,
                                 "duration_s": 0.0}
                            for _, m in [(0, n) for n in mapping.values()]}
    for r in records:
        fname = r["classname"].split(".")[-1]
        marker = mapping.get(fname)
        if not marker:
            continue
        b = out[marker]
        b[r["status"]] += 1
        b["count"] += 1
        b["duration_s"] += r["time_s"]
    return out


def _stats_by_requirement(records: list[dict]) -> dict[str, dict]:
    """Aggregiert Test-Ergebnisse pro Anforderungs-ID (R1..R10).

    Ein Test, der mehreren Anforderungen zugeordnet ist, zaehlt in jeder
    mit. Bereiche ohne Tests bleiben mit count=0 sichtbar, damit Luecken
    im Dashboard auffallen.
    """
    out: dict[str, dict] = {
        rid: {"label": label, "passed": 0, "failed": 0, "error": 0,
              "skipped": 0, "count": 0, "duration_s": 0.0,
              "files": set()}
        for rid, label in REQUIREMENTS.items()
    }
    for r in records:
        for rid in r.get("requirements", []):
            b = out.get(rid)
            if b is None:
                continue
            b[r["status"]] += 1
            b["count"] += 1
            b["duration_s"] += r.get("time_s", 0.0)
            b["files"].add(r.get("module", ""))
    # set -> sortierte Liste, damit JSON-serialisierbar
    for b in out.values():
        b["files"] = sorted(f for f in b["files"] if f)
    return out


def _go_no_go(totals: dict, marker_stats: dict) -> tuple[str, list[str]]:
    """Implementiert Anhang J (Go/No-Go-Kriterien) auf Test-Ebene."""
    reasons: list[str] = []
    if totals["failed"] or totals["error"]:
        reasons.append(
            f"{totals['failed']} fehlgeschlagene / {totals['error']} Fehler-"
            "Tests")
    # Release-Gate selbst muss komplett gruen sein
    gate = marker_stats.get("release_gate", {})
    if gate.get("count", 0) == 0:
        reasons.append("Release-Gate-Suite ist nicht gelaufen")
    elif gate.get("failed", 0) or gate.get("error", 0):
        reasons.append("Release-Gate enthaelt fehlgeschlagene Kriterien")
    # mind. die fuenf Bereiche muessen Tests haben
    expected = {"members", "roles", "combinatorics", "property",
                "release_gate"}
    missing = [m for m in expected if marker_stats.get(m, {}).get("count", 0)
               == 0]
    if missing:
        reasons.append(f"Keine Tests fuer Bereich(e): {sorted(missing)}")
    if reasons:
        return "NO-GO", reasons
    return "GO", []


def _md_status(s: str) -> str:
    return {"passed": "[pass]", "failed": "[FAIL]", "error": "[ERR]",
            "skipped": "[skip]"}.get(s, s)


def _format_protocol_md(records: list[dict], classified: dict,
                        marker_stats: dict, gate_decision: str,
                        gate_reasons: list[str], target: str,
                        marker: str | None, elapsed: float) -> str:
    totals = classified["totals"]
    by_file = classified["by_file"]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    lines: list[str] = []
    lines.append("# Test-Protokoll")
    lines.append("")
    lines.append(f"- Datum: {now}")
    lines.append(f"- Host: {platform.node()} ({platform.platform()})")
    lines.append(f"- Python: {sys.version.split()[0]}")
    lines.append(f"- Target: `{target}`"
                 f"{(' / Marker: `' + marker + '`') if marker else ''}")
    lines.append(f"- Laufzeit pytest: {elapsed:.2f} s")
    lines.append("")
    lines.append(f"**Entscheidung:** {gate_decision}")
    if gate_reasons:
        lines.append("")
        lines.append("Gruende fuer NO-GO:")
        for r in gate_reasons:
            lines.append(f"  - {r}")
    lines.append("")

    # 1) Gesamtuebersicht
    lines.append("## Gesamtuebersicht")
    lines.append("")
    lines.append("| Status | Anzahl |")
    lines.append("| --- | ---: |")
    for k in ("passed", "failed", "error", "skipped"):
        lines.append(f"| {k} | {totals[k]} |")
    lines.append(f"| **gesamt** | **{totals['count']}** |")
    lines.append(f"| Dauer (Summe) | {totals['duration_s']:.2f} s |")
    lines.append("")

    # 2) Konzeptabschnitte
    lines.append("## Abdeckung nach Konzept-Bereich (Anhang)")
    lines.append("")
    lines.append("| Bereich (Anhang) | Tests | passed | failed | error "
                 "| skipped | Dauer (s) |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for marker_key, label in MARKER_SECTIONS:
        b = marker_stats.get(marker_key, {})
        if not b.get("count", 0):
            continue
        lines.append(
            f"| {label} | {b['count']} | {b['passed']} | {b['failed']} "
            f"| {b['error']} | {b['skipped']} | {b['duration_s']:.2f} |")
    lines.append("")

    # 3) pro Datei
    lines.append("## Ergebnisse pro Testdatei")
    lines.append("")
    lines.append("| Datei | Tests | passed | failed | error | skipped | "
                 "Dauer (s) |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for fname in sorted(by_file):
        b = by_file[fname]
        lines.append(
            f"| {fname} | {b['count']} | {b['passed']} | {b['failed']} "
            f"| {b['error']} | {b['skipped']} | {b['duration_s']:.2f} |")
    lines.append("")

    # 4) Failures im Detail
    failed_records = [r for r in records
                      if r["status"] in ("failed", "error")]
    if failed_records:
        lines.append("## Fehlgeschlagene Tests")
        lines.append("")
        for r in failed_records:
            lines.append(f"### {r['id']}")
            lines.append("")
            lines.append("```")
            lines.append(r.get("message", "")[:1500])
            lines.append("```")
            lines.append("")

    # 5) Alle Tests aufgelistet (nachweisbare Spur)
    lines.append("## Vollstaendige Test-Liste")
    lines.append("")
    lines.append("| Status | Test-ID | Dauer (s) |")
    lines.append("| --- | --- | ---: |")
    for r in sorted(records, key=lambda x: (x["status"], x["id"])):
        lines.append(
            f"| {_md_status(r['status'])} | `{r['id']}` | "
            f"{r['time_s']:.3f} |")
    lines.append("")

    # 6) Erlaeuterung Mapping zu Anhang A-K
    lines.append("## Mapping zu Anhang A-K (TESTING.md)")
    lines.append("")
    lines.append("| Anhang | Inhalt | Quelle im Repo |")
    lines.append("| --- | --- | --- |")
    lines.append("| A | Vollstaendiges Testkonzept | `TESTING.md` |")
    lines.append("| B | Testarchitektur            | `tests/concept/` |")
    lines.append("| C | Pairwise-Matrix            | `tests/concept/"
                 "reports/pairwise-matrix.tsv` |")
    lines.append("| D | Rollen-/Mitglieder-TCs     | "
                 "`tests/concept/test_roles_permissions.py`, "
                 "`tests/concept/test_members_scenarios.py` |")
    lines.append("| E | Aufgaben-/Funktions-TCs    | "
                 "`tests/concept/test_pairwise_matrix.py` |")
    lines.append("| F | 14-Tage-Testplan           | "
                 "`TESTING.md` Abschnitt 7 / Anhang F |")
    lines.append("| G | Tester-Onboarding          | "
                 "`TESTING.md` Anhang G |")
    lines.append("| H | Feedback-/Fehlerberichte   | "
                 "`TESTING.md` Anhang H |")
    lines.append("| I | CI/CD-Pipeline             | "
                 "`TESTING.md` Anhang I + `tools/test_protocol.py` |")
    lines.append("| J | Go/No-Go-Kriterien         | "
                 "`tests/concept/test_release_gate.py` |")
    lines.append("| K | Massnahmenplan             | "
                 "`TESTING.md` Anhang K |")
    lines.append("")
    return "\n".join(lines)


def _write_failure_protocol(rc: int, elapsed: float, target: str,
                            marker: str | None) -> str:
    """Schreibt ein ehrliches NO-GO-Protokoll, wenn pytest kein frisches
    JUnit-XML erzeugt hat (z.B. Abbruch vor dem ersten Test, etwa weil unter
    ``pythonw.exe`` kein Konsolen-Stdout vorhanden ist). So kann das Dashboard
    niemals auf Altdaten ein GO anzeigen. Liefert den NO-GO-Grund zurueck."""
    now = datetime.now(timezone.utc)
    reason = (f"pytest lieferte kein frisches JUnit-XML (Exit-Code {rc}, "
              f"{elapsed:.2f}s) - Lauf vermutlich vor dem ersten Test "
              f"abgebrochen.")
    lines = [
        "# Test-Protokoll",
        "",
        f"- Datum: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"- Host: {platform.node()} ({platform.platform()})",
        f"- Python: {sys.version.split()[0]}",
        f"- Target: `{target}`"
        f"{(' / Marker: `' + marker + '`') if marker else ''}",
        f"- Laufzeit pytest: {elapsed:.2f} s",
        "",
        "**Entscheidung:** NO-GO",
        "",
        "Gruende fuer NO-GO:",
        f"  - {reason}",
        "",
    ]
    PROTOCOL_MD.write_text("\n".join(lines), encoding="utf-8")
    PROTOCOL_JSON.write_text(json.dumps({
        "records": [],
        "totals": {"passed": 0, "failed": 0, "error": 0, "skipped": 0,
                   "duration_s": 0.0, "count": 0},
        "by_file": {},
        "by_marker": {},
        "requirements": REQUIREMENTS,
        "by_requirement": {},
        "decision": "NO-GO",
        "reasons": [reason],
        "elapsed_s": elapsed,
        "exit_code": rc,
        "generated_at": now.isoformat(),
    }, indent=2), encoding="utf-8")
    return reason


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=
                                      argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--target", default="tests/concept",
                        help="pytest-Target (Default: tests/concept)")
    parser.add_argument("--all", action="store_true",
                        help="auf gesamte tests/-Suite anwenden")
    parser.add_argument("--marker", default=None,
                        help="optionaler -m <marker>")
    args = parser.parse_args(argv)

    target = "tests" if args.all else args.target
    rc, elapsed = _run_pytest(target, args.marker)

    records = _parse_junit(JUNIT_XML)
    if not records:
        print("WARN: pytest erzeugte kein frisches JUnit-XML - schreibe "
              "NO-GO-Protokoll statt veralteter Daten.")
        reason = _write_failure_protocol(rc, elapsed, target, args.marker)
        print(f"Protokoll geschrieben: {PROTOCOL_MD}")
        print("Entscheidung:         NO-GO")
        print(f"  - {reason}")
        return rc or 1
    _enrich_records(records)
    classified = _classify(records)
    marker_stats = _stats_by_marker(records)
    req_stats = _stats_by_requirement(records)
    decision, reasons = _go_no_go(classified["totals"], marker_stats)
    md = _format_protocol_md(records, classified, marker_stats, decision,
                              reasons, target, args.marker, elapsed)

    PROTOCOL_MD.write_text(md, encoding="utf-8")
    PROTOCOL_JSON.write_text(json.dumps({
        "records": records,
        "totals": classified["totals"],
        "by_file": {f: {k: v for k, v in b.items() if k != "tests"}
                      for f, b in classified["by_file"].items()},
        "by_marker": marker_stats,
        "requirements": REQUIREMENTS,
        "by_requirement": req_stats,
        "decision": decision,
        "reasons": reasons,
        "elapsed_s": elapsed,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }, indent=2), encoding="utf-8")

    print()
    print(f"Protokoll geschrieben: {PROTOCOL_MD}")
    print(f"JSON-Protokoll:       {PROTOCOL_JSON}")
    print(f"JUnit-XML:            {JUNIT_XML}")
    print(f"Entscheidung:         {decision}")
    if reasons:
        for r in reasons:
            print(f"  - {r}")
    return 0 if (decision == "GO" and rc == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
