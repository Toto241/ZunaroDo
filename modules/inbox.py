"""
Modul "Posteingang" - Mail-Analyse und zentrale Vorschlags-Ablage.

Ablauf nach dem Prinzip "Mensch bestaetigt, bevor geschrieben wird":

  Mail-Text  -->  Analyse  -->  Vorschlag in der zentralen Ablage
                                       |
                          Nutzer prueft (uebernehmen / ablehnen)
                                       |
                  uebernehmen  -->  Ziel-Capability wird aufgerufen
                                    (das zustaendige Modul prueft die Daten)

Die Vorschlags-Ablage ist zentral: jeder Vorschlag traegt eine
Ziel-Capability (z.B. "contracts.add"). Beim Uebernehmen wird genau diese
ueber den ModuleContext aufgerufen - das jeweilige Modul entscheidet
selbst, ob die Daten gueltig sind. Nichts wird ungeprueft eingetragen.

Hinweis: Dieser Prototyp analysiert eingefuegten Mail-Text bzw. .eml-
Dateien. Ein echter IMAP-Postfachzugriff waere ein spaeterer,
separater Schritt.
"""
from __future__ import annotations

import os
import re
from datetime import date

from core.interface import Capability, ModuleContext, ModuleInterface
from database import ProposalRepository
from models import Proposal


# IMAP-Postfachzugriff ist bewusst optional. Konfiguration via
# Umgebungsvariablen ALLTAGSHELFER_IMAP_{HOST,USER,PASS}.

# Stichworte zur groben Kategorie-Erkennung
_CATEGORY_HINTS = {
    "streaming": ("netflix", "spotify", "disney", "dazn", "streaming", "wow"),
    "mobilfunk": ("telekom", "vodafone", "o2", "mobilfunk", "handy", "congstar"),
    "versicherung": ("versicherung", "huk", "allianz", "axa", "police"),
    "strom": ("strom", "energie", "eon", "vattenfall", "stadtwerke"),
}


def _extract_euro(text: str) -> float | None:
    """Sucht einen Euro-Betrag wie '12,99 EUR' oder 'EUR 12,99'."""
    patterns = [r"(\d+[.,]\d{2})\s*(?:eur|euro|\u20ac)",
                r"(?:eur|euro|\u20ac)\s*(\d+[.,]\d{2})"]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return float(m.group(1).replace(",", "."))
    return None


def _extract_date(text: str) -> str | None:
    """Sucht ein Datum im Format TT.MM.JJJJ und gibt es als ISO zurueck."""
    m = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", text)
    if not m:
        return None
    day, month, year = (int(g) for g in m.groups())
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return None


def _guess_category(text: str) -> str:
    low = text.lower()
    for category, hints in _CATEGORY_HINTS.items():
        if any(h in low for h in hints):
            return category
    return "sonstiges"


