"""
Modul A - Vertrags- & Fristenmanager.

Dieses Modul implementiert ModuleInterface. Es kennt die Datenschicht,
aber NICHT den KI-Assistenten. Es stellt dem Assistenten nur
Faehigkeiten (Capabilities) bereit.

Die Fristenberechnung beruecksichtigt Mindestlaufzeit, Kuendigungsfrist
und automatische Verlaengerung - generisch genug fuer Alt- und
Neuvertraege (Gesetz fuer faire Verbrauchervertraege).
"""
from __future__ import annotations

from datetime import date

from core.interface import Capability, ModuleContext, ModuleInterface
from database import ContractRepository
from models import Contract, Deadline, Event
from services.output import OutputService, slugify


# ---------------------------------------------------------------------
# Datums-Hilfsfunktionen (bewusst ohne externe Abhaengigkeit)
# ---------------------------------------------------------------------
def _add_months(d: date, months: int) -> date:
    """Addiert (oder subtrahiert) Monate datumssicher."""
    total = d.month - 1 + months
    year = d.year + total // 12
    month = total % 12 + 1
    leap = (year % 4 == 0 and year % 100 != 0) or year % 400 == 0
    days_in_month = [31, 29 if leap else 28, 31, 30, 31, 30,
                     31, 31, 30, 31, 30, 31]
    day = min(d.day, days_in_month[month - 1])
    return date(year, month, day)


def next_cancellation_date(contract: Contract, today: date | None = None) -> date | None:
    """
    Berechnet das naechste Datum, bis zu dem gekuendigt werden muss,
    damit sich der Vertrag NICHT erneut verlaengert.
    """
    if not contract.start_date:
        return None
    today = today or date.today()

    # Ende der aktuellen Laufzeit ermitteln
    term_end = _add_months(contract.start_date, contract.minimum_term_months)
    while term_end <= today:
        term_end = _add_months(term_end, max(contract.auto_renew_months, 1))

    deadline = _add_months(term_end, -contract.notice_period_months)
    # Falls die Frist schon verstrichen ist -> naechster Zyklus
    if deadline < today:
        term_end = _add_months(term_end, max(contract.auto_renew_months, 1))
        deadline = _add_months(term_end, -contract.notice_period_months)
    return deadline


def build_cancellation_letter(contract: Contract, deadline: date | None,
                              sender_name: str, sender_address: str,
                              sender_city: str) -> str:
    """Erzeugt den Text eines fristgerechten Kuendigungsschreibens."""
    today_str = date.today().strftime("%d.%m.%Y")
    deadline_str = (deadline.strftime("%d.%m.%Y") if deadline
                    else "nächstmöglichen Termin")
    kundennr = (f"Kunden-/Vertragsnummer: {contract.customer_number}"
                if contract.customer_number
                else "Kunden-/Vertragsnummer: (bitte ergänzen)")
    return (
        f"{sender_name}\n"
        f"{sender_address}\n\n\n"
        f"{contract.provider or '(Anbieter)'}\n\n\n"
        f"{sender_city}, den {today_str}\n\n\n"
        f"Kündigung: {contract.name}\n"
        f"{kundennr}\n\n"
        "Sehr geehrte Damen und Herren,\n\n"
        "hiermit kündige ich den oben genannten Vertrag fristgerecht zum\n"
        f"nächstmöglichen Termin. Nach meiner Berechnung ist dies der\n"
        f"{deadline_str}. Sollte eine Kündigung zu diesem Datum nicht\n"
        "möglich sein, bitte ich um Kündigung zum nächstmöglichen Zeitpunkt.\n\n"
        "Bitte bestätigen Sie mir den Eingang dieser Kündigung sowie das\n"
        "genaue Vertragsende schriftlich.\n\n"
        "Mit freundlichen Grüßen\n\n\n\n"
        f"{sender_name}\n"
    )


