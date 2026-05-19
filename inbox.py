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

import re
from datetime import date

from core.interface import Capability, ModuleContext, ModuleInterface
from database import ProposalRepository
from models import Proposal

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

    def __init__(self, repo: ProposalRepository):
        self.repo = repo
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
            ),
            Capability(
                name="inbox.reject_proposal",
                description="Lehnt einen Vorschlag ab (wird nicht uebernommen).",
                parameters={
                    "proposal_id": {"type": "integer", "_required": True,
                                    "description": "ID des Vorschlags"},
                },
                handler=self._cap_reject_proposal,
            ),
        ]

    # ---- Handler -------------------------------------------------------
    def _cap_analyze_mail(self, mail_text: str) -> dict:
        proposals = self._analyze(mail_text)
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
            payload = {
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
