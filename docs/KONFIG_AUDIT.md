# Audit: Vollständigkeit der „einfachen Konfiguration"

> Stand: 2026-06-30 · Methodik: Multi-Agent-Audit (Inventar + 4 Säulen Wizard/PowerShell/Tooltips/Erklärung), adversarial verifiziert, Belege als `Datei:Zeile`.

## 1. Gesamturteil

Die einfache Konfiguration von ZunaroDo ist **inhaltlich solide, aber strukturell
unvollständig und zerfasert**. Es fehlt nicht die Substanz, sondern die *geführte,
auffindbare, einheitliche Verpackung*:

- **Kein** geführter Konfigurations-Wizard (kein Mehrschritt-Stepper, keine `.env`-Erzeugung).
- **Kein einziger** echter Hover-Tooltip im ganzen Repo — alle „Tooltips" sind dauerhaft sichtbare statische Labels.
- PowerShell deckt **nur** die Release-Ebene ab; die App-/Laufzeit-Konfiguration (`.env`, Gemini, IMAP, Sync, SMTP) hat **keinen** PS-Pfad.
- Die beiden Konfig-Ebenen werden **nirgends zusammengeführt**: Das zentrale Einstiegsfenster (`tools/control_panel.py:360`) hat keine Konfigurations-/Einstellungen-Sektion und verlinkt die vorhandenen Erklärungen nicht.

**Geschätzter Gesamt-Vollständigkeitsgrad: ~43 %** (gewichtetes Mittel der vier Säulen
mit Abzug für die fehlende Zusammenführung und die Null-Discoverability aus dem Control Panel).

## 2. Säulen-Übersicht

| Säule | Vollständigkeit | Kernbefund |
|---|---|---|
| **Wizard / Assistent** | 30 % | Kein Mehrschritt-Wizard, keine `.env`-Erzeugung. Nur Endnutzer-Onboarding (Pricing/Demo-Daten) + flaches Settings-Formular. Control Panel: weder Wizard noch Einstellungen-Sektion. PS-Setups nicht-interaktiv. |
| **PowerShell** | 35 % | 5 robuste `.ps1` — aber nur Admin/Release. Laufzeit-Ebene ohne PS. Kein `.ps1` aus `start.bat`/Control Panel erreichbar. `create_upload_keystore.ps1:32` war PS-5.1-inkompatibel. |
| **Tooltips** | 45 % | Kein echter Hover-Tooltip (keine `<Enter>`/`<Leave>`-Bindings, keine `CTkToolTip`-Dependency). Statische Labels: Control Panel ~100 %, Settings-Tab nur teilweise (mehrere leere Hilfetexte). |
| **Ausführliche Erklärung** | 62 % | Release-Erklärung (why_manual/what_to_do/Links) vorbildlich und im Panel sichtbar. Laufzeit-Erklärung in README/SECURITY/`.env.example` vorhanden, aber nicht aus dem Panel verlinkt. Code/Doku-Widerspruch bei `smtp.pass`. |

## 3. Lücken-Matrix — Konfig-Punkte, die durch *alle* Raster fielen

| Konfig-Punkt | Wizard | PS | GUI-Feld | Env | Erklärung | Schwere |
|---|:--:|:--:|:--:|:--:|:--:|---|
| `smtp.pass` | ✗ | ✗ | ✗ | ✗ (kein ENV_MAP) | ✗ | **Hoch** — nirgends setzbar |
| `backup.auto_*` (4 Keys) | ✗ | ✗ | ✗ | ✗ | ✗ | **Hoch** — nur per DB |
| `checkout.*`-URLs | ✗ | ✗ | ✗ | ✗ | nur PAYMENT.md | Mittel |
| `i18n.language` | ✗ | ✗ | ✗ | ✗ | nur README | Mittel |
| `ALLTAGSHELFER_SYNC_URL/_TOKEN` | ✗ | ✗ | ✗ | ✓ (kein ENV_MAP) | `.env.example` | Mittel (Token = Secret!) |
| Play-Service-Account-Credentials | ✗ | ✗ | ✗ | ✗ (nicht in `.env.example`) | nur Confirm-Text | Mittel |

## 4. Priorisierte Empfehlungen

