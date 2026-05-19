"""
Modul Volltextsuche.

Sucht querbeet ueber alle relevanten Tabellen mit LIKE-Pattern. Bewusst
einfach gehalten - kein FTS5-Index. Bei den im Familien-Maßstab
erwarteten Mengen (hunderte bis tausende Eintraege) reicht das.

Liefert einheitlich getypte Treffer mit:
  - source        Tabelle / Modul-Bezeichner
  - entity_id     ID innerhalb dieses Moduls
  - title         menschenlesbare Hauptzeile
  - detail        zusaetzlicher Kontext
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

from core.interface import Capability, ModuleInterface
from database import (CalendarRepository, ContractRepository,
                      ExpenseRepository, FamilyRepository, NoteRepository,
                      ProposalRepository, SocialRepository)


@dataclass
class SearchHit:
    source: str
    entity_id: int
    title: str
    detail: str = ""


class SearchModule(ModuleInterface):
    """Querbeet-Suche ueber alle wichtigen Datenbestaende."""

    def __init__(self,
                 contracts: ContractRepository,
                 expenses: ExpenseRepository,
                 calendar: CalendarRepository,
                 family: FamilyRepository,
                 social: SocialRepository,
                 proposals: ProposalRepository,
                 notes: NoteRepository | None = None):
        self.contracts = contracts
        self.expenses = expenses
        self.calendar = calendar
        self.family = family
        self.social = social
        self.proposals = proposals
        self.notes = notes

    @property
    def module_id(self) -> str:
        return "search"

    @property
    def display_name(self) -> str:
        return "Volltextsuche"

    def get_context_summary(self) -> str:
        return "Suche ueber 'system.search'."

    def get_capabilities(self) -> list[Capability]:
        return [
            Capability(
                name="system.search",
                description="Sucht querbeet in Vertraegen, Ausgaben, "
                            "Terminen, Familienmitgliedern, Kontakten und "
                            "Vorschlaegen. Eingabe ist ein Stichwort - "
                            "Treffer kommen vereinheitlicht zurueck.",
                parameters={
                    "query": {"type": "string", "_required": True,
                              "description": "Suchbegriff (mindestens 2 Zeichen)"},
                    "limit": {"type": "integer",
                              "description": "Maximale Treffer (Standard: 50)"},
                },
                handler=self._cap_search,
            ),
        ]

    # ---- Handler -------------------------------------------------------
    def _cap_search(self, query: str, limit: int = 50) -> dict:
        query = (query or "").strip()
        if len(query) < 2:
            return {"error": "Suchbegriff muss mindestens 2 Zeichen haben"}
        hits = list(self._collect_hits(query.lower()))
        return {"query": query, "count": len(hits),
                "hits": [asdict(h) for h in hits[:limit]]}

    # ---- Treffer aus den einzelnen Repositories -----------------------
    def _collect_hits(self, query: str):
        # Vertraege
        for c in self.contracts.list_all(only_active=False):
            haystack = " ".join(filter(None, [
                c.name, c.provider, c.customer_number, c.notes,
                c.owner_name, c.category])).lower()
            if query in haystack:
                yield SearchHit(
                    source="contracts", entity_id=c.id or 0,
                    title=f"{c.name} ({c.provider or '-'})",
                    detail=(f"{c.monthly_cost:.2f} EUR/Monat, "
                             f"Kategorie {c.category}"))

        # Ausgaben
        for e in self.expenses.list_all():
            haystack = " ".join(filter(None, [
                e.description, e.category, e.owner_name])).lower()
            if query in haystack:
                yield SearchHit(
                    source="expenses", entity_id=e.id or 0,
                    title=e.description,
                    detail=(f"{e.amount:.2f} EUR, {e.category}, "
                             + (e.spent_on.isoformat() if e.spent_on else "?")))

        # Termine
        for cal in self.calendar.list_all():
            haystack = " ".join(filter(None, [
                cal.title, cal.description, cal.category,
                cal.person_name])).lower()
            if query in haystack:
                yield SearchHit(
                    source="calendar", entity_id=cal.id or 0,
                    title=cal.title,
                    detail=f"{cal.category} - {cal.due_date.isoformat()}")

        # Familie
        for m in self.family.list_members():
            haystack = " ".join(filter(None, [m.name, m.role])).lower()
            if query in haystack:
                yield SearchHit(
                    source="family", entity_id=m.id or 0,
                    title=m.name, detail=m.role)

        # Auftraege
        for o in self.family.list_orders():
            haystack = " ".join(filter(None, [
                o.title, o.description, o.assignee_name])).lower()
            if query in haystack:
                yield SearchHit(
                    source="orders", entity_id=o.id or 0,
                    title=o.title,
                    detail=(f"{o.status}, zugewiesen an "
                             f"{o.assignee_name or 'niemand'}"))

        # Sozialkontakte
        for s in self.social.list_all():
            haystack = " ".join(filter(None, [
                s.name, s.relation, s.notes])).lower()
            if query in haystack:
                yield SearchHit(
                    source="social", entity_id=s.id or 0,
                    title=s.name, detail=s.relation or "(Kontakt)")

        # Vorschlaege
        for p in self.proposals.list():
            haystack = " ".join(filter(None, [
                p.summary, p.target_capability, p.source])).lower()
            if query in haystack:
                yield SearchHit(
                    source="proposals", entity_id=p.id or 0,
                    title=p.summary,
                    detail=f"{p.status} -> {p.target_capability}")

        # Notizen
        if self.notes is not None:
            for n in self.notes.list_all():
                haystack = " ".join(filter(None, [
                    n.title, n.content, n.entity_type])).lower()
                if query in haystack:
                    target = (f"-> {n.entity_type}#{n.entity_id}"
                               if n.entity_type else "(frei)")
                    yield SearchHit(
                        source="notes", entity_id=n.id or 0,
                        title=n.title, detail=target)
