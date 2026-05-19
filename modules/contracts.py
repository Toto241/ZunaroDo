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

from core.interface import Capability, ModuleInterface
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


class ContractModule(ModuleInterface):
    """Modul A als steckbares Fachmodul."""

    def __init__(self, repo: ContractRepository,
                 output_service: OutputService | None = None):
        self.repo = repo
        self.output = output_service        # optional: fuer PDF/Mail-Ausgabe

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
                description="Listet alle aktiven Vertraege mit Kosten auf.",
                parameters={},
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
                description="Loescht einen Vertrag samt Preis-Historie "
                            "endgueltig. Fuer Statuswechsel (gekuendigt) "
                            "stattdessen 'contracts.report_price_change' "
                            "mit 0.0 oder eine Statusspalte verwenden.",
                parameters={
                    "contract_id": {"type": "integer", "_required": True,
                                    "description": "ID des Vertrags"},
                },
                handler=self._cap_delete,
                destructive=True,
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
    def _cap_list(self) -> dict:
        contracts = self.repo.list_all(only_active=True)
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
        existed = self.repo.delete(contract_id)
        if not existed:
            return {"error": f"Vertrag {contract_id} nicht gefunden"}
        return {"status": "geloescht", "contract_id": contract_id}

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
        result: dict = {
            "status": "Kuendigungsschreiben erstellt",
            "contract": contract.name,
            "cancellation_date": deadline.isoformat() if deadline else None,
            "letter_text": letter,
        }

        # Ausgabe ueber den OutputService (Drucken / Mail)
        if self.output is None:
            result["hinweis"] = ("Kein Ausgabedienst angebunden - nur Text "
                                 "erzeugt.")
            return result

        base = f"kuendigung_{slugify(contract.name)}"
        title = f"Kündigung {contract.name}"
        if channel in ("pdf", "both"):
            result["pdf_path"] = self.output.write_pdf(
                title, letter, base + ".pdf")
        if channel in ("email", "both"):
            result["email_draft_path"] = self.output.write_email_draft(
                recipient_email, title, letter, base + ".eml")
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
