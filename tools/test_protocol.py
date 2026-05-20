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
    ("release_gate",  "Anhang J + J2 - Release-Gate"),
]


def _run_pytest(target: str, marker: str | None) -> tuple[int, float]:
    """Fuehrt pytest aus, schreibt JUnit-XML, liefert (rc, sekunden)."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    args = [sys.executable, "-m", "pytest", target,
            "-q", "--tb=short", "-p", "no:cacheprovider",
            f"--junit-xml={JUNIT_XML}"]
    if marker:
        args += ["-m", marker]
    t0 = time.monotonic()
    print("Running:", " ".join(args))
    rc = subprocess.call(args, cwd=REPO_ROOT)
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


def _classify(records: list[dict]) -> dict:
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
        print("WARN: JUnit-XML enthielt keine Testfaelle.")
        return rc or 1
    classified = _classify(records)
    marker_stats = _stats_by_marker(records)
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
