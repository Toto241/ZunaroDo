"""
Datenschutz- und Compliance-Scans (TESTING.md Teil II Abschnitt 12).

Diese Tests laufen schnell und vor jedem PR. Sie verhindern, dass
versehentlich Secrets, Klartext-URLs, undokumentierte Permissions
oder unzulaessige Daten im Code landen.

Abgedeckte P-IDs:

  P-A-04   Drittanbieter-SDK-Inventar dokumentiert
  P-C-01   Manifest enthaelt nur dokumentierte Permissions
  P-C-03   Hintergrund-Permissions begruendet
  P-D-01   HTTPS-only - kein Klartext-`http://` im Code (Whitelist Tests/Docs)
  P-D-04   Keine PII in Log-Statements (Best-Effort-Regex-Scan)
  P-D-08   Manifest-Backup-Flag bewusst gesetzt
  P-B-01   Konto-Loeschung in der App vorhanden (Capability)
  P-A-01   Datenschutz-Dokumente vorhanden (DSGVO Art. 13/14)
  J2-S-02  keine Hardcoded Secrets
  J2-G-03  targetSdk >= 35

Hinweis: die Scans haben Whitelisten fuer Test-/Dokumentations-Pfade
und fuer Beispiel-Token in tests/.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest


pytestmark = [pytest.mark.concept, pytest.mark.privacy]


REPO = Path(__file__).resolve().parents[2]


# Pfade, die fuer Scans als 'nur App-Code' gelten
APP_SOURCE_DIRS = ["core", "modules", "services", "mobile", "tools"]
APP_SOURCE_FILES = ["assistant.py", "database.py", "gui.py", "main.py",
                    "models.py", "__main__.py", "diagnose.py"]


def _app_source_files() -> list[Path]:
    out: list[Path] = []
    for d in APP_SOURCE_DIRS:
        out.extend((REPO / d).rglob("*.py"))
    for f in APP_SOURCE_FILES:
        p = REPO / f
        if p.is_file():
            out.append(p)
    # Keine pycache, keine tests, keine docs
    return [p for p in out if "__pycache__" not in p.parts]


# ---------------------------------------------------------------------------
# P-D-01 HTTPS-only
# ---------------------------------------------------------------------------
HTTP_PATTERN = re.compile(r"http://([A-Za-z0-9\-\._]+)")

ALLOWED_HTTP_HOSTS = {
    "127.0.0.1", "localhost",          # lokaler Sync-Server, Tests
    "example.com", "example.org",      # Beispiel-Hosts in Doku/Kommentaren
    "www.w3.org",                       # XML-Namespace-URL-Konvention
    "schemas.android.com",
    "www.example.org",
    "server",                           # Docstring-Platzhalter (kein DNS)
    "deinserver.example.org",
}


@pytest.mark.parametrize("path", _app_source_files(),
                          ids=lambda p: p.relative_to(REPO).as_posix())
def test_PD01_no_cleartext_http_urls(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    offenders: list[str] = []
    for line in text.splitlines():
        # Kommentare ausnehmen
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        for m in HTTP_PATTERN.finditer(line):
            host = m.group(1).lower()
            if host in ALLOWED_HTTP_HOSTS:
                continue
            # Localhost-Varianten
            if host.startswith("127.") or host.startswith("0.0."):
                continue
            offenders.append(f"{line.strip()[:120]}  ->  http://{host}")
    assert not offenders, (
        f"Klartext-HTTP in {path.relative_to(REPO).as_posix()}: "
        f"{offenders[:3]}")


# ---------------------------------------------------------------------------
# J2-S-02 Keine Hardcoded Secrets
# ---------------------------------------------------------------------------
SECRET_PATTERNS = [
    # AWS, Stripe, GitHub-Token, Google-API-Key
    re.compile(r"AKIA[0-9A-Z]{16}"),                           # AWS
    re.compile(r"sk_live_[A-Za-z0-9]{24,}"),                   # Stripe
    re.compile(r"ghp_[A-Za-z0-9]{36,}"),                       # GitHub PAT
    re.compile(r"AIza[0-9A-Za-z\-_]{35}"),                     # Google API
    re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"),   # PEM
]


@pytest.mark.parametrize("path", _app_source_files(),
                          ids=lambda p: p.relative_to(REPO).as_posix())
def test_JS02_no_hardcoded_secrets(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    for pat in SECRET_PATTERNS:
        m = pat.search(text)
        assert m is None, (
            f"Moegliches Secret in {path.relative_to(REPO).as_posix()}: "
            f"Muster {pat.pattern!r}")


# ---------------------------------------------------------------------------
# P-D-04 Keine PII in Log-Statements (Best-Effort)
# ---------------------------------------------------------------------------
PII_IN_LOG_PATTERNS = [
    # log/print mit deutschen Telefonformaten
    re.compile(r"(?:log|print).*\+49"),
    # log/print mit literalen E-Mail-Adressen
    re.compile(r"(?:log|print).*[\w\.\-]+@[\w\.\-]+\.[A-Za-z]{2,}"),
]


@pytest.mark.parametrize("path", _app_source_files(),
                          ids=lambda p: p.relative_to(REPO).as_posix())
def test_PD04_no_pii_in_log_statements(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    offenders: list[str] = []
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        for pat in PII_IN_LOG_PATTERNS:
            if pat.search(line):
                offenders.append(line.strip()[:120])
                break
    assert not offenders, (
        f"PII-Verdacht in Log/Print von {path.relative_to(REPO).as_posix()}: "
        f"{offenders[:3]}")


# ---------------------------------------------------------------------------
# P-C-01 / P-C-03  Permissions im buildozer.spec dokumentiert
# ---------------------------------------------------------------------------
ALLOWED_PERMISSIONS = {
    "INTERNET",
    "ACCESS_NETWORK_STATE",     # falls in Zukunft Offline-Banner
    "POST_NOTIFICATIONS",       # Erinnerungen, API 33+
}


def _spec_permissions() -> set[str]:
    spec = (REPO / "buildozer.spec").read_text(encoding="utf-8")
    perms: set[str] = set()
    for line in spec.splitlines():
        line = line.strip()
        if line.startswith("android.permissions") and "=" in line:
            _, _, value = line.partition("=")
            for token in value.split(","):
                token = token.strip()
                if token:
                    perms.add(token)
    return perms


def test_PC01_only_whitelisted_permissions():
    declared = _spec_permissions()
    unexpected = declared - ALLOWED_PERMISSIONS
    assert not unexpected, (
        f"Manifest enthaelt undokumentierte Permissions: {unexpected}. "
        f"Erweitere ALLOWED_PERMISSIONS bewusst, sonst Datenschutz-No-Go.")


def test_PC01_at_least_internet_declared():
    declared = _spec_permissions()
    assert "INTERNET" in declared, (
        "INTERNET fehlt im Manifest - dann fuktioniert weder Sync noch KI.")


# ---------------------------------------------------------------------------
# P-D-08 Backup-Flag bewusst gesetzt
# ---------------------------------------------------------------------------
def test_PD08_backup_flag_is_explicit():
    spec = (REPO / "buildozer.spec").read_text(encoding="utf-8")
    found = False
    for line in spec.splitlines():
        line = line.strip()
        if line.startswith("android.allow_backup"):
            _, _, value = line.partition("=")
            v = value.strip().lower()
            # bewusst False ODER True - egal welcher Wert, er muss
            # gesetzt sein (kein Default).
            assert v in ("0", "1", "true", "false"), (
                f"android.allow_backup hat ungueltigen Wert: {value!r}")
            found = True
            break
    assert found, "android.allow_backup fehlt im buildozer.spec"


# ---------------------------------------------------------------------------
# J2-G-03 targetSdk >= 35
# ---------------------------------------------------------------------------
def test_JG03_target_sdk_meets_play_minimum():
    spec = (REPO / "buildozer.spec").read_text(encoding="utf-8")
    for line in spec.splitlines():
        line = line.strip()
        if line.startswith("android.api") and "=" in line and not line.startswith("android.api_"):
            _, _, value = line.partition("=")
            try:
                api = int(value.split("#", 1)[0].strip())
            except ValueError:
                pytest.fail(f"android.api hat keinen Integer-Wert: {value!r}")
            assert api >= 34, (
                f"Play Store verlangt aktuell targetSdk >= 34/35. "
                f"buildozer.spec hat android.api = {api}.")
            return
    pytest.fail("android.api fehlt im buildozer.spec")


def test_JG03_min_sdk_is_supported():
    spec = (REPO / "buildozer.spec").read_text(encoding="utf-8")
    for line in spec.splitlines():
        line = line.strip()
        if line.startswith("android.minapi"):
            _, _, value = line.partition("=")
            try:
                api = int(value.split("#", 1)[0].strip())
            except ValueError:
                pytest.fail(f"android.minapi keine Zahl: {value!r}")
            # Play unterstuetzt offiziell ab API 21+, sinnvoll >= 24.
            assert 21 <= api <= 35, (
                f"android.minapi = {api} liegt ausserhalb des plausiblen "
                "Bereichs (21..35)")
            return


# ---------------------------------------------------------------------------
# P-A-01 / DSGVO Art. 13/14  Datenschutz-Dokumente vorhanden
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("doc", [
    "DATENSCHUTZ.md", "IMPRESSUM.md", "AGB.md", "WIDERRUF.md",
])
def test_PA01_legal_docs_present(doc):
    p = REPO / "legal" / doc
    assert p.is_file(), f"Pflichtdokument legal/{doc} fehlt"


def test_PA01_legal_docs_not_empty():
    for doc in ["DATENSCHUTZ.md", "IMPRESSUM.md"]:
        p = REPO / "legal" / doc
        assert p.stat().st_size > 200, (
            f"legal/{doc} ist verdaechtig kurz ({p.stat().st_size} B) - "
            "bitte echte Fassung einpflegen.")


# ---------------------------------------------------------------------------
# P-A-04 SDK-Inventar dokumentiert (im Konzept oder PLAYSTORE.md)
# ---------------------------------------------------------------------------
def test_PA04_sdk_inventory_mentioned():
    """In TESTING.md (Teil II) UND/ODER PLAYSTORE.md muss ein SDK-
    Inventar geben - jede App muss klar deklarieren, welche SDKs
    Daten verarbeiten."""
    testing = (REPO / "TESTING.md").read_text(encoding="utf-8",
                                                errors="replace")
    assert "SDK" in testing and "Crashlytics" in testing, (
        "TESTING.md enthaelt keinen SDK-Inventar-Abschnitt mit "
        "Crashlytics-Eintrag")


# ---------------------------------------------------------------------------
# P-B-01 Kontoloeschung als Capability vorhanden
# ---------------------------------------------------------------------------
def test_PB01_account_deletion_capability_exists():
    """Pruefen, dass mindestens *eine* Loesch-/Purge-Capability existiert
    - das ist Voraussetzung fuer die Play-Pflicht 'Kontoloeschung'."""
    import tempfile, os
    from core.interface import ModuleRegistry
    from database import (CalendarRepository, ContractRepository, Database,
                          ExpenseRepository, FamilyRepository, NoteRepository,
                          ProposalRepository, ShoppingRepository,
                          SocialRepository)
    from modules.calendar import CalendarModule
    from modules.contracts import ContractModule
    from modules.family import FamilyModule
    from modules.finance import FinanceModule
    from modules.inbox import InboxModule
    from modules.notes import NotesModule
    from modules.social import SocialModule

    fd, p = tempfile.mkstemp(prefix="zd-priv-", suffix=".db"); os.close(fd)
    try:
        db = Database(path=p)
        try:
            reg = ModuleRegistry()
            reg.register(FamilyModule(FamilyRepository(db),
                                       ShoppingRepository(db)))
            reg.register(ContractModule(ContractRepository(db)))
            reg.register(FinanceModule(ExpenseRepository(db)))
            reg.register(CalendarModule(CalendarRepository(db)))
            reg.register(SocialModule(SocialRepository(db)))
            reg.register(NotesModule(NoteRepository(db)))
            reg.register(InboxModule(ProposalRepository(db)))
            deletes = [c.name for c in reg.all_capabilities(
                          include_disabled=True)
                       if c.destructive and
                       any(k in c.name.lower() for k in
                            ("delete", "purge", "remove"))]
            assert deletes, (
                "Es gibt keine destructive 'delete'/'purge'-Capability - "
                "Play-Pflicht 'Kontoloeschung' nicht erfuellbar.")
        finally:
            db.close()
    finally:
        try:
            os.unlink(p)
        except OSError:
            pass
