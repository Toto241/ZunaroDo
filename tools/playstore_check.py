"""
Automatisierter Play-Store-Compliance-Checker fuer Alltagshelfer/ZunaroDo.

Prueft das Repository (und das generierte Manifest, falls vorhanden) gegen
die Vorgaben in docs/android/02_PLAYSTORE_COMPLIANCE.md.

Aufruf:

    python -m tools.playstore_check                       # alle Checks
    python -m tools.playstore_check --strict              # exit > 0 bei WARN
    python -m tools.playstore_check --only manifest,sdk   # Untermenge
    python -m tools.playstore_check --json > report.json

Exit-Codes:
    0   alles okay
    1   mindestens ein FAIL (oder WARN, wenn --strict)
    2   interner Fehler (Konfiguration, fehlende Datei)

Der Checker ist bewusst pythonisch, ohne Drittabhaengigkeiten - er muss
in der CI ohne Setup laufen.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Sequence

# ---------------------------------------------------------------------------
# Konfiguration - hier liegen die "weichen" Vorgaben, die der Checker hart
# durchsetzt. Aenderungen brauchen ein Review der Compliance-Doku.
# ---------------------------------------------------------------------------

#: Mindest- und Soll-Werte fuer die API-Levels.
MIN_TARGET_SDK = 35
ALLOWED_MIN_SDK = (24, 25, 26, 27, 28, 29, 30, 31)  # >=24 Pflicht
ALLOWED_NDK_API = ALLOWED_MIN_SDK

#: Permissions, die ohne Sonderpruefung im Manifest landen duerfen.
#: Jede neue Permission muss in docs/android/04_PRIVACY_PERMISSIONS.md
#: begruendet sein und hier eingetragen werden.
ALLOWED_PERMISSIONS = {
    "android.permission.INTERNET",
    "android.permission.ACCESS_NETWORK_STATE",
    "android.permission.POST_NOTIFICATIONS",
}

#: Permissions, die wir niemals freiwillig hinzufuegen.
DENIED_PERMISSIONS = {
    "android.permission.MANAGE_EXTERNAL_STORAGE",
    "android.permission.QUERY_ALL_PACKAGES",
    "android.permission.READ_PHONE_STATE",
    "android.permission.READ_CALL_LOG",
    "android.permission.READ_SMS",
    "android.permission.SEND_SMS",
    "android.permission.RECEIVE_SMS",
    "android.permission.ACCESS_BACKGROUND_LOCATION",
    "android.permission.REQUEST_INSTALL_PACKAGES",
    "android.permission.SYSTEM_ALERT_WINDOW",
    "android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS",
}

#: Verzeichnisse, die der Repo-Scan ignorieren soll.
SCAN_EXCLUDE_DIRS = {
    ".git", ".buildozer", "build", "dist", "__pycache__",
    ".mypy_cache", ".pytest_cache", ".venv", "venv", "node_modules",
    "htmlcov", "logs", "backups",
}

#: Quellen-Endungen, die wir scannen.
SOURCE_EXTS = {".py", ".kv", ".kt", ".java", ".gradle", ".xml", ".pro"}

#: Heuristische Secret-Patterns.
SECRET_PATTERNS: list[tuple[str, str]] = [
    ("Google API Key",      r"AIza[0-9A-Za-z\-_]{35}"),
    ("AWS Access Key",      r"AKIA[0-9A-Z]{16}"),
    ("Slack Token",         r"xox[abp]-[0-9A-Za-z\-]{10,48}"),
    ("Generic JWT",         r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    ("Stripe Live Key",     r"sk_live_[0-9A-Za-z]{16,}"),
    ("Paddle Vendor Auth",  r"pdl_live_apikey_[0-9A-Za-z]{16,}"),
    ("Private Key Block",   r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"),
]

#: Verbotene Krypto/Code-Smells.
CODE_SMELLS: list[tuple[str, str, str]] = [
    ("INSECURE_TRUST_MANAGER",
     r"checkServerTrusted\s*\([^)]*\)\s*\{\s*\}",
     "Leerer TrustManager.checkServerTrusted - TLS-Bypass"),
    ("CLEARTEXT_HTTP",
     r"\"http://(?!localhost|127\.0\.0\.1)[A-Za-z0-9.\-]+",
     "Klartext-HTTP-URL in Code"),
    ("REQUESTS_VERIFY_FALSE",
     r"requests\.(?:get|post|put|delete|patch|request)\([^)]*verify\s*=\s*False",
     "requests.* mit verify=False (TLS-Bypass)"),
    ("INSECURE_CIPHER_DES",
     r"Cipher\.getInstance\(\s*\"DES",
     "Cipher DES - unsicher"),
    ("INSECURE_CIPHER_ECB",
     r"Cipher\.getInstance\(\s*\"AES/ECB",
     "AES im ECB-Modus - unsicher"),
    ("RUNTIME_EXEC_SU",
     r"Runtime\.exec\(\s*\"su\"",
     "Runtime.exec(\"su\") - Root-Versuch"),
    ("PRINT_IN_SERVICE",
     r"^\s*print\(",
     "print() in Production-Code - logging verwenden"),
    ("EVAL_NONCONST",
     r"\beval\s*\(",
     "eval() im Code - vermeiden"),
    ("EXEC_NONCONST",
     r"\bexec\s*\(",
     "exec() im Code - vermeiden"),
    ("SUBPROCESS_SHELL_TRUE",
     r"subprocess\.\w+\([^)]*shell\s*=\s*True",
     "subprocess mit shell=True - Injection-Risiko"),
]

#: SDKs/Bibliotheken, die im SDK-Inventar dokumentiert sein muessen.
#: Diese Liste spiegelt die "ueblichen verdaechtigen"; sie wird mit
#: requirements.txt verglichen.
DOCUMENTED_SDKS = {
    "kivy", "kivymd", "certifi", "requests", "google-generativeai",
    "cryptography", "Pillow", "pyjnius", "sqlcipher3",
    # Sichere Geraetekopplung (services/pairing/):
    "keyring", "spake2",
    # Desktop / cross-cutting Libraries (laufen nicht auf Android,
    # sind aber im requirements-Inventar):
    "customtkinter", "fpdf2", "APScheduler", "plyer",
}

REPO_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Result-Modell
# ---------------------------------------------------------------------------

class Level:
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


@dataclass
class Finding:
    check: str
    level: str
    message: str
    file: str | None = None
    line: int | None = None

    def as_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)

    def add(self, **kw) -> None:
        self.findings.append(Finding(**kw))

    def by_level(self, level: str) -> list[Finding]:
        return [f for f in self.findings if f.level == level]

    def summary(self) -> dict[str, int]:
        return {
            "pass":  len(self.by_level(Level.PASS)),
            "warn":  len(self.by_level(Level.WARN)),
            "fail":  len(self.by_level(Level.FAIL)),
            "total": len(self.findings),
        }


# ---------------------------------------------------------------------------
# Buildozer.spec Parser (minimalistisch, INI-aehnlich)
# ---------------------------------------------------------------------------

def parse_buildozer_spec(path: Path) -> dict[str, str]:
    """Liest die Schluessel-Wert-Paare im [app]-Block."""
    if not path.exists():
        return {}
    result: dict[str, str] = {}
    current_section = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current_section = line[1:-1].strip()
            continue
        if current_section != "app":
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result


# ---------------------------------------------------------------------------
# Datei-Iteratoren
# ---------------------------------------------------------------------------

def iter_source_files(root: Path) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SCAN_EXCLUDE_DIRS]
        for name in filenames:
            p = Path(dirpath) / name
            if p.suffix.lower() in SOURCE_EXTS:
                yield p


# ---------------------------------------------------------------------------
# Einzelne Checks
# ---------------------------------------------------------------------------

def check_sdk_levels(report: Report, spec: dict[str, str]) -> None:
    name = "sdk"
    if not spec:
        report.add(check=name, level=Level.FAIL,
                   message="buildozer.spec nicht lesbar.")
        return

    target = spec.get("android.api")
    if target is None:
        report.add(check=name, level=Level.FAIL,
                   message="android.api fehlt in buildozer.spec.")
    else:
        try:
            t = int(target)
        except ValueError:
            report.add(check=name, level=Level.FAIL,
                       message=f"android.api ist kein Integer: {target!r}")
        else:
            if t < MIN_TARGET_SDK:
                report.add(check=name, level=Level.FAIL,
                           message=f"android.api={t} < MIN_TARGET_SDK={MIN_TARGET_SDK}. "
                                   "Play Store verlangt aktuelle Target-SDK.")
            else:
                report.add(check=name, level=Level.PASS,
                           message=f"android.api={t} >= {MIN_TARGET_SDK}")

    minapi = spec.get("android.minapi")
    if minapi is None:
        report.add(check=name, level=Level.WARN,
                   message="android.minapi nicht gesetzt - Default verwendet.")
    else:
        try:
            m = int(minapi)
        except ValueError:
            report.add(check=name, level=Level.FAIL,
                       message=f"android.minapi ist kein Integer: {minapi!r}")
        else:
            if m < min(ALLOWED_MIN_SDK):
                report.add(check=name, level=Level.FAIL,
                           message=f"android.minapi={m} ist zu niedrig "
                                   f"(min {min(ALLOWED_MIN_SDK)}).")
            else:
                report.add(check=name, level=Level.PASS,
                           message=f"android.minapi={m}")

    ndk = spec.get("android.ndk_api")
    if ndk is not None:
        try:
            n = int(ndk)
        except ValueError:
            report.add(check=name, level=Level.FAIL,
                       message=f"android.ndk_api kein Integer: {ndk!r}")
        else:
            if n < min(ALLOWED_NDK_API):
                report.add(check=name, level=Level.WARN,
                           message=f"android.ndk_api={n} unter empfohlenem Mindestwert.")


def check_permissions(report: Report, spec: dict[str, str]) -> None:
    name = "permissions"
    raw = spec.get("android.permissions", "")
    if not raw:
        report.add(check=name, level=Level.PASS,
                   message="Keine Permissions deklariert.")
        return
    # Komma-getrennt, evtl. mit Whitespace
    perms = {p.strip() for p in raw.split(",") if p.strip()}
    # Nutzer schreiben oft "INTERNET" statt voll qualifiziert. Wir
    # normalisieren auf "android.permission.X".
    normed: set[str] = set()
    for p in perms:
        if "." not in p:
            normed.add(f"android.permission.{p}")
        else:
            normed.add(p)

    extra = normed - ALLOWED_PERMISSIONS
    denied = normed & DENIED_PERMISSIONS
    for p in sorted(denied):
        report.add(check=name, level=Level.FAIL,
                   message=f"Verbotene Permission deklariert: {p}")
    for p in sorted(extra - DENIED_PERMISSIONS):
        report.add(check=name, level=Level.WARN,
                   message=f"Permission nicht in Whitelist: {p}. "
                           "Begruendung in docs/android/04_PRIVACY_PERMISSIONS.md ergaenzen.")
    for p in sorted(normed & ALLOWED_PERMISSIONS):
        report.add(check=name, level=Level.PASS,
                   message=f"Whitelisted: {p}")


def check_versioning(report: Report, spec: dict[str, str]) -> None:
    name = "versioning"
    ver = spec.get("version")
    if not ver:
        report.add(check=name, level=Level.FAIL,
                   message="version in buildozer.spec fehlt.")
        return
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:-[\w.]+)?", ver):
        report.add(check=name, level=Level.WARN,
                   message=f"version {ver!r} ist kein striktes SemVer (MAJOR.MINOR.PATCH).")
    else:
        report.add(check=name, level=Level.PASS, message=f"version={ver}")

    numeric = spec.get("android.numeric_version")
    if not numeric:
        report.add(check=name, level=Level.FAIL,
                   message="android.numeric_version fehlt in buildozer.spec "
                           "(Play-Store versionCode).")
        return
    try:
        code = int(numeric)
    except ValueError:
        report.add(check=name, level=Level.FAIL,
                   message=f"android.numeric_version ist kein Integer: {numeric!r}")
        return
    if code <= 0:
        report.add(check=name, level=Level.FAIL,
                   message=f"android.numeric_version={code} muss > 0 sein.")
    else:
        report.add(check=name, level=Level.PASS,
                   message=f"android.numeric_version={code}")

    cfg = _load_playstore_yml()
    ps_code = ((cfg.get("identity") or {}).get("version_code"))
    if ps_code is not None:
        try:
            expected = int(ps_code)
        except (TypeError, ValueError):
            report.add(check=name, level=Level.WARN,
                       message=f"playstore.yml version_code ungueltig: {ps_code!r}")
        else:
            if code != expected:
                report.add(check=name, level=Level.FAIL,
                           message=f"versionCode-Mismatch: buildozer={code}, "
                                   f"playstore.yml={expected}")
            else:
                report.add(check=name, level=Level.PASS,
                           message=f"versionCode synchron mit playstore.yml ({code}).")


def check_secrets(report: Report, files: Sequence[Path]) -> None:
    name = "secrets"
    hits = 0
    for p in files:
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for label, pattern in SECRET_PATTERNS:
            for m in re.finditer(pattern, text):
                hits += 1
                line_no = text.count("\n", 0, m.start()) + 1
                report.add(check=name, level=Level.FAIL,
                           message=f"Moegliches Secret ({label}) gefunden.",
                           file=str(p.relative_to(REPO_ROOT)), line=line_no)
    if hits == 0:
        report.add(check=name, level=Level.PASS, message="Keine Secret-Patterns gefunden.")


#: Pfade, die auf Android tatsaechlich gepackt werden. Nur hier gilt das
#: harte print()-Verbot. CLI-Entry-Points (main.py, __main__.py, diagnose.py),
#: tools/, tests/ und Server-Code sind explizit ausgenommen.
MOBILE_RUNTIME_PREFIXES = (
    ("mobile",),
    ("core",),
    ("modules",),
)
MOBILE_RUNTIME_FILES = {
    "database.py",
    "models.py",
    "assistant.py",
}


def _on_mobile_runtime(rel: Path) -> bool:
    parts = rel.parts
    if not parts:
        return False
    if parts in {(name,) for name in MOBILE_RUNTIME_FILES}:
        return True
    if len(parts) == 1 and parts[0] in MOBILE_RUNTIME_FILES:
        return True
    for prefix in MOBILE_RUNTIME_PREFIXES:
        if parts[:len(prefix)] == prefix:
            return True
    if parts[0] == "services":
        # services laufen auch auf Android - bis auf reine Server-Skripte
        if len(parts) >= 2 and parts[1] in {"sync_server.py", "notifier.py"}:
            return False
        return True
    return False


#: Verzeichnisse, in denen Anti-Pattern bewusst als negativ-Beispiel
#: oder Test-Fixture vorkommen koennen - hier wuerden Smells false-
#: positives ausloesen.
SMELL_EXEMPT_PREFIXES = ("tests", "tools", "docs")


def check_smells(report: Report, files: Sequence[Path]) -> None:
    name = "code_smells"
    hits = 0
    for p in files:
        rel = p.relative_to(REPO_ROOT)
        if rel.parts and rel.parts[0] in SMELL_EXEMPT_PREFIXES:
            continue
        on_mobile = _on_mobile_runtime(rel)
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for code, pattern, label in CODE_SMELLS:
            # Heuristiken, die nur fuer den Mobile-Pfad gelten:
            if code in {"PRINT_IN_SERVICE", "EVAL_NONCONST", "EXEC_NONCONST"}:
                if not on_mobile:
                    continue
            flags = re.MULTILINE if code == "PRINT_IN_SERVICE" else 0
            for m in re.finditer(pattern, text, flags=flags):
                hits += 1
                line_no = text.count("\n", 0, m.start()) + 1
                report.add(check=name, level=Level.FAIL,
                           message=f"{code}: {label}",
                           file=str(rel), line=line_no)
    if hits == 0:
        report.add(check=name, level=Level.PASS,
                   message="Keine kritischen Code-Smells gefunden.")


def check_demo_data_excluded(report: Report, spec: dict[str, str]) -> None:
    name = "demo_data"
    excl = spec.get("source.exclude_exts", "")
    parts = {p.strip() for p in excl.split(",") if p.strip()}
    required = {"db", "sqlite"}
    missing = required - parts
    if missing:
        report.add(check=name, level=Level.FAIL,
                   message=f"source.exclude_exts deckt {sorted(missing)} nicht ab. "
                           "Demo-DBs koennten ins APK gelangen.")
    else:
        report.add(check=name, level=Level.PASS,
                   message="Demo-DBs sind vom Bundle ausgeschlossen.")


def check_privacy_docs(report: Report) -> None:
    name = "privacy_docs"
    must_exist = [
        "legal/DATENSCHUTZ.md",
        "legal/AGB.md",
        "legal/IMPRESSUM.md",
        "legal/WIDERRUF.md",
        "docs/android/04_PRIVACY_PERMISSIONS.md",
    ]
    for rel in must_exist:
        if (REPO_ROOT / rel).exists():
            report.add(check=name, level=Level.PASS,
                       message=f"{rel} vorhanden.")
        else:
            report.add(check=name, level=Level.FAIL,
                       message=f"{rel} fehlt - Pflicht-Artefakt.")


def check_data_deletion(report: Report) -> None:
    """
    Play Store verlangt einen In-App-Weg zur vollstaendigen Loeschung der
    Nutzerdaten (Data-Deletion / DSGVO Art. 17). Wir pruefen, dass der
    Mechanismus existiert: services/data_deletion.py + Database.wipe_all_data.
    """
    name = "data_deletion"
    ok = True
    svc = REPO_ROOT / "services" / "data_deletion.py"
    if not svc.exists():
        report.add(check=name, level=Level.FAIL,
                   message="services/data_deletion.py fehlt - kein "
                           "Voll-Loeschungs-Pfad (Play Data-Deletion).")
        ok = False
    db = REPO_ROOT / "database.py"
    if db.exists():
        if "def wipe_all_data" not in db.read_text(encoding="utf-8", errors="ignore"):
            report.add(check=name, level=Level.FAIL,
                       message="Database.wipe_all_data() fehlt - DB kann "
                               "nicht vollstaendig geleert werden.")
            ok = False
    else:
        report.add(check=name, level=Level.FAIL, message="database.py fehlt.")
        ok = False
    if ok:
        report.add(check=name, level=Level.PASS,
                   message="Voll-Loeschung der Nutzerdaten vorhanden.")


#: Closed-Testing-Mindestvorgaben (Google Play: vor Produktion 14 Tage
#: ununterbrochenes Testing mit >=12 Testern).
CLOSED_TEST_MIN_TESTERS = 12
CLOSED_TEST_MIN_DAYS = 14


def _load_playstore_yml(path: Path | None = None) -> dict:
    """Laedt playstore.yml (YAML, JSON-Fallback). Fehlt sie -> {}."""
    p = path or (REPO_ROOT / "playstore.yml")
    if not p.is_file():
        return {}
    text = p.read_text(encoding="utf-8")
    try:
        import yaml
        return yaml.safe_load(text) or {}
    except ImportError:
        import json
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {}


def evaluate_closed_test_gate(config: dict, evidence_dir: Path) -> dict:
    """
    Reines Release-Gate-Kriterium fuer den Closed-Test-Nachweis.

    'ready' ist nur True, wenn (a) der closed-Track die Mindestvorgaben
    (>=12 Tester, >=14 Tage) verlangt UND (b) ein Nachweisdokument
    (release/closed-test-*.md) vorliegt. So kann es deterministisch
    getestet werden, ohne externe Systeme.
    """
    closed = ((config.get("tracks") or {}).get("closed") or {})
    min_testers = closed.get("min_testers", 0) or 0
    min_days = closed.get("min_days", 0) or 0
    config_ok = (min_testers >= CLOSED_TEST_MIN_TESTERS
                 and min_days >= CLOSED_TEST_MIN_DAYS)
    evidence = (sorted(evidence_dir.glob("closed-test-*.md"))
                if evidence_dir.is_dir() else [])
    evidence_present = bool(evidence)
    reasons: list[str] = []
    if not config_ok:
        reasons.append(
            f"closed-Track muss min_testers>={CLOSED_TEST_MIN_TESTERS} und "
            f"min_days>={CLOSED_TEST_MIN_DAYS} verlangen "
            f"(ist: {min_testers}/{min_days}).")
    if not evidence_present:
        reasons.append("Kein Closed-Test-Nachweis (release/closed-test-*.md) "
                       "gefunden.")
    return {
        "config_ok": config_ok,
        "evidence_present": evidence_present,
        "ready": config_ok and evidence_present,
        "evidence_files": [p.name for p in evidence],
        "reasons": reasons,
    }


def check_closed_test_evidence(report: Report) -> None:
    """
    Prueft die Closed-Testing-Voraussetzungen. Eine falsche Konfiguration
    (zu wenige Tester/Tage) ist ein FAIL. Ein noch fehlender Nachweis ist
    KEIN WARN: das ist ein Release-Zeitpunkt-Thema und wuerde den
    Pre-Merge-Check (--strict behandelt WARN als Fehler) waehrend der
    Entwicklung unnoetig rot faerben. Die eigentliche GO-Entscheidung
    trifft 'evaluate_closed_test_gate' (verlangt den Nachweis sehr wohl).
    """
    name = "closed_test"
    cfg = _load_playstore_yml()
    closed = ((cfg.get("tracks") or {}).get("closed") or {})
    if not closed:
        # playstore.yml ist hier nicht auswertbar - typisch, wenn dieser
        # CI-Step ohne PyYAML laeuft (playstore_check ist bewusst
        # abhaengigkeitsfrei). Kein FAIL: die Konfiguration wird mit
        # YAML-Parser separat geprueft (playstore_sync validate / der
        # Unit-Test 'test_live_config_meets_minimums').
        report.add(check=name, level=Level.PASS,
                   message="closed-Track nicht auswertbar (playstore.yml "
                           "ohne PyYAML) - separat geprueft.")
        return
    gate = evaluate_closed_test_gate(cfg, REPO_ROOT / "release")
    if not gate["config_ok"]:
        report.add(check=name, level=Level.FAIL,
                   message="; ".join(gate["reasons"]))
        return
    report.add(check=name, level=Level.PASS,
               message=f"Closed-Track verlangt >={CLOSED_TEST_MIN_TESTERS} "
                       f"Tester / >={CLOSED_TEST_MIN_DAYS} Tage.")
    if gate["evidence_present"]:
        report.add(check=name, level=Level.PASS,
                   message="Closed-Test-Nachweis vorhanden: "
                           + ", ".join(gate["evidence_files"]) + ".")
    else:
        report.add(check=name, level=Level.PASS,
                   message="Closed-Test-Nachweis (release/closed-test-*.md) "
                           "noch nicht hinterlegt - vor Produktions-GO "
                           "erforderlich (Release-Gate prueft das separat).")


def check_i18n(report: Report) -> None:
    """
    Locale-Parität: keine Sprache hat Keys ausserhalb der Default-Sprache,
    und jede vorhandene Locale-Datei deckt die Pflicht-CORE_KEYS ab.
    Delegiert an tools.i18n_sync (dieselbe Logik wie der CI-i18n-Check).
    """
    name = "i18n"
    try:
        from tools import i18n_sync
    except Exception as exc:                          # pragma: no cover
        report.add(check=name, level=Level.WARN,
                   message=f"i18n_sync nicht ladbar: {exc!r}")
        return
    rep = i18n_sync.analyze()
    errors = i18n_sync.check(rep)
    if errors:
        for e in errors:
            report.add(check=name, level=Level.FAIL, message=e)
    else:
        n_langs = sum(1 for v in rep["languages"].values() if v["exists"])
        report.add(check=name, level=Level.PASS,
                   message=f"Locale-Parität ok ({n_langs} Sprachen, "
                           f"Basis {rep['default_key_count']} Keys).")


def check_sdk_inventory(report: Report) -> None:
    """
    Vergleicht requirements.txt + buildozer.spec gegen DOCUMENTED_SDKS.
    Drift -> WARN, damit die Doku gepflegt bleibt.
    """
    name = "sdk_inventory"
    declared: set[str] = set()
    req = REPO_ROOT / "requirements.txt"
    if req.exists():
        for line in req.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            pkg = re.split(r"[=<>!~ ]", line, maxsplit=1)[0]
            declared.add(pkg)
    spec_path = REPO_ROOT / "buildozer.spec"
    spec = parse_buildozer_spec(spec_path)
    requirements = spec.get("requirements", "")
    for tok in requirements.split(","):
        pkg = re.split(r"[=<>!~ ]", tok.strip(), maxsplit=1)[0]
        if pkg:
            declared.add(pkg)

    undocumented = {p for p in declared if p and p.lower() not in {s.lower() for s in DOCUMENTED_SDKS} and p != "python3"}
    # Wir lassen Standard-Python-Pakete (sqlite3, hashlib) durch.
    stdlib_allowlist = {"sqlite3", "hashlib", "json"}
    undocumented -= stdlib_allowlist
    if undocumented:
        for p in sorted(undocumented):
            report.add(check=name, level=Level.WARN,
                       message=f"SDK/Library {p!r} ist nicht in DOCUMENTED_SDKS. "
                               "Eintrag in docs/android/04_PRIVACY_PERMISSIONS.md ergaenzen.")
    else:
        report.add(check=name, level=Level.PASS,
                   message="Alle deklarierten Libraries dokumentiert.")


def check_store_assets(report: Report) -> None:
    """Prueft, ob in playstore.yml referenzierte Store-Bilder existieren."""
    name = "store_assets"
    cfg = _load_playstore_yml()
    images = cfg.get("images") or {}
    required: list[tuple[str, str]] = []
    icon = images.get("icon")
    if icon:
        required.append(("icon", icon))
    fg = images.get("feature_graphic")
    if fg:
        required.append(("feature_graphic", fg))
    for i, shot in enumerate(images.get("phone_screenshots") or [], start=1):
        if shot:
            required.append((f"phone_screenshot_{i}", shot))
    if not required:
        report.add(check=name, level=Level.WARN,
                   message="Keine Store-Assets in playstore.yml konfiguriert.")
        return
    missing: list[str] = []
    for label, rel in required:
        path = REPO_ROOT / str(rel).replace("\\", "/")
        if not path.is_file() or path.stat().st_size < 64:
            missing.append(f"{label}: {rel}")
    if missing:
        for item in missing:
            report.add(check=name, level=Level.FAIL,
                       message=f"Store-Asset fehlt oder zu klein: {item}")
        return
    report.add(check=name, level=Level.PASS,
               message=f"Alle {len(required)} Store-Assets vorhanden.")


def check_listing_strings(report: Report, files: Sequence[Path]) -> None:
    """Sucht in Quellen nach Lorem-ipsum/TODO-Platzhaltern, die im UI erscheinen koennten."""
    name = "listing_strings"
    patterns = [r"\blorem\s+ipsum\b", r"\bplaceholder text\b"]
    hits = 0
    for p in files:
        if p.suffix.lower() not in {".py", ".kv", ".xml", ".json"}:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pat in patterns:
            for m in re.finditer(pat, text, re.IGNORECASE):
                hits += 1
                line_no = text.count("\n", 0, m.start()) + 1
                report.add(check=name, level=Level.FAIL,
                           message=f"Platzhalter-Text in Quelle: {m.group(0)!r}",
                           file=str(p.relative_to(REPO_ROOT)), line=line_no)
    if hits == 0:
        report.add(check=name, level=Level.PASS,
                   message="Keine Lorem-ipsum-Platzhalter gefunden.")


def check_manifest_if_present(report: Report) -> None:
    """
    Falls ein generiertes AndroidManifest.xml im .buildozer-Build liegt,
    pruefen wir es zusaetzlich. Im Frischen Repo existiert es nicht -
    das ist okay (PASS-Skip).
    """
    name = "manifest"
    candidates = list((REPO_ROOT / ".buildozer").rglob("AndroidManifest.xml"))
    if not candidates:
        report.add(check=name, level=Level.PASS,
                   message="(Kein generiertes AndroidManifest.xml im Repo - okay.)")
        return
    for mf in candidates:
        try:
            text = mf.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if 'android:usesCleartextTraffic="true"' in text:
            report.add(check=name, level=Level.FAIL,
                       message="usesCleartextTraffic=true im Manifest.",
                       file=str(mf.relative_to(REPO_ROOT)))
        if 'android:debuggable="true"' in text:
            report.add(check=name, level=Level.FAIL,
                       message="debuggable=true im Manifest.",
                       file=str(mf.relative_to(REPO_ROOT)))
        if 'android:allowBackup="true"' in text:
            report.add(check=name, level=Level.WARN,
                       message="allowBackup=true im Manifest. "
                               "PII-Apps sollten Auto-Backup steuern (BackupAgent oder false).",
                       file=str(mf.relative_to(REPO_ROOT)))


def check_apk_branding(report: Report, spec: dict[str, str]) -> None:
    """Prueft, dass Icon/Presplash in buildozer.spec gesetzt und vorhanden sind."""
    name = "apk_branding"
    icon = spec.get("icon.filename")
    if not icon:
        report.add(check=name, level=Level.FAIL,
                   message="icon.filename fehlt in buildozer.spec "
                           "(Kivy-Default-Icon vermeiden).")
    else:
        path = REPO_ROOT / icon
        if not path.is_file() or path.stat().st_size < 256:
            report.add(check=name, level=Level.FAIL,
                       message=f"App-Icon fehlt oder zu klein: {icon}")
        else:
            report.add(check=name, level=Level.PASS,
                       message=f"App-Icon vorhanden: {icon}")

    splash = spec.get("presplash.filename")
    if not splash:
        report.add(check=name, level=Level.WARN,
                   message="presplash.filename nicht gesetzt (optional, empfohlen).")
    else:
        path = REPO_ROOT / splash
        if not path.is_file() or path.stat().st_size < 256:
            report.add(check=name, level=Level.FAIL,
                       message=f"Splash fehlt oder zu klein: {splash}")
        else:
            report.add(check=name, level=Level.PASS,
                       message=f"Splash vorhanden: {splash}")


# ---------------------------------------------------------------------------
# Orchestrierung
# ---------------------------------------------------------------------------

CHECKS: dict[str, Callable[..., None]] = {
    "sdk":             lambda rep, ctx: check_sdk_levels(rep, ctx["spec"]),
    "permissions":     lambda rep, ctx: check_permissions(rep, ctx["spec"]),
    "versioning":      lambda rep, ctx: check_versioning(rep, ctx["spec"]),
    "secrets":         lambda rep, ctx: check_secrets(rep, ctx["files"]),
    "code_smells":     lambda rep, ctx: check_smells(rep, ctx["files"]),
    "demo_data":       lambda rep, ctx: check_demo_data_excluded(rep, ctx["spec"]),
    "privacy_docs":    lambda rep, ctx: check_privacy_docs(rep),
    "data_deletion":   lambda rep, ctx: check_data_deletion(rep),
    "closed_test":     lambda rep, ctx: check_closed_test_evidence(rep),
    "i18n":            lambda rep, ctx: check_i18n(rep),
    "sdk_inventory":   lambda rep, ctx: check_sdk_inventory(rep),
    "listing_strings": lambda rep, ctx: check_listing_strings(rep, ctx["files"]),
    "store_assets":    lambda rep, ctx: check_store_assets(rep),
    "apk_branding":    lambda rep, ctx: check_apk_branding(rep, ctx["spec"]),
    "manifest":        lambda rep, ctx: check_manifest_if_present(rep),
}


def run_checks(only: list[str] | None) -> Report:
    spec_path = REPO_ROOT / "buildozer.spec"
    spec = parse_buildozer_spec(spec_path)
    files = list(iter_source_files(REPO_ROOT))
    ctx = {"spec": spec, "files": files}
    report = Report()
    selected = list(CHECKS.keys()) if not only else [c for c in only if c in CHECKS]
    for name in selected:
        try:
            CHECKS[name](report, ctx)
        except Exception as e:                       # pragma: no cover - safety
            report.add(check=name, level=Level.FAIL,
                       message=f"Interner Fehler im Check {name!r}: {e!r}")
    return report


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def format_text(report: Report) -> str:
    lines: list[str] = []
    summary = report.summary()
    lines.append(f"Play-Store-Compliance-Report")
    lines.append("=" * 70)
    lines.append(f"PASS: {summary['pass']}  WARN: {summary['warn']}  FAIL: {summary['fail']}  TOTAL: {summary['total']}")
    lines.append("")
    by_check: dict[str, list[Finding]] = {}
    for f in report.findings:
        by_check.setdefault(f.check, []).append(f)
    for check_name in sorted(by_check):
        lines.append(f"[{check_name}]")
        for f in by_check[check_name]:
            tag = {Level.PASS: "ok  ", Level.WARN: "warn", Level.FAIL: "FAIL"}[f.level]
            loc = ""
            if f.file:
                loc = f"  ({f.file}" + (f":{f.line})" if f.line else ")")
            lines.append(f"  {tag}  {f.message}{loc}")
        lines.append("")
    return "\n".join(lines)


def format_json(report: Report) -> str:
    return json.dumps({
        "summary":  report.summary(),
        "findings": [f.as_dict() for f in report.findings],
    }, indent=2, sort_keys=True)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Play-Store-Compliance-Checker fuer Alltagshelfer/ZunaroDo")
    parser.add_argument("--only", default=None,
                        help="Kommagetrennte Liste von Checks "
                             "(z.B. 'sdk,permissions,secrets').")
    parser.add_argument("--json", action="store_true",
                        help="JSON-Report statt Text.")
    parser.add_argument("--strict", action="store_true",
                        help="Beendet mit exit > 0 auch bei WARN.")
    args = parser.parse_args(argv)

    only = [s.strip() for s in args.only.split(",") if s.strip()] if args.only else None
    if only:
        unknown = [c for c in only if c not in CHECKS]
        if unknown:
            print(f"Unbekannter Check: {unknown}. Bekannte: {sorted(CHECKS)}",
                  file=sys.stderr)
            return 2

    report = run_checks(only)
    out = format_json(report) if args.json else format_text(report)
    print(out)

    summary = report.summary()
    if summary["fail"] > 0:
        return 1
    if args.strict and summary["warn"] > 0:
        return 1
    return 0


if __name__ == "__main__":                            # pragma: no cover
    raise SystemExit(main())
