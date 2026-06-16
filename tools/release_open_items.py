"""
Zentrale Liste offener, nicht voll automatisierbarer Release-Schritte.

Das Control Panel, das statische Dashboard und die Markdown-Dokumentation
nutzen diese Datei als gemeinsame Quelle. So bleiben die operativen
Restpunkte (Play Console, echte Geräte, Keystore, Closed Testing usw.)
an einer Stelle gepflegt und driften nicht auseinander.

Aufruf:

    python -m tools.release_open_items --markdown
    python -m tools.release_open_items --markdown --out release/OFFENE_MANUELLE_SCHRITTE.md
    python -m tools.release_open_items --json
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable, Optional


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "release" / "OFFENE_MANUELLE_SCHRITTE.md"


@dataclass(frozen=True)
class Reference:
    """Lokale Doku oder externer Link zu einem offenen Punkt."""

    label: str
    target: str

    @property
    def is_url(self) -> bool:
        return self.target.startswith(("https://", "http://"))

    @property
    def is_https(self) -> bool:
        return self.target.startswith("https://")


@dataclass(frozen=True)
class OpenItem:
    """Ein offener Schritt, der nicht vollständig lokal automatisierbar ist."""

    id: str
    title: str
    category: str
    status: str
    why_manual: str
    what_to_do: tuple[str, ...]
    local_docs: tuple[Reference, ...] = field(default_factory=tuple)
    official_links: tuple[Reference, ...] = field(default_factory=tuple)
    related_commands: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class AutomatedCheck:
    """Ein lokaler Check, der im Admin-Panel ausgeführt werden kann."""

    id: str
    label: str
    module: str
    args: tuple[str, ...] = field(default_factory=tuple)
    description: str = ""
    requires: tuple[str, ...] = field(default_factory=tuple)

    def command(self, python: str) -> list[str]:
        return [python, "-m", self.module, *self.args]


def automated_checks() -> list[AutomatedCheck]:
    """Automatisierbare Prüfungen für den Release-/Preflight-Bereich."""

    return [
        AutomatedCheck(
            id="playstore-strict",
            label="Play-Store-Compliance (strict)",
            module="tools.playstore_check",
            args=("--strict",),
            description=(
                "Prüft SDK-Level, Permissions, Versionierung, Secrets, "
                "Store-Assets, Datenschutz-Dokumente und Release-Gates."
            ),
        ),
        AutomatedCheck(
            id="data-safety-check",
            label="Data-Safety gegen Code prüfen",
            module="tools.data_safety",
            args=("--check",),
            description=(
                "Vergleicht playstore.yml mit den im Code erkennbaren "
                "Datenflüssen, SDKs und Löschfunktionen."
            ),
        ),
        AutomatedCheck(
            id="data-safety-markdown",
            label="Data-Safety-Antwortbogen anzeigen",
            module="tools.data_safety",
            args=("--markdown",),
            description=(
                "Rendert die Antworten, die im Play-Console-Formular "
                "manuell übertragen werden müssen."
            ),
        ),
        AutomatedCheck(
            id="privacy-policy-check",
            label="Datenschutzerklärung prüfen",
            module="tools.privacy_policy",
            args=("--check",),
            description=(
                "Prüft, ob die lokale Datenschutzerklärung existiert und "
                "keine harten Veröffentlichungsfehler enthält."
            ),
        ),
        AutomatedCheck(
            id="legal-coverage",
            label="Rechtstexte-Coverage anzeigen",
            module="tools.legal_status",
            description="Zeigt, welche Rechtstexte in welchen Sprachen vorliegen.",
        ),
        AutomatedCheck(
            id="build-status",
            label="Build-Status für alle Plattformen",
            module="tools.build_status",
            args=("--no-emoji",),
            description="Listet Desktop-, Android- und iOS-Build-Voraussetzungen.",
        ),
        AutomatedCheck(
            id="android-device-skip-ocr",
            label="Android-Gerät prüfen (ohne OCR)",
            module="tools.verify_android_device",
            args=("--skip-ocr",),
            description=(
                "Prüft ein angeschlossenes adb-Gerät auf installierte App "
                "und SQLCipher-DB. OCR bleibt für den manuellen Scan separat."
            ),
            requires=("adb", "echtes oder emuliertes Android-Gerät"),
        ),
        AutomatedCheck(
            id="release-open-items-markdown",
            label="Offene manuelle Punkte als Markdown",
            module="tools.release_open_items",
            args=("--markdown",),
            description="Gibt die unten gezeigte offene-Punkte-Liste im Terminal aus.",
        ),
    ]


def items() -> list[OpenItem]:
    """Deterministische Liste der offenen manuellen/externalen Schritte."""

    data = [
        OpenItem(
            id="android-device-verification",
            title="SQLCipher, ML-Kit-OCR und App-Icon auf echtem Android-Gerät prüfen",
            category="blocker",
            status="external_device_required",
            why_manual=(
                "Die Verschlüsselung im App-Sandbox-Pfad, ML-Kit-Kamera/OCR "
                "und Launcher-Darstellung hängen von einem realen Android-"
                "Gerät bzw. Emulator mit installierter App ab. Das Repo kann "
                "nur den Prüfbefehl bereitstellen, nicht das Gerät selbst."
            ),
            what_to_do=(
                "Debug- oder Release-Build installieren.",
                "`python -m tools.verify_android_device` ausführen; für einen "
                "schnellen SQLCipher-Check zunächst `--skip-ocr` verwenden.",
                "Für OCR einen Beleg in der App scannen und den Check ohne "
                "`--skip-ocr` wiederholen.",
                "Launcher öffnen und prüfen, dass kein weißes Default-Icon "
                "angezeigt wird.",
            ),
            local_docs=(
                Reference("Go-Live-TODO §1.1", "release/GO_LIVE_TODO.md#11-android-build-erzeugen-basis-fuer-alles-weitere"),
                Reference("Android-Geräteprüfer", "tools/verify_android_device.py"),
                Reference("Android-Release-Checkliste", "docs/android/09_RELEASE_CHECKLIST.md#e-funktionaler-smoke-manuell-auf-echtem-gerat"),
            ),
            official_links=(
                Reference("Android Debug Bridge (adb)", "https://developer.android.com/tools/adb"),
                Reference("ML Kit Text Recognition", "https://developers.google.com/ml-kit/vision/text-recognition/v2"),
            ),
            related_commands=(
                "python -m tools.verify_android_device --skip-ocr",
                "python -m tools.verify_android_device",
            ),
        ),
        OpenItem(
            id="upload-keystore",
            title="Upload-Keystore erzeugen, sichern und Secrets setzen",
            category="blocker",
            status="secret_material_required",
            why_manual=(
                "Der Upload-Key ist geheimes, langlebiges Signiermaterial. "
                "Er darf nicht im Repository erzeugt oder gespeichert werden "
                "und muss in einem Passwort-Manager sowie als CI-Secret "
                "außerhalb des Codes gesichert werden."
            ),
            what_to_do=(
                "`release/create_upload_keystore.ps1` oder "
                "`release/create_upload_keystore.sh` lokal ausführen.",
                "Keystore-Datei und Passwörter sicher außerhalb des Repos sichern.",
                "CI-Secrets `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_PASSWORD`, "
                "`ANDROID_KEY_ALIAS`, `ANDROID_KEY_ALIAS_PASSWORD` setzen.",
                "Vor dem ersten Production-Upload Play App Signing aktivieren.",
            ),
            local_docs=(
                Reference("Play-Console-Setup", "release/PLAY_CONSOLE_SETUP.md"),
                Reference("Windows-Keystore-Helfer", "release/create_upload_keystore.ps1"),
                Reference("Linux/macOS-Keystore-Helfer", "release/create_upload_keystore.sh"),
            ),
            official_links=(
                Reference("Play App Signing", "https://support.google.com/googleplay/android-developer/answer/9842756"),
                Reference("App signieren", "https://developer.android.com/studio/publish/app-signing"),
            ),
        ),
        OpenItem(
            id="release-aab",
            title="Signiertes Release-AAB bauen und als Play-Artefakt prüfen",
            category="blocker",
            status="ci_or_build_host_required",
            why_manual=(
                "Google Play akzeptiert für neue Apps ein signiertes Android "
                "App Bundle. Der Build benötigt Linux/WSL2 oder CI sowie die "
                "nicht im Repo liegenden Keystore-Secrets."
            ),
            what_to_do=(
                "Release-Workflow `Android Release (AAB)` dispatchen oder "
                "unter Linux/WSL2 `buildozer android release` ausführen.",
                "Artefakt `dist/*.aab` herunterladen und Version/Signatur prüfen.",
                "Bei jedem Upload `android.numeric_version` und "
                "`playstore.yml identity.version_code` gemeinsam erhöhen.",
            ),
            local_docs=(
                Reference("Buildozer-Konfiguration", "buildozer.spec"),
                Reference("Mobile-Build-Anleitung", "MOBILE.md#build-schritt-fuer-schritt"),
                Reference("Release-Checkliste", "docs/android/09_RELEASE_CHECKLIST.md#a-code--build"),
            ),
            official_links=(
                Reference("Android App Bundles", "https://developer.android.com/guide/app-bundle"),
                Reference("Buildozer", "https://buildozer.readthedocs.io/"),
            ),
            related_commands=(
                "python -m tools.playstore_check --strict",
                "buildozer android release",
            ),
        ),
        OpenItem(
            id="play-console-app",
            title="Play-Developer-Konto verifizieren und App in der Play Console anlegen",
            category="blocker",
            status="external_account_required",
            why_manual=(
                "Kontoerstellung, Identitätsprüfung, Zahlungsprofil und das "
                "finale Anlegen der App passieren ausschließlich in Googles "
                "Play Console und erfordern persönliche bzw. Organisationsdaten."
            ),
            what_to_do=(
                "Developer Account anlegen bzw. verifizieren.",
                "Neue App mit Name `ZunaroDo`, Standardsprache `de-DE`, "
                "Kategorie `PRODUCTIVITY` und Package `de.alltagshelfer.alltagshelfer` anlegen.",
                "Support-, Marketing- und Datenschutz-URLs aus `playstore.yml` übertragen.",
            ),
            local_docs=(
                Reference("Play-Store-Anleitung", "PLAYSTORE.md#5-play-console-einrichten"),
                Reference("Play-Console-Setup", "release/PLAY_CONSOLE_SETUP.md"),
                Reference("Playstore-Konfiguration", "playstore.yml"),
            ),
            official_links=(
                Reference("Play Console Signup", "https://play.google.com/console/signup"),
                Reference("App erstellen und einrichten", "https://support.google.com/googleplay/android-developer/answer/9859152"),
            ),
        ),
        OpenItem(
            id="data-safety-iarc",
            title="Data-Safety- und Content-Rating/IARC-Formulare ausfüllen",
            category="blocker",
            status="console_form_required",
            why_manual=(
                "Das Repo kann die Antworten generieren und gegen den Code "
                "prüfen, aber die Play-Console-Formulare müssen im Google-UI "
                "durch einen berechtigten Account bestätigt werden."
            ),
            what_to_do=(
                "`python -m tools.data_safety --markdown` ausführen.",
                "Antworten in der Play Console übertragen und mit "
                "`release/DATA_SAFETY_CONSOLE_ANSWERS.md` gegenprüfen.",
                "IARC-/Content-Rating-Fragebogen ausfüllen und Ergebnis speichern.",
            ),
            local_docs=(
                Reference("Data-Safety-Antworten", "release/DATA_SAFETY_CONSOLE_ANSWERS.md"),
                Reference("Data-Safety-Tool", "tools/data_safety.py"),
                Reference("Privacy-/Permissions-Doku", "docs/android/04_PRIVACY_PERMISSIONS.md"),
            ),
            official_links=(
                Reference("Play Data Safety", "https://support.google.com/googleplay/android-developer/answer/10787469"),
                Reference("Content Ratings", "https://support.google.com/googleplay/android-developer/answer/188189"),
            ),
            related_commands=(
                "python -m tools.data_safety --check",
                "python -m tools.data_safety --markdown",
            ),
        ),
        OpenItem(
            id="closed-testing",
            title="Closed Testing mit mindestens 12 Testern über 14 Tage nachweisen",
            category="blocker",
            status="calendar_and_people_required",
            why_manual=(
                "Google verlangt bei neuen persönlichen Developer-Konten "
                "echte Tester, einen zusammenhängenden Zeitraum und Play-"
                "Console-Nachweise. Diese Signale können lokal nicht erzeugt "
                "oder simuliert werden."
            ),
            what_to_do=(
                "AAB in Internal/Closed Testing hochladen.",
                "Testergruppe mit mindestens 12 aktiven Testern betreiben.",
                "Mindestens 14 zusammenhängende Tage warten und Feedback/Crashes prüfen.",
                "Nachweise in `release/closed-test-*.md` und `release/assets/` ablegen.",
            ),
            local_docs=(
                Reference("Closed-Test-Runbook", "release/CLOSED_TEST_RUNBOOK.md"),
                Reference("Evidenz-Vorlage", "release/CLOSED_TEST_EVIDENCE_TEMPLATE.md"),
                Reference("Vorbereiteter Nachweis", "release/closed-test-2026-05-30.md"),
            ),
            official_links=(
                Reference("Closed testing requirements", "https://support.google.com/googleplay/android-developer/answer/14151465"),
                Reference("Tracks einrichten", "https://support.google.com/googleplay/android-developer/answer/9845334"),
            ),
        ),
        OpenItem(
            id="play-billing",
            title="Optionalen Play-Billing-Kaufflow mit Lizenztester prüfen",
            category="optional",
            status="conditional_if_iap_launches",
            why_manual=(
                "Echte Käufe, Lizenztester, Subscription-Produkte und Server-"
                "Verifikation laufen über Play Console, Google-Konten und "
                "einen deployten Payment-Server."
            ),
            what_to_do=(
                "Nur nötig, wenn Pro/Abos bereits zum Launch verkauft werden.",
                "Abo-IDs exakt wie in `services/play_billing_android.py` anlegen.",
                "Payment-Server deployen und `/verify/play` mit Service-Account testen.",
                "Echten Testkauf durchführen und signiertes Lizenz-Token prüfen.",
            ),
            local_docs=(
                Reference("Payment-Dokumentation", "PAYMENT.md"),
                Reference("Payment-Server-Deploy", "release/deploy-payment-server.md"),
                Reference("Billing-Implementierung", "services/play_billing_android.py"),
            ),
            official_links=(
                Reference("Google Play Billing", "https://developer.android.com/google/play/billing"),
                Reference("Subscriptions", "https://developer.android.com/google/play/billing/subscriptions"),
            ),
        ),
        OpenItem(
            id="ios-build",
            title="iOS-Build auf macOS/Xcode verifizieren",
            category="platform",
            status="macos_required",
            why_manual=(
                "Apple erlaubt iOS-Builds und Code-Signing nur mit macOS, "
                "Xcode und Apple-Developer-Zugang. Eine Linux/Windows-VM kann "
                "das Xcode-Projekt höchstens dokumentieren, nicht final bauen."
            ),
            what_to_do=(
                "Auf macOS `scripts/build-ios.sh` ausführen.",
                "Xcode-Projekt öffnen, Bundle-ID und Signing-Team setzen.",
                "Run auf Gerät/Simulator ausführen und IPA-Export separat prüfen.",
            ),
            local_docs=(
                Reference("iOS-Build-Skript", "scripts/build-ios.sh"),
                Reference("Mobile-Dokumentation", "MOBILE.md"),
                Reference("Build-Status-Tool", "tools/build_status.py"),
            ),
            official_links=(
                Reference("Xcode", "https://developer.apple.com/xcode/"),
                Reference("kivy-ios", "https://github.com/kivy/kivy-ios"),
            ),
            related_commands=("bash scripts/build-ios.sh",),
        ),
        OpenItem(
            id="production-monitoring",
            title="Produktionsrollout überwachen und nach 48 Stunden bewerten",
            category="post_release",
            status="live_traffic_required",
            why_manual=(
                "Crash-/ANR-Raten, Reviews und Support-Tickets entstehen erst "
                "durch echten Rollout mit echten Nutzern. Lokale Tests können "
                "nur die Schwellen und Checklisten vorbereiten."
            ),
            what_to_do=(
                "Gestaffelten Rollout starten (z. B. 5 % → 20 % → 50 % → 100 %).",
                "Android Vitals, Reviews und Support-Tickets in den ersten 48 h prüfen.",
                "Bei P0/P1-Problemen Rollout pausieren und Incident-Doku anlegen.",
            ),
            local_docs=(
                Reference("Release-Checkliste M/Post-Release", "docs/android/09_RELEASE_CHECKLIST.md#m-post-release"),
                Reference("Go-Live-TODO §3", "release/GO_LIVE_TODO.md#3-finaler-pre-submit-check-vor-jedem-upload"),
                Reference("Playstore-Konfiguration Monitoring", "playstore.yml"),
            ),
            official_links=(
                Reference("Android Vitals", "https://developer.android.com/topic/performance/vitals"),
                Reference("Play Console Vitals", "https://play.google.com/console/about/vitals/"),
            ),
        ),
    ]
    return sorted(data, key=lambda item: item.id)


def manual_items() -> list[OpenItem]:
    return items()


def _rel_or_url(ref: Reference) -> str:
    if ref.is_url:
        return ref.target
    return ref.target.replace("\\", "/")


def _reference_markdown(refs: Iterable[Reference]) -> str:
    parts = []
    for ref in refs:
        target = _rel_or_url(ref)
        parts.append(f"[{ref.label}]({target})")
    return ", ".join(parts) if parts else "—"


def to_markdown(open_items: Optional[list[OpenItem]] = None) -> str:
    """Rendert die offenen Punkte als abhakbare Markdown-Übersicht."""

    open_items = open_items if open_items is not None else items()
    lines = [
        "# Offene manuelle Release-Schritte",
        "",
        "Diese Liste enthält Punkte, die das Repository vorbereiten und prüfen, "
        "aber nicht vollständig selbst erledigen kann. Sie wird aus "
        "`tools/release_open_items.py` generiert und ist dieselbe Quelle, die "
        "das Control Panel verwendet.",
        "",
        "Legende: `[ ]` offen · `blocker` vor Production-Go zwingend · "
        "`optional` nur bei entsprechendem Launch-Umfang · `post_release` nach "
        "Rollout prüfen.",
        "",
    ]
    for item in open_items:
        lines.extend([
            f"## [ ] {item.title}",
            "",
            f"- ID: `{item.id}`",
            f"- Kategorie: `{item.category}`",
            f"- Status: `{item.status}`",
            f"- Warum nicht voll automatisierbar: {item.why_manual}",
            f"- Lokale Doku: {_reference_markdown(item.local_docs)}",
            f"- Offizielle Links: {_reference_markdown(item.official_links)}",
            "",
            "Nächste Schritte:",
            "",
        ])
        lines.extend(f"1. {step}" for step in item.what_to_do)
        if item.related_commands:
            lines.extend(["", "Prüf-/Hilfsbefehle:", ""])
            lines.extend(f"- `{cmd}`" for cmd in item.related_commands)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _jsonable() -> dict:
    return {
        "automated_checks": [asdict(c) for c in automated_checks()],
        "manual_items": [asdict(i) for i in items()],
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Offene manuelle Release-Schritte ausgeben.")
    parser.add_argument("--markdown", action="store_true",
                        help="Markdown statt Kurzliste ausgeben.")
    parser.add_argument("--json", action="store_true",
                        help="Maschinenlesbare JSON-Ausgabe.")
    parser.add_argument("--out", default=None,
                        help=f"Markdown-Zielpfad (Default: {DEFAULT_OUT}).")
    parser.add_argument("--write-default", action="store_true",
                        help="Markdown nach release/OFFENE_MANUELLE_SCHRITTE.md schreiben.")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")     # type: ignore[union-attr]
        except (AttributeError, ValueError):         # pragma: no cover
            pass

    if args.json:
        print(json.dumps(_jsonable(), ensure_ascii=False, indent=2))
        return 0

    if args.markdown or args.write_default or args.out:
        text = to_markdown()
        if args.out or args.write_default:
            out = Path(args.out) if args.out else DEFAULT_OUT
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(text, encoding="utf-8")
            print(f"Offene manuelle Schritte geschrieben: {out}")
        else:
            sys.stdout.write(text)
        return 0

    print("Offene manuelle Release-Schritte:")
    for item in items():
        print(f"- [{item.category}] {item.title} ({item.status})")
    print()
    print("Details: python -m tools.release_open_items --markdown")
    return 0


if __name__ == "__main__":                            # pragma: no cover
    raise SystemExit(main())