class InboxModule(ModuleInterface):
    """Modul fuer Mail-Analyse und die zentrale Vorschlags-Ablage."""

    def __init__(self, repo: ProposalRepository,
                 llm=None):                              # LLMClient | None
        self.repo = repo
        self.llm = llm
        self._ctx: ModuleContext | None = None

    @property
    def module_id(self) -> str:
        return "inbox"

    @property
    def display_name(self) -> str:
        return "Posteingang & Vorschlaege"

    def on_register(self, context: ModuleContext) -> None:
        self._ctx = context

    def get_context_summary(self) -> str:
        offen = self.repo.list(status="offen")
        if not offen:
            return "Keine offenen Vorschlaege."
        return f"{len(offen)} Vorschlag/Vorschlaege warten auf Pruefung."

    # ---- Faehigkeiten --------------------------------------------------
    def get_capabilities(self) -> list[Capability]:
        return [
            Capability(
                name="inbox.analyze_mail",
                description="Analysiert den Text einer eingegangenen Mail und "
                            "legt passende Vorschlaege in der Ablage an.",
                parameters={
                    "mail_text": {"type": "string", "_required": True,
                                  "description": "Der vollstaendige Mail-Text"},
                },
                handler=self._cap_analyze_mail,
            ),
            Capability(
                name="inbox.proposals",
                description="Listet die offenen Vorschlaege in der Ablage auf.",
                parameters={},
                handler=self._cap_proposals,
            ),
            Capability(
                name="inbox.accept_proposal",
                description="Uebernimmt einen Vorschlag: ruft die Ziel-"
                            "Capability auf, das zustaendige Modul traegt "
                            "die Daten ein.",
                parameters={
                    "proposal_id": {"type": "integer", "_required": True,
                                    "description": "ID des Vorschlags"},
                },
                handler=self._cap_accept_proposal,
                destructive=True,
            ),
            Capability(
                name="inbox.reject_proposal",
                description="Lehnt einen Vorschlag ab (wird nicht uebernommen).",
                parameters={
                    "proposal_id": {"type": "integer", "_required": True,
                                    "description": "ID des Vorschlags"},
                },
                handler=self._cap_reject_proposal,
                destructive=True,
            ),
            Capability(
                name="inbox.import_eml",
                description="Liest eine .eml-Datei ein und analysiert sie.",
                parameters={
                    "path": {"type": "string", "_required": True,
                             "description": "Pfad zur .eml-Datei"},
                },
                handler=self._cap_import_eml,
            ),
            Capability(
                name="inbox.fetch_imap",
                description="Holt ungelesene Mails per IMAP und analysiert sie. "
                            "Braucht ALLTAGSHELFER_IMAP_HOST/USER/PASS in "
                            "der Umgebung; ohne diese wird uebersprungen.",
                parameters={
                    "folder": {"type": "string",
                               "description": "IMAP-Ordner (Standard: INBOX)"},
                    "limit": {"type": "integer",
                              "description": "Max. Anzahl Mails"},
                },
                handler=self._cap_fetch_imap,
            ),
        ]

    # ---- Handler -------------------------------------------------------
    def _cap_analyze_mail(self, mail_text: str) -> dict:
        # 1) regelbasierte Erkennung (deterministisch, schnell, kostenlos)
        proposals = self._analyze(mail_text)

        # 2) zusaetzlich: LLM-Erkennung, wenn verfuegbar
        if self.llm is not None and getattr(self.llm, "is_available", False):
            llm_proposals = self._analyze_with_llm(mail_text)
            # Doppelte (gleiche Capability + gleiche zentrale Payload-Felder)
            # vermeiden
            seen = {(p.target_capability,
                      p.payload.get("contract_id"),
                      p.payload.get("name")) for p in proposals}
            for p in llm_proposals:
                key = (p.target_capability,
                        p.payload.get("contract_id"),
                        p.payload.get("name"))
                if key not in seen:
                    proposals.append(p)
                    seen.add(key)

        for p in proposals:
            self.repo.add(p)
        if not proposals:
            return {"status": "analysiert",
                    "found": 0,
                    "hinweis": "Kein bekanntes Muster erkannt - kein "
                               "Vorschlag erstellt."}
        return {"status": "analysiert",
                "found": len(proposals),
                "proposals": [p.to_dict() for p in proposals]}

    # ---- LLM-basierte Analyse (Gemini) ---------------------------------
    # Halluzinationen abfangen: das Modell darf nur Vorschlaege fuer
    # Capabilities aus dieser Allowlist erzeugen. Alles andere wird im
    # Parser verworfen.
    _ALLOWED_LLM_TARGETS: set[str] = {
        "contracts.add", "contracts.report_price_change",
        "family.add_order", "calendar.add_event",
    }

    def _analyze_with_llm(self, mail_text: str) -> list[Proposal]:
        """Bittet das LLM, strukturierte Vorschlaege im JSON-Format zu liefern."""
        cap_names = []
        if self._ctx is not None:
            for cap in self._ALLOWED_LLM_TARGETS:
                if self._ctx.has_capability(cap):
                    cap_names.append(cap)
        instruction = (
            "Du analysierst eine eingegangene E-Mail. Erkenne, ob darin "
            "eine konkrete Aktion fuer den Alltagshelfer steckt - "
            "z.B. ein neuer Vertrag, eine Preisaenderung zu einem "
            "bestehenden Vertrag, ein konkreter Termin oder ein Auftrag. "
            "Antworte AUSSCHLIESSLICH mit gueltigem JSON, ohne weitere "
            "Erklaerung, im Schema "
            '{"proposals": [{"target_capability": "<eine der: '
            f"{', '.join(sorted(cap_names)) or 'contracts.add, family.add_order'}>"
            '", "summary": "<kurz>", "payload": {<Argumente fuer die '
            'Capability>}}]}. Wenn nichts Konkretes erkennbar ist, '
            'gib {"proposals": []} zurueck.')
        try:
            raw, _ = self.llm.analyze_text(instruction, mail_text)
        except Exception:                                  # pragma: no cover
            return []
        candidates = self._parse_llm_proposals(raw)
        # Validierung gegen das Capability-Schema, bevor wir die Vorschlaege
        # ablegen. Halluzinierte Ziele und fehlende Pflichtparameter werden
        # gefiltert.
        return [p for p in candidates if self._is_valid_proposal(p)]

    def _is_valid_proposal(self, p: Proposal) -> bool:
        """True, wenn target_capability erlaubt ist und Pflichtparameter da sind."""
        if p.target_capability not in self._ALLOWED_LLM_TARGETS:
            return False
        if self._ctx is None or not self._ctx.has_capability(
                p.target_capability):
            return False
        required = self._required_params(p.target_capability)
        missing = [name for name in required if name not in p.payload]
        return not missing

    def _required_params(self, capability_name: str) -> list[str]:
        """Holt die Pflichtparameter einer Capability ueber die Registry."""
        registry = getattr(self._ctx, "_registry", None) \
            if self._ctx is not None else None
        if registry is None:
            return []
        cap = registry._capabilities.get(capability_name)
        if cap is None:
            return []
        return cap.required_params()

    @staticmethod
    def _parse_llm_proposals(raw: str) -> list[Proposal]:
        import json
        # Modelle umrahmen JSON oft mit ```json ... ``` oder ```...```.
        # Robust extrahieren: erst Code-Fence suchen, sonst Roh-Text.
        cleaned = raw.strip()
        fence = re.search(
            r"```(?:json)?\s*(?P<body>.*?)```",
            cleaned, flags=re.DOTALL | re.IGNORECASE)
        if fence is not None:
            cleaned = fence.group("body").strip()
        try:
            data = json.loads(cleaned)
        except Exception:
            # Letzter Versuch: das erste JSON-Objekt im Text suchen.
            match = re.search(r"\{[\s\S]*\}", cleaned)
            if match is None:
                return []
            try:
                data = json.loads(match.group(0))
            except Exception:
                return []
        result: list[Proposal] = []
        for item in data.get("proposals", []):
            if not isinstance(item, dict):
                continue
            target = item.get("target_capability")
            summary = item.get("summary") or "(ohne Beschreibung)"
            payload = item.get("payload") or {}
            if not target or not isinstance(payload, dict):
                continue
            result.append(Proposal(
                source="mail-llm",
                summary=summary,
                target_capability=target,
                payload=payload,
            ))
        return result

    def _cap_proposals(self) -> dict:
        offen = self.repo.list(status="offen")
        return {"count": len(offen),
                "proposals": [p.to_dict() for p in offen]}

    def _cap_accept_proposal(self, proposal_id: int) -> dict:
        proposal = self.repo.get(proposal_id)
        if proposal is None:
            return {"error": f"Vorschlag {proposal_id} nicht gefunden"}
        if proposal.status != "offen":
            return {"error": f"Vorschlag bereits '{proposal.status}'"}
        if self._ctx is None or not self._ctx.has_capability(
                proposal.target_capability):
            return {"error": f"Ziel '{proposal.target_capability}' "
                             f"nicht verfuegbar"}
        # Ziel-Capability ueber die Schnittstelle aufrufen -
        # das zustaendige Modul prueft die Daten selbst.
        result = self._ctx.call(proposal.target_capability, **proposal.payload)
        if "error" in result:
            return {"status": "Uebernahme fehlgeschlagen",
                    "error": result["error"]}
        self.repo.set_status(proposal_id, "uebernommen")
        return {"status": "Vorschlag uebernommen",
                "target": proposal.target_capability,
                "result": result}

    def _cap_reject_proposal(self, proposal_id: int) -> dict:
        proposal = self.repo.get(proposal_id)
        if proposal is None:
            return {"error": f"Vorschlag {proposal_id} nicht gefunden"}
        self.repo.set_status(proposal_id, "abgelehnt")
        return {"status": "Vorschlag abgelehnt"}

    # ---- .eml-Import + IMAP-Anbindung ----------------------------------
    def _cap_import_eml(self, path: str) -> dict:
        import email
        from pathlib import Path
        p = Path(path)
        if not p.exists():
            return {"error": f"Datei '{path}' nicht gefunden"}
        try:
            msg = email.message_from_bytes(p.read_bytes())
        except Exception as exc:
            return {"error": f".eml nicht lesbar: {exc}"}
        return self._cap_analyze_mail(self._extract_text(msg))

    def _cap_fetch_imap(self, folder: str = "INBOX",
                        limit: int = 10) -> dict:
        host = os.environ.get("ALLTAGSHELFER_IMAP_HOST")
        user = os.environ.get("ALLTAGSHELFER_IMAP_USER")
        pwd = os.environ.get("ALLTAGSHELFER_IMAP_PASS")
        if not (host and user and pwd):
            return {"status": "uebersprungen",
                    "hinweis": ("IMAP nicht konfiguriert. Setze "
                                 "ALLTAGSHELFER_IMAP_HOST/USER/PASS, um echte "
                                 "Mails zu lesen.")}
        try:
            import email
            import imaplib
            client = imaplib.IMAP4_SSL(host)
            client.login(user, pwd)
            client.select(folder)
            _typ, data = client.search(None, "UNSEEN")
            ids = data[0].split()[:limit]
            found = 0
            for mid in ids:
                _typ, msg_data = client.fetch(mid, "(RFC822)")
                raw_bytes = msg_data[0][1]              # type: ignore[index]
                msg = email.message_from_bytes(raw_bytes)  # type: ignore[arg-type]
                res = self._cap_analyze_mail(self._extract_text(msg))
                found += res.get("found", 0)
            client.logout()
            return {"status": "abgerufen", "checked": len(ids),
                    "found": found}
        except Exception as exc:
            return {"status": "fehler", "error": str(exc)}

    @staticmethod
    def _extract_text(msg) -> str:
        """
        Liefert den Plain-Text einer Mail. Bewusst robust gegen
        ungewoehnliche / kaputte Mails: get_payload(decode=True) kann
        None liefern (z.B. bei content-transfer-encoding-Problemen) -
        wir fangen das ab und liefern leeren Text statt zu crashen.
        """
        def _decode(part) -> str:
            data = part.get_payload(decode=True)
            if not data:
                return ""
            charset = part.get_content_charset() or "utf-8"
            try:
                return data.decode(charset, errors="replace")
            except (LookupError, AttributeError):
                # exotischer / unbekannter Charset
                return data.decode("utf-8", errors="replace")

        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    text = _decode(part)
                    if text:
                        return text
            return ""
        text = _decode(msg)
        if text:
            return text
        # Fallback: roher payload-Wert als String (z.B. unsigned 7bit)
        raw = msg.get_payload()
        return str(raw) if raw is not None else ""

    # ---- Mail-Analyse (regelbasiert) ----------------------------------
    def _analyze(self, mail_text: str) -> list[Proposal]:
        """Erkennt bekannte Muster und erzeugt passende Vorschlaege."""
        low = mail_text.lower()
        proposals: list[Proposal] = []

        # Muster 1: Preiserhoehung zu einem bestehenden Vertrag
        if any(k in low for k in ("preiserhöh", "preisanpassung",
                                  "preisänderung", "preis erhöh",
                                  "neuer preis")):
            amount = _extract_euro(mail_text)
            match = self._match_contract(mail_text)
            if match and amount:
                proposals.append(Proposal(
                    source="mail",
                    summary=(f"Preisaenderung fuer '{match['name']}' auf "
                             f"{amount:.2f} EUR uebernehmen"),
                    target_capability="contracts.report_price_change",
                    payload={"contract_id": match["id"], "new_cost": amount},
                ))

        # Muster 2: Bestaetigung eines neuen Vertrags
        if any(k in low for k in ("auftragsbestätigung", "vertragsbestätigung",
                                  "willkommen bei", "ihr neuer vertrag",
                                  "neuer vertrag")):
            amount = _extract_euro(mail_text)
            provider = self._guess_provider(mail_text)
            payload: dict = {
                "name": f"Vertrag {provider}" if provider else "Neuer Vertrag",
                "category": _guess_category(mail_text),
                "provider": provider,
            }
            if amount:
                payload["monthly_cost"] = amount
            proposals.append(Proposal(
                source="mail",
                summary=f"Neuen Vertrag '{payload['name']}' anlegen",
                target_capability="contracts.add",
                payload=payload,
            ))

        # Muster 3: Aufgabe / Termin -> Auftrag fuer den Haushalt
        if any(k in low for k in ("bitte erledigen", "zu erledigen",
                                  "aufgabe für", "termin am", "denk daran")):
            iso = _extract_date(mail_text)
            payload = {"title": "Aus Mail: " + self._first_line(mail_text)}
            if iso:
                payload["due_date"] = iso
            proposals.append(Proposal(
                source="mail",
                summary=f"Auftrag anlegen: {payload['title']}",
                target_capability="family.add_order",
                payload=payload,
            ))

        return proposals

    def _match_contract(self, mail_text: str) -> dict | None:
        """Sucht einen bestehenden Vertrag, dessen Anbieter in der Mail vorkommt."""
        if self._ctx is None or not self._ctx.has_capability("contracts.list"):
            return None
        result = self._ctx.call("contracts.list")
        low = mail_text.lower()
        for contract in result.get("contracts", []):
            provider = (contract.get("provider") or "").lower()
            if provider and provider in low:
                return contract
        return None

    def _guess_provider(self, mail_text: str) -> str:
        """Rät den Anbieter aus bekannten Namen im Text."""
        low = mail_text.lower()
        for hints in _CATEGORY_HINTS.values():
            for hint in hints:
                if hint in low and len(hint) > 3:
                    return hint.capitalize()
        return ""

    @staticmethod
    def _first_line(mail_text: str) -> str:
        for line in mail_text.splitlines():
            if line.strip():
                return line.strip()[:60]
        return "Mail"
