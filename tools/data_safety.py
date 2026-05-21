"""
Play-Store-"Data Safety"-Automatisierung fuer Alltagshelfer/ZunaroDo.

Die Data-Safety-Angaben im Play Console MUESSEN der Realitaet entsprechen
- eine Falschangabe ist ein Policy-Verstoss. Statt die Antworten von Hand
zu pflegen (und dabei mit der App auseinanderzulaufen), leitet dieses
Tool sie aus den App-Fakten ab und prueft die in playstore.yml
hinterlegten Angaben dagegen.

Ground Truth:
  * Tracking-/Sharing-SDKs werden aus requirements.txt + buildozer.spec
    erkannt. Sind keine vorhanden, DARF nichts geteilt und keine
    Analytics-/Werbe-Zwecke deklariert werden.
  * Der Loesch-Pfad (services/data_deletion.py + Database.wipe_all_data)
    bestimmt 'users_can_request_deletion'.

Aufruf:
    python -m tools.data_safety --generate      # wahrheitsgemaesser YAML-Block
    python -m tools.data_safety --check          # playstore.yml gegen Realitaet
    python -m tools.data_safety --markdown       # Antwortbogen fuers Console-UI
    python -m tools.data_safety --json

Exit-Codes: 0 = ok, 1 = Inkonsistenz (bei --check), 2 = interner Fehler.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLAYSTORE_YML = REPO_ROOT / "playstore.yml"

#: Namens-Fragmente bekannter Tracking-/Analytics-/Sharing-SDKs. Taucht
#: keines davon in den Abhaengigkeiten auf, ist die App nachweislich
#: tracking-frei - dann sind 'shared' und Analytics-Zwecke unzulaessig.
KNOWN_TRACKING_SDKS = (
    "firebase", "crashlytics", "google-analytics", "ga4", "gtag",
    "facebook", "appsflyer", "adjust", "sentry", "mixpanel", "amplitude",
    "flurry", "onesignal", "segment", "branch-sdk", "appcenter",
    "bugsnag", "instabug", "umeng", "yandex-metrica", "matomo",
    "googleanalytics", "admob", "applovin", "unityads",
)

#: Datentypen, die die App lokal erfasst. Alle dienen ausschliesslich der
#: App-Funktionalitaet und verlassen das Geraet nur, wenn der Nutzer
#: optionale Funktionen (IMAP/SMTP, Sync) selbst konfiguriert.
LOCAL_DATA_TYPES: dict[str, dict] = {
    "email": {"collected": True, "shared": False,
              "purpose": "APP_FUNCTIONALITY", "optional": True},
    "name": {"collected": True, "shared": False,
             "purpose": "APP_FUNCTIONALITY", "optional": False},
    "user_content": {"collected": True, "shared": False,
                     "purpose": "APP_FUNCTIONALITY", "optional": False},
}


def _requirement_tokens(repo_root: Path) -> set[str]:
    """Sammelt Paketnamen aus requirements.txt + buildozer.spec (lowercase)."""
    tokens: set[str] = set()
    req = repo_root / "requirements.txt"
    if req.is_file():
        for line in req.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            tokens.add(re.split(r"[=<>!~ \[]", line, maxsplit=1)[0].lower())
    spec = repo_root / "buildozer.spec"
    if spec.is_file():
        for raw in spec.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if line.startswith("requirements") and "=" in line:
                _, _, value = line.partition("=")
                for tok in value.split(","):
                    name = re.split(r"[=<>!~ ]", tok.strip(), maxsplit=1)[0]
                    if name:
                        tokens.add(name.lower())
    return tokens


def detect_tracking_sdks(repo_root: Path = REPO_ROOT) -> list[str]:
    """Liefert die in den Abhaengigkeiten gefundenen Tracking-SDK-Tokens."""
    tokens = _requirement_tokens(repo_root)
    found: set[str] = set()
    for tok in tokens:
        for known in KNOWN_TRACKING_SDKS:
            if known in tok:
                found.add(tok)
    return sorted(found)


def deletion_supported(repo_root: Path = REPO_ROOT) -> bool:
    """True, wenn der Voll-Loesch-Pfad existiert (services + DB-Methode)."""
    svc = repo_root / "services" / "data_deletion.py"
    db = repo_root / "database.py"
    if not svc.is_file() or not db.is_file():
        return False
    return "def wipe_all_data" in db.read_text(encoding="utf-8", errors="ignore")


def generate(repo_root: Path = REPO_ROOT) -> dict:
    """Baut die wahrheitsgemaesse data_safety-Struktur aus App-Fakten."""
    tracking = detect_tracking_sdks(repo_root)
    return {
        "data_collected": True,
        "data_shared": bool(tracking),
        "encrypted_in_transit": True,
        "users_can_request_deletion": deletion_supported(repo_root),
        "types": {name: dict(entry) for name, entry in LOCAL_DATA_TYPES.items()},
        "sdk_inventory": [],
        "privacy_policy_file": "legal/DATENSCHUTZ.md",
    }


def check_consistency(declared: dict, repo_root: Path = REPO_ROOT) -> list[tuple[str, str, str]]:
    """
    Prueft die deklarierten data_safety-Angaben gegen die Realitaet.
    Liefert (severity, path, message)-Tupel; severity in {error, warning}.
    """
    tracking = detect_tracking_sdks(repo_root)
    issues: list[tuple[str, str, str]] = []

    if declared.get("data_shared") and not tracking:
        issues.append((
            "error", "data_safety.data_shared",
            "data_shared=true, aber keine Tracking-/Sharing-SDK in den "
            "Abhaengigkeiten - laut Code wird nichts an Dritte weitergegeben."))

    for tname, entry in (declared.get("types") or {}).items():
        if not isinstance(entry, dict):
            continue
        purpose = entry.get("purpose")
        if purpose in ("ANALYTICS", "ADVERTISING") and not tracking:
            issues.append((
                "error", f"data_safety.types.{tname}.purpose",
                f"Zweck '{purpose}' deklariert, aber kein passendes SDK "
                "vorhanden."))
        if entry.get("shared") and not tracking:
            issues.append((
                "error", f"data_safety.types.{tname}.shared",
                "shared=true ohne Sharing-SDK."))
        for sw in entry.get("shared_with") or []:
            issues.append((
                "error", f"data_safety.types.{tname}.shared_with",
                f"Weitergabe an '{sw}' deklariert, aber kein entsprechendes "
                "SDK in den Abhaengigkeiten."))

    for entry in declared.get("sdk_inventory") or []:
        nm = str(entry.get("name", "")).lower()
        if any(k in nm for k in KNOWN_TRACKING_SDKS) and not tracking:
            issues.append((
                "error", "data_safety.sdk_inventory",
                f"SDK '{entry.get('name')}' gelistet, aber nicht in den "
                "Abhaengigkeiten - Karteileiche oder Falschangabe."))

    if deletion_supported(repo_root) and not declared.get("users_can_request_deletion"):
        issues.append((
            "warning", "data_safety.users_can_request_deletion",
            "Loesch-Pfad existiert, ist aber nicht als true deklariert."))
    if not deletion_supported(repo_root):
        issues.append((
            "warning", "data_safety.users_can_request_deletion",
            "Kein Voll-Loesch-Pfad gefunden - Play verlangt In-App-Loeschung."))

    return issues


def format_markdown(ds: dict) -> str:
    """Antwortbogen fuer das Data-Safety-Formular im Play Console."""
    lines = [
        "# Play Console - Data Safety (Antwortbogen)",
        "",
        f"- Daten gesammelt: **{ds.get('data_collected')}**",
        f"- Daten an Dritte weitergegeben: **{ds.get('data_shared')}**",
        f"- Verschluesselt bei Uebertragung: **{ds.get('encrypted_in_transit')}**",
        f"- Nutzer koennen Loeschung anfordern: "
        f"**{ds.get('users_can_request_deletion')}**",
        "",
        "## Datentypen",
        "",
        "| Typ | gesammelt | geteilt | Zweck | optional |",
        "| --- | --- | --- | --- | --- |",
    ]
    for name, e in (ds.get("types") or {}).items():
        lines.append(
            f"| {name} | {e.get('collected')} | {e.get('shared')} | "
            f"{e.get('purpose')} | {e.get('optional')} |")
    inv = ds.get("sdk_inventory") or []
    lines += ["", "## SDK-Inventar", ""]
    lines.append("(keine Tracking-/Sharing-SDKs)" if not inv
                 else "\n".join(f"- {e.get('name')}" for e in inv))
    return "\n".join(lines)


def _load_declared() -> dict:
    if not PLAYSTORE_YML.is_file():
        return {}
    text = PLAYSTORE_YML.read_text(encoding="utf-8")
    try:
        import yaml
        data = yaml.safe_load(text) or {}
    except ImportError:                               # pragma: no cover
        data = json.loads(text)
    return data.get("data_safety") or {}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Play Data Safety aus App-Fakten ableiten/pruefen.")
    parser.add_argument("--generate", action="store_true",
                        help="Wahrheitsgemaesse data_safety-Struktur ausgeben.")
    parser.add_argument("--check", action="store_true",
                        help="playstore.yml gegen die Realitaet pruefen.")
    parser.add_argument("--markdown", action="store_true",
                        help="Antwortbogen fuers Console-UI.")
    parser.add_argument("--json", action="store_true",
                        help="Ausgabe als JSON statt YAML/Text.")
    args = parser.parse_args(argv)

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")     # type: ignore[union-attr]
        except (AttributeError, ValueError):         # pragma: no cover
            pass

    if args.check:
        declared = _load_declared()
        issues = check_consistency(declared)
        errors = [i for i in issues if i[0] == "error"]
        for sev, path, msg in issues:
            stream = sys.stderr if sev == "error" else sys.stdout
            print(f"[{sev.upper()}] {path}: {msg}", file=stream)
        if not issues:
            print("OK: Data-Safety-Angaben sind konsistent mit dem Code.")
        return 1 if errors else 0

    ds = generate()
    if args.markdown:
        print(format_markdown(ds))
    elif args.json:
        print(json.dumps(ds, indent=2, ensure_ascii=False))
    else:
        try:
            import yaml
            print(yaml.safe_dump({"data_safety": ds}, sort_keys=False,
                                 allow_unicode=True, indent=2))
        except ImportError:                           # pragma: no cover
            print(json.dumps({"data_safety": ds}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":                            # pragma: no cover
    raise SystemExit(main())