# ---------------------------------------------------------------------
#  Affiliate-Empfehlungen (statisch, kein Tracking)
# ---------------------------------------------------------------------
# Schluessel-Worte im Vertragsnamen / Kategorie / Anbieter -> Liste
# von Partner-IDs aus services.licensing.AFFILIATE_PARTNERS.
# Bewusst pauschal gehalten: bei Kuendigung kommen immer beide
# allgemeinen Anlaufstellen (Verbraucherzentrale + Stiftung Warentest)
# - das ist der unaufdringliche Mittelweg zwischen 'gar keine Hilfe'
# und 'Affiliate-Spam'.
_DEFAULT_PARTNER_KEYS: tuple[str, ...] = ("verbraucherzentrale",
                                            "stiftung_warentest")


def _affiliate_suggestions(contract: Contract) -> list[dict]:
    """Liefert eine kleine Liste von Tarifvergleichs-Empfehlungen."""
    from services.licensing import AFFILIATE_PARTNERS
    return [{"name": k.replace("_", " ").title(),
             "url": AFFILIATE_PARTNERS[k]}
            for k in _DEFAULT_PARTNER_KEYS
            if k in AFFILIATE_PARTNERS]


def _format_affiliate_block(suggestions: list[dict]) -> str:
    """Fuegt einen kurzen, deutlich abgesetzten Hinweisblock an Brief/PDF."""
    if not suggestions:
        return ""
    lines = ["--",
             "Wenn du nach einem Nachfolge-Tarif suchst, hilft dir bei",
             "unabhaengigen Vergleichen z.B.:"]
    for s in suggestions:
        lines.append(f"  * {s['name']}: {s['url']}")
    lines.append("")
    lines.append("(Diese Hinweise sind nicht personalisiert und werden")
    lines.append(" nicht getrackt - sie stehen statisch in der App.)")
    return "\n".join(lines)


