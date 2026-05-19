"""
Erzeugt API.md aus den real geladenen Modulen.

Aufruf:
    python tools/gen_api_doc.py > API.md
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database import Database
from main import build_registry
from services.output import OutputService


def main() -> None:
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = Database(path)
    out_dir = Path(tempfile.gettempdir())
    output = OutputService(out_dir)
    registry = build_registry(db, output)

    lines: list[str] = [
        "# API-Referenz (Capabilities)",
        "",
        "Automatisch aus den geladenen Modulen erzeugt. Regenerieren mit:",
        "",
        "```pwsh",
        "python tools/gen_api_doc.py > API.md",
        "```",
        "",
    ]

    caps_by_mod: dict[str, list] = {}
    for cap in registry.all_capabilities():
        mod = cap.name.split(".")[0]
        caps_by_mod.setdefault(mod, []).append(cap)

    lines.append(
        f"Gesamtzahl: **{sum(len(v) for v in caps_by_mod.values())}** "
        f"Capabilities in **{len(caps_by_mod)}** Modulen.")
    lines.append("")

    for mod in sorted(caps_by_mod):
        lines.append(f"## Modul `{mod}`")
        lines.append("")
        for cap in sorted(caps_by_mod[mod], key=lambda c: c.name):
            flags: list[str] = []
            if cap.destructive:
                flags.append("destruktiv")
            if cap.internal:
                flags.append("intern")
            flag_str = f" *({', '.join(flags)})*" if flags else ""
            lines.append(f"### `{cap.name}`{flag_str}")
            lines.append("")
            lines.append(cap.description)
            lines.append("")
            if cap.parameters:
                lines.append("**Parameter:**")
                lines.append("")
                for k, v in cap.parameters.items():
                    req = " **(erforderlich)**" if v.get(
                        "_required") else ""
                    desc = v.get("description", "")
                    type_str = v.get("type", "any")
                    lines.append(
                        f"- `{k}` ({type_str}){req} - {desc}")
                lines.append("")
        lines.append("")

    sys.stdout.write("\n".join(lines))

    db.close()
    os.unlink(path)


if __name__ == "__main__":
    main()
