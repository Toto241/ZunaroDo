"""
Generiert maschinenlesbare Contract-Artefakte fuer den Google-AI-Studio-
Build-Mode-Re-Build (und allgemein fuer jede Web-/Node-Portierung) **direkt
aus dem echten Code** - nichts wird haendisch dupliziert.

Erzeugt unter ``docs/ai-studio/contracts/``:

  capabilities.json   Vollstaendige Capability-Liste (Name, Beschreibung,
                      Parameter-Schema, Flags destructive/internal, Modul).
  openapi.json        OpenAPI-3.1-Spezifikation: je Capability ein
                      POST /api/<capability> mit Request-Body = Parameter-
                      Schema. So baut Build Mode die Node-Endpunkte 1:1
                      statt sie zu erraten.
  schema.sql          DDL des tatsaechlichen SQLite-Schemas (aus
                      sqlite_master) - Grundlage fuer die Cloud-SQL-Abbildung.
  schema.prisma       Aus dem Schema abgeleitetes Prisma-Datenmodell
                      (Naeherung; Build Mode nutzt es fuer Cloud SQL/Postgres).

Aufruf:

    python -m tools.gen_ai_studio_contracts
    python -m tools.gen_ai_studio_contracts --check   # nur pruefen, ob aktuell
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import sys
import tempfile
from typing import Any

# Repo-Wurzel in den Pfad legen, falls direkt aufgerufen
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

OUT_DIR = os.path.join(_ROOT, "docs", "ai-studio", "contracts")

# SQLite-Affinitaet -> Prisma-Skalar (Naeherung)
_PRISMA_TYPE = {
    "INTEGER": "Int",
    "INT": "Int",
    "REAL": "Float",
    "FLOAT": "Float",
    "NUMERIC": "Decimal",
    "BOOLEAN": "Boolean",
    "TEXT": "String",
    "CLOB": "String",
    "BLOB": "Bytes",
}


def _build_registry():
    """Baut dieselbe Registry wie die echten Clients - auf einer Temp-DB."""
    from database import Database
    from main import build_registry
    from services.output import OutputService

    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = Database(db_path)
    output_dir = tempfile.mkdtemp(prefix="ah_contracts_")
    output = OutputService(output_dir)
    registry = build_registry(db, output)
    return registry, db, db_path, output_dir


def build_capabilities(registry) -> list[dict[str, Any]]:
    """Vollstaendige Capability-Liste inkl. interner und gesperrter."""
    caps: list[dict[str, Any]] = []
    for cap in sorted(registry.all_capabilities(include_disabled=True),
                      key=lambda c: c.name):
        schema = cap.to_tool_schema()
        caps.append({
            "name": cap.name,
            "module": cap.module_id,
            "description": schema["description"],
            "destructive": bool(cap.destructive),
            "internal": bool(cap.internal),
            "parameters": schema["parameters"],
        })
    return caps


def build_openapi(capabilities: list[dict[str, Any]]) -> dict[str, Any]:
    """OpenAPI 3.1: je Capability ein POST /api/<name>."""
    paths: dict[str, Any] = {}
    for cap in capabilities:
        tags = [cap["module"]]
        op: dict[str, Any] = {
            "operationId": cap["name"].replace(".", "_"),
            "summary": cap["description"],
            "tags": tags,
            "x-destructive": cap["destructive"],
            "x-internal": cap["internal"],
            "requestBody": {
                "required": bool(cap["parameters"].get("required")),
                "content": {
                    "application/json": {"schema": cap["parameters"]},
                },
            },
            "responses": {
                "200": {
                    "description": "Ergebnis-Dict der Capability.",
                    "content": {
                        "application/json": {
                            "schema": {"type": "object",
                                       "additionalProperties": True},
                        },
                    },
                },
                "402": {"description": "tier_locked - Capability im "
                                       "aktuellen Tier gesperrt."},
                "400": {"description": "Validierungsfehler (error-Feld)."},
            },
        }
        paths[f"/api/{cap['name']}"] = {"post": op}

    return {
        "openapi": "3.1.0",
        "info": {
            "title": "ZunaroDo Capability API",
            "version": "1.0.0",
            "description": (
                "Aus core.interface.ModuleRegistry generierter "
                "Capability-Contract. Jede Capability ist ein einzelner "
                "Dispatch-Aufruf (ModuleRegistry.dispatch) und wird hier als "
                "POST-Endpunkt abgebildet. Quelle der Wahrheit ist der Code; "
                "diese Datei via tools/gen_ai_studio_contracts.py erzeugen."
            ),
        },
        "servers": [{"url": "/", "description": "App-Backend"}],
        "paths": paths,
    }


def dump_sql_schema(db_path: str) -> str:
    """DDL aus sqlite_master - exakt das, was database.py erzeugt."""
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "SELECT sql FROM sqlite_master "
            "WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%' "
            "ORDER BY CASE type WHEN 'table' THEN 0 ELSE 1 END, name"
        ).fetchall()
    finally:
        con.close()
    header = ("-- Generiert aus dem echten SQLite-Schema (database.py)\n"
              "-- via tools/gen_ai_studio_contracts.py. Nicht haendisch "
              "editieren.\n\n")
    return header + "\n\n".join(r[0].strip() + ";" for r in rows) + "\n"


def _prisma_type(sqlite_type: str) -> str:
    base = (sqlite_type or "TEXT").upper().split("(")[0].strip()
    return _PRISMA_TYPE.get(base, "String")


def dump_prisma_schema(db_path: str) -> str:
    """Aus dem SQLite-Schema abgeleitetes Prisma-Modell (Naeherung)."""
    con = sqlite3.connect(db_path)
    try:
        tables = [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()]
        blocks: list[str] = []
        for table in tables:
            cols = con.execute(f"PRAGMA table_info('{table}')").fetchall()
            # cols: (cid, name, type, notnull, dflt_value, pk)
            lines: list[str] = []
            for _cid, name, ctype, notnull, _dflt, pk in cols:
                ptype = _prisma_type(ctype)
                optional = "" if (notnull or pk) else "?"
                attrs = ""
                if pk:
                    attrs = (" @id @default(autoincrement())"
                             if ptype == "Int" else " @id")
                lines.append(f"  {name} {ptype}{optional}{attrs}")
            model = _pascal(table)
            blocks.append(
                f"model {model} {{\n" + "\n".join(lines) +
                f"\n\n  @@map(\"{table}\")\n}}")
    finally:
        con.close()

    header = (
        "// Aus dem SQLite-Schema (database.py) abgeleitetes Prisma-Modell -\n"
        "// NAEHERUNG fuer die Cloud-SQL-/Postgres-Abbildung im Build Mode.\n"
        "// Beziehungen (@relation) sind bewusst NICHT abgeleitet (SQLite-\n"
        "// FKs ueber ON DELETE SET NULL, siehe ARCHITECTURE.md) und vor dem\n"
        "// Einsatz manuell zu ergaenzen. Generiert via "
        "tools/gen_ai_studio_contracts.py.\n\n"
        "datasource db {\n  provider = \"postgresql\"\n"
        "  url      = env(\"DATABASE_URL\")\n}\n\n"
        "generator client {\n  provider = \"prisma-client-js\"\n}\n\n")
    return header + "\n\n".join(blocks) + "\n"


def _pascal(name: str) -> str:
    return "".join(p.capitalize() for p in name.split("_"))


def generate() -> dict[str, str]:
    registry, db, db_path, output_dir = _build_registry()
    try:
        capabilities = build_capabilities(registry)
        openapi = build_openapi(capabilities)
        sql = dump_sql_schema(db_path)
        prisma = dump_prisma_schema(db_path)
    finally:
        try:
            db.close()
        except Exception:                                  # noqa: BLE001
            pass
        if os.path.exists(db_path):
            try:
                os.unlink(db_path)
            except OSError:
                pass
        shutil.rmtree(output_dir, ignore_errors=True)

    return {
        "capabilities.json": json.dumps(
            {"capabilities": capabilities,
             "count": len(capabilities),
             "destructive": sorted(
                 c["name"] for c in capabilities if c["destructive"]),
             "internal": sorted(
                 c["name"] for c in capabilities if c["internal"])},
            ensure_ascii=False, indent=2) + "\n",
        "openapi.json": json.dumps(openapi, ensure_ascii=False, indent=2)
        + "\n",
        "schema.sql": sql,
        "schema.prisma": prisma,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="Nur pruefen, ob die Artefakte aktuell sind "
                             "(exit 1 bei Drift).")
    args = parser.parse_args(argv)

    artifacts = generate()
    os.makedirs(OUT_DIR, exist_ok=True)

    drift = False
    for name, content in artifacts.items():
        path = os.path.join(OUT_DIR, name)
        old = None
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                old = fh.read()
        if old != content:
            drift = True
            if args.check:
                print(f"DRIFT: {name} ist nicht aktuell.")
            else:
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(content)
                print(f"geschrieben: docs/ai-studio/contracts/{name}")

    if args.check:
        if drift:
            print("Contracts veraltet - "
                  "`python -m tools.gen_ai_studio_contracts` ausfuehren.")
            return 1
        print("Contracts sind aktuell.")
        return 0

    caps = json.loads(artifacts["capabilities.json"])
    print(f"OK - {caps['count']} Capabilities "
          f"({len(caps['destructive'])} destruktiv, "
          f"{len(caps['internal'])} intern).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
