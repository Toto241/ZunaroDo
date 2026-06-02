"""
Google-Play-Console-Sync (Pull / Push / Diff / Validate / Init).

Macht aus dem Inhalt von PLAYSTORE.md *Konfiguration*. Eine einzige YAML
(`playstore.yml` im Projekt-Root) ist die Quelle der Wahrheit fuer alle
automatisierbaren Einstellungen:

  identity            - package_name, app_name, default_language
  contact             - support_email, support_url, marketing_url
  localizations       - title, short/long description, video pro Sprache
  images              - icon, feature_graphic, screenshots, promo_video
  store_listing       - category, content_rating, tags
  data_safety         - Datentypen, Zwecke, Weitergaben (DSGVO-konform)
  permissions         - Manifest-Permissions (Soll vs. Ist)
  tracks              - internal/closed/production-Releases (versionCode,
                        userFraction, release_notes)
  testers             - Closed-Test-Pool (Google-Group, Mail-Liste)
  monitoring          - Crashlytics-Schwellen, ANR-Schwellen
  policy              - Inhaltsbewertung, Zielgruppe, Werbung

CLI-Aufrufe:

  python -m tools.playstore_sync init       # YAML aus buildozer.spec
                                              # / Repo-Heuristik vorbefuellen
  python -m tools.playstore_sync validate   # Soll-Schema pruefen
  python -m tools.playstore_sync pull       # Werte aus Play Console
                                              # in die YAML uebernehmen
  python -m tools.playstore_sync push       # YAML in die Play Console
                                              # uebertragen (--dry-run)
  python -m tools.playstore_sync diff       # YAML vs. Play Console
  python -m tools.playstore_sync export     # gerendertes Markdown fuer
                                              # die Doku erzeugen
  python -m tools.playstore_sync sample     # Beispiel-YAML aus dem Repo
                                              # ausgeben (stdout)

Authentifizierung gegen die Google-Play-Developer-API:

  - Service-Account-JSON ablegen (Pfad in ENV `GOOGLE_PLAY_CREDENTIALS`
    oder via `--credentials <pfad>`).
  - Erforderliche Pakete: `google-api-python-client` + `google-auth`.
    Fehlen sie, faellt der Sync auf einen offline-Mock zurueck und
    arbeitet gegen die Datei `playstore.local.json` (Lokal-Repo).
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import os
import re
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_YAML = REPO_ROOT / "playstore.yml"
LOCAL_MIRROR = REPO_ROOT / "playstore.local.json"   # Mock-Backend
ANDROIDPUBLISHER_SCOPE = "https://www.googleapis.com/auth/androidpublisher"


# ---------------------------------------------------------------------------
# YAML-Helfer (PyYAML, mit JSON-Fallback)
# ---------------------------------------------------------------------------
def _load_yaml(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(path)
    text = path.read_text(encoding="utf-8")
    try:
        import yaml
        return yaml.safe_load(text) or {}
    except ImportError:
        return json.loads(text)


def _dump_yaml(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        import yaml
        text = yaml.safe_dump(data, sort_keys=False, allow_unicode=True,
                                width=92, indent=2)
    except ImportError:
        text = json.dumps(data, ensure_ascii=False, indent=2)
    path.write_text(text, encoding="utf-8")


def _dump_str(data: dict) -> str:
    try:
        import yaml
        return yaml.safe_dump(data, sort_keys=False, allow_unicode=True,
                                width=92, indent=2)
    except ImportError:
        return json.dumps(data, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Schema-Definition + Validierung
# ---------------------------------------------------------------------------
@dataclasses.dataclass
class ValidationIssue:
    path: str
    severity: str       # 'error' | 'warning' | 'info'
    message: str


REQUIRED_TOP_KEYS = (
    "identity", "contact", "localizations", "store_listing",
    "data_safety", "permissions", "tracks",
)
REQUIRED_IDENTITY = ("package_name", "app_name", "default_language")
REQUIRED_LOCALE_FIELDS = ("title", "short_description", "full_description")
DATA_SAFETY_PURPOSES = (
    "APP_FUNCTIONALITY", "ANALYTICS", "DEVELOPER_COMMUNICATIONS",
    "ADVERTISING", "FRAUD_PREVENTION", "PERSONALIZATION",
    "ACCOUNT_MANAGEMENT",
)
SUPPORTED_TRACKS = ("internal", "closed", "open", "production")
SUPPORTED_RELEASE_STATUS = ("draft", "inProgress", "halted", "completed",
                             "statusUnspecified")


def validate(config: dict) -> list[ValidationIssue]:
    """Pruefen, ob die YAML strukturell ok ist."""
    issues: list[ValidationIssue] = []

    def err(p: str, m: str) -> None:
        issues.append(ValidationIssue(p, "error", m))

    def warn(p: str, m: str) -> None:
        issues.append(ValidationIssue(p, "warning", m))

    # Top-Level-Keys
    for key in REQUIRED_TOP_KEYS:
        if key not in config:
            err(key, f"Pflicht-Bereich '{key}' fehlt.")

    # identity
    ident = config.get("identity") or {}
    for fld in REQUIRED_IDENTITY:
        if not ident.get(fld):
            err(f"identity.{fld}", f"Pflichtfeld fehlt oder leer.")
    pkg = ident.get("package_name", "")
    if pkg and not re.match(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$", pkg):
        err("identity.package_name",
             f"Paketname '{pkg}' entspricht nicht dem Java-Schema.")

    # contact
    contact = config.get("contact") or {}
    if not contact.get("support_email"):
        err("contact.support_email", "Pflicht-Support-E-Mail fehlt.")
    elif "@" not in contact.get("support_email", ""):
        err("contact.support_email", "Keine gueltige E-Mail.")

    # localizations
    locales = config.get("localizations") or {}
    if not locales:
        err("localizations", "Keine Lokalisierung definiert.")
    default = ident.get("default_language", "")
    if default and default not in locales:
        err(f"localizations.{default}",
             "Standardsprache hat keine Eintraege.")
    for code, lc in locales.items():
        for fld in REQUIRED_LOCALE_FIELDS:
            if not lc.get(fld):
                err(f"localizations.{code}.{fld}", "fehlt")
        title = lc.get("title", "") or ""
        short = lc.get("short_description", "") or ""
        full = lc.get("full_description", "") or ""
        # Play-Limits: title <= 30, short <= 80, full <= 4000
        if len(title) > 30:
            err(f"localizations.{code}.title",
                 f"max. 30 Zeichen, ist {len(title)}.")
        if len(short) > 80:
            err(f"localizations.{code}.short_description",
                 f"max. 80 Zeichen, ist {len(short)}.")
        if len(full) > 4000:
            err(f"localizations.{code}.full_description",
                 f"max. 4000 Zeichen, ist {len(full)}.")

    # permissions
    perms = config.get("permissions") or {}
    declared = set(perms.get("declared", []) or [])
    blocked = set(perms.get("blocked", []) or [])
    overlap = declared & blocked
    if overlap:
        err("permissions",
             f"Permission(s) {overlap} sind in declared UND blocked.")
    if "android.permission.INTERNET" not in declared:
        warn("permissions.declared",
              "INTERNET nicht deklariert - Backend-Calls funktionieren nicht.")

    # data_safety
    ds = config.get("data_safety") or {}
    for type_name, entry in (ds.get("types") or {}).items():
        purpose = entry.get("purpose") if isinstance(entry, dict) else None
        if purpose and purpose not in DATA_SAFETY_PURPOSES:
            warn(f"data_safety.types.{type_name}.purpose",
                  f"Zweck '{purpose}' ist Google nicht bekannt.")

    # tracks
    tracks = config.get("tracks") or {}
    for name, info in tracks.items():
        if name not in SUPPORTED_TRACKS:
            warn(f"tracks.{name}", f"Track '{name}' ist nicht standard.")
        for rel in info.get("releases", []) or []:
            status = rel.get("status", "")
            if status and status not in SUPPORTED_RELEASE_STATUS:
                err(f"tracks.{name}.releases[].status",
                     f"Status '{status}' ist nicht bekannt.")
            uf = rel.get("user_fraction")
            if uf is not None and not (0 <= float(uf) <= 1):
                err(f"tracks.{name}.releases[].user_fraction",
                     f"user_fraction {uf} muss in [0, 1] liegen.")

    return issues


# ---------------------------------------------------------------------------
# Vorbefuellte Beispiel-Konfiguration
# ---------------------------------------------------------------------------
SAMPLE_CONFIG: dict[str, Any] = {
    "identity": {
        "package_name": "de.alltagshelfer.alltagshelfer",
        "app_name": "ZunaroDo",
        "default_language": "de-DE",
        "version_name": "0.9.0",
        "version_code": 1,
    },
    "contact": {
        "support_email": "125914298+Toto241@users.noreply.github.com",
        "support_url": "https://github.com/Toto241/ZunaroDo/issues",
        "marketing_url": "https://github.com/Toto241/ZunaroDo",
        "privacy_policy_url": "https://toto241.github.io/ZunaroDo/privacy/",
    },
    "localizations": {
        "de-DE": {
            "title": "ZunaroDo",
            "short_description": (
                "Vertraege, Termine, Finanzen, Familie - alles lokal "
                "und ohne Cloud-Zwang."),
            "full_description": (
                "ZunaroDo ist ein datenschutzfreundlicher Assistent\n"
                "fuer Vertraege, Termine, Finanzen und Haushaltsplanung.\n"
                "Alle Daten bleiben lokal auf dem Geraet - kein Tracking,\n"
                "keine Werbung."),
            "video_url": "",
        },
        "en-US": {
            "title": "ZunaroDo",
            "short_description": "Privacy-friendly household helper.",
            "full_description": (
                "Manage contracts, expenses, appointments and household\n"
                "tasks - on-device, encrypted, no tracking, no ads."),
            "video_url": "",
        },
    },
    "images": {
        "icon":            "assets/store/icon-512.png",
        "feature_graphic": "assets/store/feature.png",
        "phone_screenshots": [
            "assets/store/phone-1.png",
            "assets/store/phone-2.png",
            "assets/store/phone-3.png",
        ],
        "tablet_screenshots": [],
        "promo_video": "",
    },
    "store_listing": {
        "category": "PRODUCTIVITY",
        "tags":     ["household", "privacy", "german"],
        "content_rating": "USK 0",
        "target_age_group": "all",
        "ads_present": False,
        "in_app_purchases": False,
    },
    # Wahrheitsgemaess: die App nutzt kein Firebase/Analytics/Tracking.
    # Quelle/Pruefung: tools/data_safety.py (--generate/--check).
    "data_safety": {
        "data_collected": True,
        "data_shared": False,
        "encrypted_in_transit": True,
        "users_can_request_deletion": True,
        "types": {
            "email":     {"collected": True,  "shared": False,
                           "purpose": "APP_FUNCTIONALITY",
                           "optional": True},
            "name":      {"collected": True,  "shared": False,
                           "purpose": "APP_FUNCTIONALITY",
                           "optional": False},
            "user_content": {"collected": True, "shared": False,
                              "purpose": "APP_FUNCTIONALITY",
                              "optional": False},
        },
        "sdk_inventory": [],
    },
    "permissions": {
        "declared": [
            "android.permission.INTERNET",
            "android.permission.POST_NOTIFICATIONS",
        ],
        "blocked": [
            "android.permission.MANAGE_EXTERNAL_STORAGE",
            "android.permission.READ_PHONE_STATE",
            "android.permission.ACCESS_BACKGROUND_LOCATION",
            "android.permission.RECEIVE_BOOT_COMPLETED",
            "android.permission.SYSTEM_ALERT_WINDOW",
        ],
    },
    "tracks": {
        "internal": {
            "tester_groups": ["internal-team@example.org"],
            "releases": [
                {"version_code": 1, "version_name": "0.9.0",
                 "status": "completed", "user_fraction": 1.0,
                 "release_notes": {
                     "de-DE": "Initialer Internal-Test-Build."}},
            ],
        },
        "closed": {
            "tester_groups": ["zunarodo-closed-testers@googlegroups.com"],
            "min_testers": 12,
            "min_days": 14,
            "releases": [],
        },
        "production": {
            "release_notes_default_locale": "de-DE",
            "releases": [],
        },
    },
    "testers": {
        "google_groups": [
            "zunarodo-closed-testers@googlegroups.com",
        ],
        "individual_emails": [],
    },
    "monitoring": {
        "crash_free_users_threshold": 99.5,
        "anr_rate_threshold": 0.47,
        "min_engagement_days_per_tester": 10,
    },
    "policy": {
        "content_guidelines_accepted": True,
        "us_export_compliance": False,
        "ads_complies_with_families_policy": False,
        "target_audience_includes_children": False,
    },
    "metadata": {
        "schema_version": 1,
        "generated_by": "tools/playstore_sync.py",
        "generated_at": "1970-01-01T00:00:00+00:00",
    },
}


# ---------------------------------------------------------------------------
# Heuristik: aus Repo (buildozer.spec, legal/, Code) vorbefuellen
# ---------------------------------------------------------------------------
def init_from_repo() -> dict:
    """Erzeugt einen Vorab-Konfigurations-Stand aus dem Repo."""
    cfg = deepcopy(SAMPLE_CONFIG)
    cfg["metadata"]["generated_at"] = datetime.now(timezone.utc).isoformat(
        timespec="seconds")

    spec = REPO_ROOT / "buildozer.spec"
    if spec.is_file():
        text = spec.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("package.domain") and "=" in line:
                domain = line.split("=", 1)[1].strip()
                pkg_name = cfg["identity"]["package_name"].split(".")[-1]
                cfg["identity"]["package_name"] = f"{domain}.{pkg_name}"
            elif line.startswith("package.name") and "=" in line:
                name = line.split("=", 1)[1].strip()
                cfg["identity"]["app_name"] = name.capitalize()
                # Paketname-Suffix anpassen
                pkg = cfg["identity"]["package_name"]
                if pkg.count(".") >= 1:
                    head = pkg.rsplit(".", 1)[0]
                    cfg["identity"]["package_name"] = f"{head}.{name}"
            elif line.startswith("title") and "=" in line:
                cfg["identity"]["app_name"] = line.split("=", 1)[1].strip()
            elif line.startswith("version ") or line.startswith("version="):
                cfg["identity"]["version_name"] = line.split("=", 1)[1].strip()
            elif line.startswith("android.permissions") and "=" in line:
                tokens = line.split("=", 1)[1].strip().split(",")
                declared = ["android.permission." + t.strip()
                            for t in tokens if t.strip()]
                cfg["permissions"]["declared"] = declared

    # Datenschutzerklaerung-Datei vorhanden? -> URL als Platzhalter belassen,
    # aber Hinweis-Flag setzen
    if (REPO_ROOT / "legal" / "DATENSCHUTZ.md").is_file():
        cfg["data_safety"]["privacy_policy_file"] = "legal/DATENSCHUTZ.md"
    return cfg


# ---------------------------------------------------------------------------
# Backend-Abstraktion: Real (Google API) vs. Mock (Datei)
# ---------------------------------------------------------------------------
class Backend:
    name = "abstract"

    def pull(self, package: str) -> dict:
        raise NotImplementedError

    def push(self, package: str, cfg: dict, *,
              dry_run: bool = False) -> list[str]:
        raise NotImplementedError


class MockBackend(Backend):
    """Persistente lokale Datei statt echter Play-Console.

    Erlaubt vollstaendige Tests ohne Google-Konto und ohne Drittpakete.
    """
    name = "mock"

    def __init__(self, mirror_path: Path = LOCAL_MIRROR):
        self.path = mirror_path

    def _read(self) -> dict:
        if not self.path.is_file():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def _write(self, data: dict) -> None:
        self.path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8")

    def pull(self, package: str) -> dict:
        mirror = self._read()
        cfg = mirror.get(package)
        if not cfg:
            raise RuntimeError(
                f"Im Mock-Backend gibt es noch keinen Eintrag fuer "
                f"'{package}'. Lege ihn via 'push' oder 'init' an.")
        return cfg

    def push(self, package: str, cfg: dict, *,
              dry_run: bool = False) -> list[str]:
        existing = self._read().get(package)
        actions: list[str] = []
        if dry_run:
            if existing is None:
                actions.append(f"would create entry for {package}")
            elif existing != cfg:
                actions.extend(_diff_keys(existing, cfg))
            else:
                actions.append("no changes")
            return actions
        data = self._read()
        data[package] = cfg
        self._write(data)
        actions.append(f"wrote {package} to {self.path}")
        return actions


class GooglePlayBackend(Backend):
    """Implementierung gegen die Google Play Developer API v3.

    Pflicht: service-account JSON-Datei mit Rolle 'Release Manager'
    (oder mind. Lese-/Schreibrechten auf das Projekt).
    """
    name = "google"

    def __init__(self, credentials_path: str):
        try:
            from google.oauth2 import service_account     # type: ignore
            from googleapiclient.discovery import build   # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "Pakete 'google-api-python-client' und 'google-auth' "
                "fehlen. Installation: "
                "pip install google-api-python-client google-auth"
            ) from exc
        creds = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=[ANDROIDPUBLISHER_SCOPE])
        self.service = build("androidpublisher", "v3",
                              credentials=creds, cache_discovery=False)

    # Lese-Operation: einzelne Bausteine zusammen­tragen
    def pull(self, package: str) -> dict:
        s = self.service
        edits = s.edits()
        edit = edits.insert(packageName=package, body={}).execute()
        eid = edit["id"]
        try:
            listings = edits.listings().list(
                packageName=package, editId=eid).execute().get("listings", [])
            details = edits.details().get(
                packageName=package, editId=eid).execute()
            tracks = edits.tracks().list(
                packageName=package, editId=eid).execute().get("tracks", [])
        finally:
            try:
                edits.delete(packageName=package, editId=eid).execute()
            except Exception:
                pass

        cfg = deepcopy(SAMPLE_CONFIG)
        cfg["identity"]["package_name"] = package
        cfg["contact"]["support_email"] = details.get("contactEmail", "")
        cfg["contact"]["support_url"]    = details.get("contactWebsite", "")
        cfg["contact"]["marketing_url"]  = details.get("contactWebsite", "")
        cfg["identity"]["default_language"] = details.get(
            "defaultLanguage", "de-DE")
        cfg["localizations"] = {}
        for listing in listings:
            lang = listing.get("language")
            if not lang:
                continue
            cfg["localizations"][lang] = {
                "title":              listing.get("title", ""),
                "short_description":  listing.get("shortDescription", ""),
                "full_description":   listing.get("fullDescription", ""),
                "video_url":          listing.get("video", ""),
            }
        cfg["tracks"] = {}
        for track in tracks:
            name = track.get("track", "")
            cfg["tracks"][name] = {
                "tester_groups": [],
                "releases": [],
            }
            for rel in track.get("releases", []) or []:
                cfg["tracks"][name]["releases"].append({
                    "version_code": (rel.get("versionCodes") or [None])[0],
                    "version_name": rel.get("name", ""),
                    "status":       rel.get("status", ""),
                    "user_fraction": rel.get("userFraction"),
                    "release_notes": {
                        n.get("language"): n.get("text", "")
                        for n in (rel.get("releaseNotes") or [])
                    },
                })
        cfg["metadata"]["generated_by"] = "playstore_sync (pull)"
        cfg["metadata"]["generated_at"] = datetime.now(timezone.utc).isoformat(
            timespec="seconds")
        return cfg

    def push(self, package: str, cfg: dict, *,
              dry_run: bool = False) -> list[str]:
        actions: list[str] = []
        if dry_run:
            actions.append(f"would push edit to {package}")
            return actions
        s = self.service
        edits = s.edits()
        edit = edits.insert(packageName=package, body={}).execute()
        eid = edit["id"]
        try:
            # Details
            details = cfg.get("contact", {})
            edits.details().update(
                packageName=package, editId=eid,
                body={
                    "contactEmail":    details.get("support_email", ""),
                    "contactPhone":    details.get("support_phone", ""),
                    "contactWebsite":  details.get("support_url", ""),
                    "defaultLanguage": cfg.get("identity", {})
                                            .get("default_language", "de-DE"),
                }).execute()
            actions.append("details updated")
            # Listings
            for lang, lc in (cfg.get("localizations") or {}).items():
                edits.listings().update(
                    packageName=package, editId=eid, language=lang,
                    body={
                        "language":          lang,
                        "title":             lc.get("title", "")[:30],
                        "shortDescription":  lc.get("short_description",
                                                     "")[:80],
                        "fullDescription":   lc.get("full_description",
                                                     "")[:4000],
                        "video":             lc.get("video_url", ""),
                    }).execute()
                actions.append(f"listing {lang} updated")
            # Tracks (nur Status + Release-Notes; AAB-Upload erfolgt
            # ueber gradle-play-publisher o.ae.)
            for name, info in (cfg.get("tracks") or {}).items():
                releases = []
                for rel in info.get("releases", []) or []:
                    vc = rel.get("version_code")
                    if not vc:
                        continue
                    releases.append({
                        "name":         rel.get("version_name", ""),
                        "versionCodes": [vc],
                        "status":       rel.get("status", "draft"),
                        "userFraction": rel.get("user_fraction"),
                        "releaseNotes": [
                            {"language": k, "text": v}
                            for k, v in (rel.get("release_notes") or {}).items()
                        ],
                    })
                if releases:
                    edits.tracks().update(
                        packageName=package, editId=eid, track=name,
                        body={"track": name, "releases": releases}).execute()
                    actions.append(f"track {name} updated")
            edits.commit(packageName=package, editId=eid).execute()
            actions.append("edit committed")
        except Exception:
            try:
                edits.delete(packageName=package, editId=eid).execute()
            except Exception:
                pass
            raise
        return actions


def _resolve_backend(args: argparse.Namespace) -> Backend:
    if args.mock:
        return MockBackend(mirror_path=Path(args.mock_file))
    cred_path = args.credentials or os.environ.get("GOOGLE_PLAY_CREDENTIALS")
    if not cred_path:
        print("[INFO] Keine Service-Account-JSON gefunden - nutze Mock.",
              file=sys.stderr)
        return MockBackend(mirror_path=Path(args.mock_file))
    return GooglePlayBackend(cred_path)


# ---------------------------------------------------------------------------
# Diff zwischen zwei Konfigurationen (kanonisch, nestbar)
# ---------------------------------------------------------------------------
def _diff_keys(a: Any, b: Any, prefix: str = "") -> list[str]:
    """Liefert eine flache Liste 'pfad: alt -> neu' Eintraege."""
    out: list[str] = []
    if type(a) is not type(b):
        out.append(f"{prefix}: {_short(a)}  ->  {_short(b)}")
        return out
    if isinstance(a, dict):
        keys = sorted(set(a) | set(b))
        for k in keys:
            sub = f"{prefix}.{k}" if prefix else k
            if k not in a:
                out.append(f"{sub}: <neu>  ->  {_short(b[k])}")
            elif k not in b:
                out.append(f"{sub}: {_short(a[k])}  ->  <entfernt>")
            else:
                out.extend(_diff_keys(a[k], b[k], sub))
    elif isinstance(a, list):
        if a != b:
            out.append(f"{prefix}: {_short(a)}  ->  {_short(b)}")
    else:
        if a != b:
            out.append(f"{prefix}: {_short(a)}  ->  {_short(b)}")
    return out


def _short(value: Any) -> str:
    s = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) \
        else value
    if len(s) > 60:
        return s[:57] + "..."
    return s


# ---------------------------------------------------------------------------
# Markdown-Export (Auszug, fuer release/closed-test-*/)
# ---------------------------------------------------------------------------
def export_markdown(cfg: dict) -> str:
    """Erzeugt eine kompakte Markdown-Zusammenfassung der Konfiguration.

    Wird in `release/<datum>/playstore-snapshot.md` abgelegt - so kann
    der Release-Lead per Pull-Request den Stand vor dem Upload reviewen.
    """
    ident = cfg.get("identity", {}) or {}
    contact = cfg.get("contact", {}) or {}
    locales = cfg.get("localizations", {}) or {}
    listing = cfg.get("store_listing", {}) or {}
    perms = cfg.get("permissions", {}) or {}
    tracks = cfg.get("tracks", {}) or {}
    ds = cfg.get("data_safety", {}) or {}

    lines: list[str] = []
    lines.append(f"# Play-Console-Snapshot fuer "
                  f"`{ident.get('package_name', '?')}`")
    lines.append("")
    lines.append(f"Stand: {cfg.get('metadata', {}).get('generated_at', '-')}")
    lines.append("")
    lines.append("## Identitaet")
    lines.append("")
    lines.append("| Feld | Wert |")
    lines.append("| --- | --- |")
    lines.append(f"| App-Name | {ident.get('app_name', '-')} |")
    lines.append(f"| Package | `{ident.get('package_name', '-')}` |")
    lines.append(f"| Version | {ident.get('version_name', '-')} "
                  f"(code {ident.get('version_code', '-')}) |")
    lines.append(f"| Standard-Sprache | {ident.get('default_language', '-')} |")
    lines.append("")
    lines.append("## Kontakt / URLs")
    lines.append("")
    lines.append(f"- Support-E-Mail: `{contact.get('support_email', '-')}`")
    lines.append(f"- Support-URL:    {contact.get('support_url', '-')}")
    lines.append(f"- Marketing-URL:  {contact.get('marketing_url', '-')}")
    lines.append(f"- Datenschutz:    {contact.get('privacy_policy_url', '-')}")
    lines.append("")
    lines.append("## Lokalisierungen")
    lines.append("")
    for code, lc in locales.items():
        lines.append(f"### {code}")
        lines.append("")
        lines.append(f"- Titel: {lc.get('title', '-')} "
                      f"({len(lc.get('title', ''))}/30)")
        lines.append(f"- Kurz:  {lc.get('short_description', '-')} "
                      f"({len(lc.get('short_description', ''))}/80)")
        full = lc.get('full_description', '') or ''
        lines.append(f"- Lang:  {len(full)}/4000 Zeichen")
        lines.append("")
    lines.append("## Store-Listing")
    lines.append("")
    lines.append(f"- Kategorie: {listing.get('category', '-')}")
    lines.append(f"- Tags: {', '.join(listing.get('tags', []) or [])}")
    lines.append(f"- Werbung: {listing.get('ads_present', False)}")
    lines.append(f"- In-App-Kaeufe: {listing.get('in_app_purchases', False)}")
    lines.append("")
    lines.append("## Permissions")
    lines.append("")
    lines.append("Deklariert:")
    for p in perms.get("declared", []) or []:
        lines.append(f"  - {p}")
    lines.append("")
    lines.append("Blockiert (Datenschutz-Negativliste):")
    for p in perms.get("blocked", []) or []:
        lines.append(f"  - {p}")
    lines.append("")
    lines.append("## Data Safety")
    lines.append("")
    lines.append(f"- Daten gesammelt: {ds.get('data_collected', False)}")
    lines.append(f"- Daten geteilt:   {ds.get('data_shared', False)}")
    lines.append(f"- TLS in Transit:  {ds.get('encrypted_in_transit', False)}")
    lines.append(f"- Loeschen moeglich: "
                  f"{ds.get('users_can_request_deletion', False)}")
    lines.append("")
    if ds.get("types"):
        lines.append("### Datentypen")
        lines.append("")
        lines.append("| Typ | gesammelt | geteilt | Zweck | optional |")
        lines.append("| --- | :---: | :---: | --- | :---: |")
        for name, info in ds["types"].items():
            lines.append(
                f"| {name} | "
                f"{'x' if info.get('collected') else ''} | "
                f"{'x' if info.get('shared') else ''} | "
                f"{info.get('purpose', '-')} | "
                f"{'x' if info.get('optional') else ''} |")
        lines.append("")
    if ds.get("sdk_inventory"):
        lines.append("### SDK-Inventar")
        lines.append("")
        lines.append("| SDK | Datentypen | Zweck |")
        lines.append("| --- | --- | --- |")
        for sdk in ds["sdk_inventory"]:
            lines.append(
                f"| {sdk.get('name', '-')} | "
                f"{', '.join(sdk.get('data', []))} | "
                f"{sdk.get('purpose', '-')} |")
        lines.append("")
    lines.append("## Tracks")
    lines.append("")
    for name, info in tracks.items():
        rels = info.get("releases", []) or []
        lines.append(f"### {name}")
        lines.append("")
        lines.append(f"- {len(rels)} Release(s) konfiguriert")
        if info.get("tester_groups"):
            lines.append(f"- Tester-Gruppen: "
                          f"{', '.join(info['tester_groups'])}")
        for rel in rels:
            lines.append(
                f"  - v{rel.get('version_name','-')} "
                f"(code {rel.get('version_code','-')}, "
                f"status {rel.get('status','-')}, "
                f"rollout {rel.get('user_fraction','-')})")
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Generiert von `tools/playstore_sync.py`. "
                  "Aenderungen bitte ausschliesslich in `playstore.yml` "
                  "vornehmen und mit `python -m tools.playstore_sync push` "
                  "in die Play Console schieben.*")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _cmd_init(args: argparse.Namespace) -> int:
    yml = Path(args.config)
    if yml.is_file() and not args.force:
        print(f"[ABBRUCH] {yml} existiert bereits. Mit --force ueberschreiben.",
              file=sys.stderr)
        return 1
    cfg = init_from_repo()
    _dump_yaml(cfg, yml)
    print(f"Beispiel-YAML geschrieben: {yml}")
    print(f"  Package: {cfg['identity']['package_name']}")
    print(f"  Sprachen: {', '.join(cfg['localizations'].keys())}")
    issues = validate(cfg)
    errs = [i for i in issues if i.severity == "error"]
    if errs:
        print(f"[HINWEIS] {len(errs)} Pflichtfeld(er) sind noch leer "
              "- siehe 'validate'.")
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    cfg = _load_yaml(Path(args.config))
    issues = validate(cfg)
    if not issues:
        print("OK - Konfiguration ist gueltig.")
        return 0
    rc = 0
    for issue in issues:
        marker = "[ERR]" if issue.severity == "error" else "[WARN]"
        print(f"{marker} {issue.path}: {issue.message}")
        if issue.severity == "error":
            rc = 1
    return rc


def _cmd_pull(args: argparse.Namespace) -> int:
    cfg_local = _load_yaml(Path(args.config)) if Path(args.config).is_file() \
        else init_from_repo()
    backend = _resolve_backend(args)
    pkg = cfg_local.get("identity", {}).get("package_name") or args.package
    if not pkg:
        print("[FEHLER] Package-Name unbekannt. Erst 'init' ausfuehren.",
              file=sys.stderr)
        return 2
    remote = backend.pull(pkg)
    # metadata neu aufsetzen
    remote.setdefault("metadata", {})
    remote["metadata"]["generated_by"] = (
        f"playstore_sync pull ({backend.name})")
    remote["metadata"]["generated_at"] = datetime.now(timezone.utc).isoformat(
        timespec="seconds")
    if args.merge:
        merged = _merge(cfg_local, remote)
        _dump_yaml(merged, Path(args.config))
    else:
        _dump_yaml(remote, Path(args.config))
    print(f"Pull von {pkg} ueber Backend '{backend.name}' geschrieben "
          f"-> {args.config}")
    return 0


def _merge(local: dict, remote: dict) -> dict:
    """Tiefen-merge: lokale Werte bleiben, wo remote leer ist; sonst remote."""
    out: dict = deepcopy(local)
    for k, rv in remote.items():
        lv = out.get(k)
        if isinstance(rv, dict) and isinstance(lv, dict):
            out[k] = _merge(lv, rv)
        elif rv not in (None, "", [], {}):
            out[k] = rv
        else:
            out.setdefault(k, rv)
    return out


def _cmd_push(args: argparse.Namespace) -> int:
    cfg = _load_yaml(Path(args.config))
    issues = validate(cfg)
    errs = [i for i in issues if i.severity == "error"]
    if errs and not args.allow_invalid:
        print(f"[ABBRUCH] {len(errs)} Validierungsfehler. "
              "Push abgebrochen. Mit --allow-invalid erzwingen.",
              file=sys.stderr)
        for issue in issues:
            marker = "[ERR]" if issue.severity == "error" else "[WARN]"
            print(f"  {marker} {issue.path}: {issue.message}",
                  file=sys.stderr)
        return 1
    backend = _resolve_backend(args)
    pkg = cfg.get("identity", {}).get("package_name")
    actions = backend.push(pkg, cfg, dry_run=args.dry_run)
    label = "DRY-RUN" if args.dry_run else "PUSH"
    print(f"{label} ueber Backend '{backend.name}' fuer {pkg}:")
    for a in actions:
        print(f"  - {a}")
    return 0


def _cmd_diff(args: argparse.Namespace) -> int:
    cfg_local = _load_yaml(Path(args.config))
    backend = _resolve_backend(args)
    pkg = cfg_local.get("identity", {}).get("package_name")
    try:
        remote = backend.pull(pkg)
    except RuntimeError as exc:
        print(f"[INFO] {exc}", file=sys.stderr)
        remote = {}
    diffs = _diff_keys(remote, cfg_local)
    if not diffs:
        print("OK - keine Aenderungen (lokal == remote).")
        return 0
    print(f"{len(diffs)} Aenderung(en) zwischen Play Console "
          f"und {args.config}:")
    for line in diffs:
        print(f"  {line}")
    return 0


def _cmd_export(args: argparse.Namespace) -> int:
    cfg = _load_yaml(Path(args.config))
    out_path = Path(args.out) if args.out else REPO_ROOT / "release" / (
        f"playstore-snapshot-"
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.md")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(export_markdown(cfg), encoding="utf-8")
    print(f"Snapshot geschrieben: {out_path}")
    return 0


def _cmd_sample(args: argparse.Namespace) -> int:
    sys.stdout.write(_dump_str(SAMPLE_CONFIG))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="playstore_sync",
        description="Sync zwischen playstore.yml und der Google Play Console.")
    p.add_argument("--config", default=str(DEFAULT_YAML),
                    help="Pfad zur Konfigurations-YAML")
    p.add_argument("--credentials", default=None,
                    help="Service-Account-JSON (alternativ ENV "
                          "GOOGLE_PLAY_CREDENTIALS)")
    p.add_argument("--mock", action="store_true",
                    help="Erzwinge Mock-Backend (kein API-Aufruf)")
    p.add_argument("--mock-file", default=str(LOCAL_MIRROR),
                    help="Datei fuer den Mock-Spiegel")

    sub = p.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("init", help="Beispiel-YAML aus dem Repo erzeugen.")
    sp.add_argument("--force", action="store_true",
                     help="bestehende YAML ueberschreiben")
    sp.set_defaults(func=_cmd_init)

    sp = sub.add_parser("validate", help="YAML gegen Soll-Schema pruefen.")
    sp.set_defaults(func=_cmd_validate)

    sp = sub.add_parser("pull",
                          help="Live-Stand aus Play Console in YAML schreiben.")
    sp.add_argument("--package", default=None,
                     help="Paketname (falls noch nicht in der YAML)")
    sp.add_argument("--merge", action="store_true",
                     help="Bestehende lokale Werte beibehalten, wenn remote "
                          "leer ist.")
    sp.set_defaults(func=_cmd_pull)

    sp = sub.add_parser("push", help="YAML in die Play Console schieben.")
    sp.add_argument("--dry-run", action="store_true",
                     help="Nur anzeigen, was passieren wuerde.")
    sp.add_argument("--allow-invalid", action="store_true",
                     help="Auch mit Validierungsfehlern pushen.")
    sp.set_defaults(func=_cmd_push)

    sp = sub.add_parser("diff",
                          help="Aenderungen zwischen YAML und Play Console.")
    sp.set_defaults(func=_cmd_diff)

    sp = sub.add_parser("export",
                          help="Markdown-Snapshot in release/ erzeugen.")
    sp.add_argument("--out", default=None,
                     help="Zielpfad fuer den Snapshot")
    sp.set_defaults(func=_cmd_export)

    sp = sub.add_parser("sample",
                          help="Beispiel-Konfiguration nach stdout schreiben.")
    sp.set_defaults(func=_cmd_sample)
    return p


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