**Hoch**
1. `smtp.pass` bedienbar machen (ENV_MAP-Eintrag, anforderungskonform Env/Keyring statt DB).
2. Konfigurations-Sektion im Control Panel (`.env`-Erzeugung + `.ps1`-Buttons + Secret-Status).
3. Konfig-Doku aus dem Panel verlinken (`links()` um README/SECURITY/.env.example erweitern).
4. `backup.auto_*` bedienbar machen (SETTING_FIELDS).

**Mittel**
5. Echte Tooltip-Klasse mit `<Enter>`/`<Leave>`.
6. `.ps1` im Control Panel verdrahten.
7. PS-5.1-Kompatibilität von `create_upload_keystore.ps1`.
8. Leere Hilfetexte in `SETTING_FIELDS` füllen.
9. `i18n.language`-Feld in `SETTING_FIELDS`.

**Niedrig:** Keystore-Env-Vars optional setzen · Owner/Repo-Defaults parametrisieren · `.sh`-Äquivalente für Play/Pages · Verbindungstest für SMTP/IMAP.

## 5. Umgesetzt (Phase 1)

- ✅ **#1 `smtp.pass`** → `ENV_MAP["smtp.pass"] = ALLTAGSHELFER_SMTP_PASS` (`services/config.py`); in `.env.example` dokumentiert; SMTP-Host-Hilfetext verweist darauf. Erscheint nun automatisch in der Secret-Status-Anzeige (`gui.py:2813`).
- ✅ **#4 `backup.auto_*`** + **#9 `i18n.language`** → als editierbare Felder in `SETTING_FIELDS` (`gui.py`).
- ✅ **#8 leere Hilfetexte** gefüllt (gemini.max_tokens, imap.user, smtp.port/user/sender, sync.interval_seconds, notify.warn_within_days).
- ✅ **#3 Konfig-Doku-Links** in der Control-Panel-Doku-Sektion (`tools/control_panel.py`).
- ✅ **#7 PS-5.1-Kompatibilität** von `release/create_upload_keystore.ps1` (`?.`-Operator entfernt, `#Requires -Version 5.1`).

## 6. Umgesetzt (Phase 2)

- ✅ **#2 Konfig-Sektion im Control Panel** → neue Sektion „Konfiguration" mit geführter `.env`-Erzeugung. Dünne GUI-Buttons rufen das neue, getestete CLI-Tool `tools/env_setup.py`:
  - `.env initialisieren` (`--init`, kopiert `.env.example` → `.env`, überschreibt nie),
  - `.env-Status prüfen` (`--check`, zeigt gesetzt/leer je Variable, **Werte maskiert**).
- ✅ **#6 `.ps1` im Control Panel verdrahtet** (Discoverability null → nutzbar) → `setup-play-console.ps1` und `setup-github-pages.ps1` (Letztere mit Bestätigungsdialog) als Buttons in der Konfig-Sektion (nur Windows). Bewusst **nicht** verdrahtet: `create_upload_keystore.ps1` — `keytool` fragt interaktiv per stdin nach Passwörtern und würde den Capture-Runner blockieren; bleibt manueller Schritt.

## 7. Umgesetzt (Phase 3)

- ✅ **#5 Echte Hover-Tooltip-Klasse** → `core/tooltip.py` (`Tooltip` / `attach_tooltip`, stdlib-only, defensiv). **Additiv** eingesetzt (statische Labels bleiben):
  - `gui.py` — Settings-Eingabefelder zeigen ihren Hilfetext zusätzlich beim Hover.
  - `tools/control_panel.py` — Hover-Tooltips an Aktions-/Link-Buttons und v. a. an den auf 26 Zeichen **gekürzten** Referenz-Buttons der Release-Sektion (voller Label + Ziel). Der irreführende Kommentar (`description` = „Tooltip") ist jetzt korrekt.

**Offen (Mittel/Niedrig-Restpunkte):** Keystore-Env-Vars optional setzen statt nur drucken, `.sh`-Äquivalente für die Play/Pages-Skripte, optionaler SMTP/IMAP-Verbindungstest. Die verbleibenden „durch das Raster fallenden" Konfig-Punkte aus §3 (`checkout.*`, Play-Service-Account-Credentials) sind release-/zahlungsspezifisch und bewusst nicht im Endnutzer-Settings-Tab.

> **Ergebnis:** Alle vier Säulen (Wizard, PowerShell, Tooltips, Erklärung) sind nun strukturell abgedeckt; die im Audit identifizierten Hoch-Lücken sind geschlossen.