class ContractModule(ModuleInterface):
    """Modul A als steckbares Fachmodul."""

    def __init__(self, repo: ContractRepository,
                 output_service: OutputService | None = None):
        self.repo = repo
        self.output = output_service        # optional: fuer PDF/Mail-Ausgabe
        self._ctx: ModuleContext | None = None

    def on_register(self, context: ModuleContext) -> None:
        self._ctx = context

    def _cleanup_notes(self, entity_id: int) -> None:
        """Verwaiste Notizen aufraeumen, falls Notes-Modul aktiv ist."""
        if (self._ctx is not None
                and self._ctx.has_capability("notes.cleanup_for_entity")):
            self._ctx.call("notes.cleanup_for_entity",
                            entity_type="contracts", entity_id=entity_id)

    # ---- Pflichtangaben des Interface ---------------------------------
    @property
    def module_id(self) -> str:
        return "contracts"

    @property
    def display_name(self) -> str:
        return "Vertrags- & Fristenmanager"

    def get_context_summary(self) -> str:
        contracts = self.repo.list_all(only_active=True)
        if not contracts:
            return "Es sind noch keine Vertraege erfasst."
        total = sum(c.monthly_cost for c in contracts)
        urgent = [d for d in self._all_deadlines() if (d.days_remaining or 999) <= 30]
        text = (f"{len(contracts)} aktive Vertraege, "
                f"{total:.2f} EUR/Monat gesamt.")
        if urgent:
            text += f" {len(urgent)} Frist(en) in den naechsten 30 Tagen!"
        return text

    def get_events(self, horizon_days: int = 90) -> list[Event]:
        """Kuendigungsfristen werden zu Dashboard-Ereignissen."""
        events: list[Event] = []
        for d in self._all_deadlines():
            days = d.days_remaining
            if days is None or days < 0 or days > horizon_days:
                continue
            events.append(Event(
                title=f"Kuendigungsfrist: {d.contract_name}",
                due_date=d.due_date,
                module_id=self.module_id,
                module_name=self.display_name,
                category="frist",
                detail="Letzter Termin zum Kuendigen - sonst verlaengert "
                       "sich der Vertrag automatisch.",
                days_remaining=days,
            ))
        return events

    # ---- Faehigkeiten, die der Assistent aufrufen darf ----------------
    def get_capabilities(self) -> list[Capability]:
        return [
            Capability(
                name="contracts.list",
                description="Listet alle aktiven Vertraege mit Kosten auf. "
                            "Optional nach Kategorie filterbar.",
                parameters={
                    "category": {"type": "string",
                                 "description": "Nur Vertraege dieser "
                                                "Kategorie"},
                },
                handler=self._cap_list,
            ),
            Capability(
                name="contracts.add",
                description="Legt einen neuen Vertrag an.",
                parameters={
                    "name": {"type": "string", "_required": True,
                             "description": "Name des Vertrags"},
                    "category": {"type": "string", "_required": True,
                                 "description": "versicherung, mobilfunk, "
                                                "streaming, strom oder sonstiges"},
                    "provider": {"type": "string", "description": "Anbieter"},
                    "customer_number": {"type": "string",
                                        "description": "Kunden- oder "
                                                       "Vertragsnummer"},
                    "start_date": {"type": "string",
                                   "description": "Startdatum ISO (YYYY-MM-DD)"},
                    "minimum_term_months": {"type": "integer",
                                            "description": "Mindestlaufzeit in Monaten"},
                    "notice_period_months": {"type": "integer",
                                             "description": "Kuendigungsfrist in Monaten"},
                    "auto_renew_months": {"type": "integer",
                                          "description": "Verlaengerung in Monaten, "
                                                         "falls nicht gekuendigt wird "
                                                         "(z.B. 1 = monatlich kuendbar)"},
                    "monthly_cost": {"type": "number",
                                     "description": "Monatliche Kosten in EUR"},
                    "owner_id": {"type": "integer",
                                 "description": "Optional: ID des Haushalts"
                                                "mitglieds, dem der Vertrag "
                                                "gehoert (siehe family.members)"},
                },
                handler=self._cap_add,
            ),
            Capability(
                name="contracts.set_owner",
                description="Ordnet einen Vertrag einer Person zu (oder loest die "
                            "Zuordnung mit owner_id=0).",
                parameters={
                    "contract_id": {"type": "integer", "_required": True,
                                    "description": "ID des Vertrags"},
                    "owner_id": {"type": "integer",
                                 "description": "ID der Person (0 = keine)"},
                },
                handler=self._cap_set_owner,
                destructive=True,
            ),
            Capability(
                name="contracts.upcoming_deadlines",
                description="Liefert anstehende Kuendigungsfristen, optional "
                            "begrenzt auf die naechsten N Tage.",
                parameters={
                    "within_days": {"type": "integer",
                                    "description": "Nur Fristen innerhalb so "
                                                   "vieler Tage (Standard: alle)"},
                },
                handler=self._cap_deadlines,
            ),
            Capability(
                name="contracts.report_price_change",
                description="Vermerkt eine Preisaenderung fuer einen Vertrag "
                            "und speichert sie in der Preis-Historie.",
                parameters={
                    "contract_id": {"type": "integer", "_required": True,
                                    "description": "ID des Vertrags"},
                    "new_cost": {"type": "number", "_required": True,
                                 "description": "Neuer Monatspreis in EUR"},
                },
                handler=self._cap_price_change,
                destructive=True,
            ),
            Capability(
                name="contracts.delete",
                description="Verschiebt einen Vertrag in den Papierkorb "
                            "(Soft-Delete). Mit 'contracts.restore' "
                            "wiederherstellbar; endgueltig erst durch "
                            "'contracts.purge'.",
                parameters={
                    "contract_id": {"type": "integer", "_required": True,
                                    "description": "ID des Vertrags"},
                },
                handler=self._cap_delete,
                destructive=True,
            ),
            Capability(
                name="contracts.restore",
                description="Stellt einen geloeschten Vertrag wieder her.",
                parameters={
                    "contract_id": {"type": "integer", "_required": True,
                                    "description": "ID des Vertrags"},
                },
                handler=self._cap_restore,
                destructive=True,
            ),
            Capability(
                name="contracts.purge",
                description="Endgueltige Loeschung eines Vertrags (kein "
                            "Restore mehr moeglich).",
                parameters={
                    "contract_id": {"type": "integer", "_required": True,
                                    "description": "ID des Vertrags"},
                },
                handler=self._cap_purge,
                destructive=True,
            ),
            Capability(
                name="contracts.list_deleted",
                description="Listet die im Papierkorb liegenden Vertraege.",
                parameters={},
                handler=self._cap_list_deleted,
            ),
            Capability(
                name="contracts.generate_cancellation",
                description="Erstellt ein fristgerechtes Kuendigungsschreiben "
                            "fuer einen Vertrag - als druckbares PDF und/oder "
                            "Mail-Entwurf.",
                parameters={
                    "contract_id": {"type": "integer", "_required": True,
                                    "description": "ID des zu kuendigenden Vertrags"},
                    "sender_name": {"type": "string",
                                    "description": "Name des Absenders"},
                    "sender_address": {"type": "string",
                                       "description": "Anschrift des Absenders"},
                    "sender_city": {"type": "string",
                                    "description": "Ort fuer die Datumszeile"},
                    "recipient_email": {"type": "string",
                                        "description": "Mailadresse des Anbieters "
                                                       "(fuer den Mail-Entwurf)"},
                    "channel": {"type": "string",
                                "description": "pdf, email oder both "
                                               "(Standard: both)"},
                },
                handler=self._cap_generate_cancellation,
            ),
        ]

    # ---- Handler-Implementierungen ------------------------------------
    def _cap_list(self, category: str | None = None) -> dict:
        contracts = self.repo.list_all(only_active=True)
        if category:
            wanted = category.strip().lower()
            contracts = [c for c in contracts
                         if (c.category or "").lower() == wanted]
        return {
            "count": len(contracts),
            "total_monthly_cost": round(sum(c.monthly_cost for c in contracts), 2),
            "contracts": [c.to_dict() for c in contracts],
        }

    def _cap_add(self, name: str, category: str, provider: str = "",
                 customer_number: str = "",
                 start_date: str | None = None,
                 minimum_term_months: int = 12,
                 notice_period_months: int = 3,
                 auto_renew_months: int = 12,
                 monthly_cost: float = 0.0,
                 owner_id: int | None = None) -> dict:
        contract = Contract(
            name=name,
            category=category,
            provider=provider,
            customer_number=customer_number,
            start_date=date.fromisoformat(start_date) if start_date else None,
            minimum_term_months=minimum_term_months,
            notice_period_months=notice_period_months,
            auto_renew_months=auto_renew_months,
            monthly_cost=monthly_cost,
            owner_id=owner_id if owner_id else None,
        )
        saved = self.repo.add(contract)
        if saved.id is not None:
            saved = self.repo.get(saved.id) or saved
        return {"status": "angelegt", "contract": saved.to_dict()}

    def _cap_delete(self, contract_id: int) -> dict:
        """Standard-Loeschen ist jetzt Soft-Delete (Papierkorb)."""
        existed = self.repo.soft_delete(contract_id)
        if not existed:
            return {"error": f"Vertrag {contract_id} nicht gefunden "
                              "oder bereits im Papierkorb"}
        return {"status": "im papierkorb", "contract_id": contract_id}

    def _cap_restore(self, contract_id: int) -> dict:
        if not self.repo.restore(contract_id):
            return {"error": f"Vertrag {contract_id} ist nicht im "
                              "Papierkorb"}
        return {"status": "wiederhergestellt", "contract_id": contract_id}

    def _cap_purge(self, contract_id: int) -> dict:
        existed = self.repo.delete(contract_id)
        if not existed:
            return {"error": f"Vertrag {contract_id} nicht gefunden"}
        self._cleanup_notes(contract_id)
        return {"status": "endgueltig geloescht", "contract_id": contract_id}

    def _cap_list_deleted(self) -> dict:
        items = self.repo.list_deleted()
        return {"count": len(items),
                "contracts": [c.to_dict() for c in items]}

    def _cap_set_owner(self, contract_id: int, owner_id: int = 0) -> dict:
        contract = self.repo.get(contract_id)
        if contract is None:
            return {"error": f"Vertrag {contract_id} nicht gefunden"}
        self.repo.set_owner(contract_id, owner_id if owner_id else None)
        updated = self.repo.get(contract_id)
        return {"status": "zugeordnet",
                "contract": updated.to_dict() if updated else None}

    def _cap_generate_cancellation(self, contract_id: int,
                                   sender_name: str = "(Ihr Name)",
                                   sender_address: str = "(Ihre Anschrift)",
                                   sender_city: str = "(Ort)",
                                   recipient_email: str = "",
                                   channel: str = "both") -> dict:
        contract = self.repo.get(contract_id)
        if contract is None:
            return {"error": f"Vertrag {contract_id} nicht gefunden"}

        deadline = next_cancellation_date(contract)
        letter = build_cancellation_letter(
            contract, deadline, sender_name, sender_address, sender_city)
        suggestions = _affiliate_suggestions(contract)
        result: dict = {
            "status": "Kuendigungsschreiben erstellt",
            "contract": contract.name,
            "cancellation_date": deadline.isoformat() if deadline else None,
            "letter_text": letter,
            "affiliate_suggestions": suggestions,
        }

        # Ausgabe ueber den OutputService (Drucken / Mail)
        if self.output is None:
            result["hinweis"] = ("Kein Ausgabedienst angebunden - nur Text "
                                 "erzeugt.")
            return result

        base = f"kuendigung_{slugify(contract.name)}"
        title = f"Kündigung {contract.name}"
        # Affiliate-Block ans PDF und an die Mail anhaengen - statische
        # Empfehlungen ohne Tracking, passt zur Privacy-Positionierung.
        body = letter
        if suggestions:
            body = letter + "\n\n" + _format_affiliate_block(suggestions)
        if channel in ("pdf", "both"):
            result["pdf_path"] = self.output.write_pdf(
                title, body, base + ".pdf")
        if channel in ("email", "both"):
            result["email_draft_path"] = self.output.write_email_draft(
                recipient_email, title, body, base + ".eml")
        return result

    def _cap_deadlines(self, within_days: int | None = None) -> dict:
        deadlines = self._all_deadlines()
        if within_days is not None:
            deadlines = [d for d in deadlines
                         if d.days_remaining is not None
                         and d.days_remaining <= within_days]
        deadlines.sort(key=lambda d: d.due_date)
        return {"count": len(deadlines),
                "deadlines": [d.to_dict() for d in deadlines]}

    def _cap_price_change(self, contract_id: int, new_cost: float) -> dict:
        old = self.repo.get(contract_id)
        if old is None:
            return {"error": f"Vertrag {contract_id} nicht gefunden"}
        self.repo.update_cost(contract_id, new_cost)
        diff = new_cost - old.monthly_cost
        return {
            "status": "Preisaenderung gespeichert",
            "contract": old.name,
            "old_cost": old.monthly_cost,
            "new_cost": new_cost,
            "difference": round(diff, 2),
            "is_increase": diff > 0,
        }

    # ---- intern --------------------------------------------------------
    def _all_deadlines(self) -> list[Deadline]:
        today = date.today()
        result: list[Deadline] = []
        for c in self.repo.list_all(only_active=True):
            due = next_cancellation_date(c, today)
            if due is None:
                continue
            result.append(Deadline(
                contract_id=c.id or 0,
                type="cancellation",
                due_date=due,
                title=f"Kuendigungsfrist {c.name}",
                contract_name=c.name,
                days_remaining=(due - today).days,
            ))
        return result
