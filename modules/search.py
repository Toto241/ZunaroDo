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
from datetime import date

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


def _parse_date(value) -> date | None:
    """ISO-Datum (oder date) parsen. None bleibt None; Fehler -> ValueError."""
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


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
                            "Treffer kommen vereinheitlicht zurueck. Optional "
                            "filterbar nach Zeitraum, Status und Kategorie.",
                parameters={
                    "query": {"type": "string",
                              "description": "Suchbegriff (mindestens 2 "
                                             "Zeichen; entfaellt, wenn ein "
                                             "Filter gesetzt ist)"},
                    "limit": {"type": "integer",
                              "description": "Maximale Treffer (Standard: 50)"},
                    "date_from": {"type": "string",
                                  "description": "Nur Treffer ab diesem Datum "
                                                 "(ISO JJJJ-MM-TT)"},
                    "date_to": {"type": "string",
                                "description": "Nur Treffer bis zu diesem "
                                               "Datum (ISO JJJJ-MM-TT)"},
                    "status": {"type": "string",
                               "description": "Nur Treffer mit diesem Status "
                                              "(z.B. 'offen', 'active')"},
                    "category": {"type": "string",
                                 "description": "Nur Treffer dieser Kategorie"},
                },
                handler=self._cap_search,
            ),
        ]

    # ---- Handler -------------------------------------------------------
    def _cap_search(self, query: str = "", limit: int = 50,
                    date_from=None, date_to=None,
                    status: str | None = None,
                    category: str | None = None) -> dict:
        query = (query or "").strip()
        status = (status or "").strip().lower() or None
        category = (category or "").strip().lower() or None
        try:
            df = _parse_date(date_from)
            dt = _parse_date(date_to)
        except (ValueError, TypeError):
            return {"error": "Datum muss im Format JJJJ-MM-TT vorliegen"}

        has_filter = any(x is not None for x in (df, dt, status, category))
        if len(query) < 2 and not has_filter:
            return {"error": "Suchbegriff muss mindestens 2 Zeichen haben"}

        hits = [hit for hit, meta in self._collect_hits(query.lower())
                if self._matches_filters(meta, df, dt, status, category)]
        return {"query": query, "count": len(hits),
                "hits": [asdict(h) for h in hits[:limit]]}

    @staticmethod
    def _matches_filters(meta: dict, df, dt, status, category) -> bool:
        """Prueft einen Treffer gegen die optionalen Filter.

        Ein gesetzter Filter schliesst Treffer ohne das entsprechende Feld
        aus (z.B. Status-Filter -> nur Quellen, die ueberhaupt einen Status
        fuehren).
        """
        if category is not None:
            if meta.get("category") is None:
                return False
            if meta["category"].lower() != category:
                return False
        if status is not None:
            if meta.get("status") is None:
                return False
            if meta["status"].lower() != status:
                return False
        if df is not None or dt is not None:
            d = meta.get("date")
            if d is None:
                return False
            if df is not None and d < df:
                return False
            if dt is not None and d > dt:
                return False
        return True

    # ---- Treffer aus den einzelnen Repositories -----------------------
    def _collect_hits(self, query: str):
        """Liefert (SearchHit, meta)-Tupel. 'meta' traegt die Felder fuer die
        optionalen Filter (category/status/date) - None, wo eine Quelle das
        jeweilige Feld nicht kennt."""
        # Vertraege
        for c in self.contracts.list_all(only_active=False):
            haystack = " ".join(filter(None, [
                c.name, c.provider, c.customer_number, c.notes,
                c.owner_name, c.category])).lower()
            if query in haystack:
                yield (SearchHit(
                    source="contracts", entity_id=c.id or 0,
                    title=f"{c.name} ({c.provider or '-'})",
                    detail=(f"{c.monthly_cost:.2f} EUR/Monat, "
                             f"Kategorie {c.category}")),
                    {"category": c.category, "status": c.status,
                     "date": c.start_date})

        # Ausgaben
        for e in self.expenses.list_all():
            haystack = " ".join(filter(None, [
                e.description, e.category, e.owner_name])).lower()
            if query in haystack:
                yield (SearchHit(
                    source="expenses", entity_id=e.id or 0,
                    title=e.description,
                    detail=(f"{e.amount:.2f} EUR, {e.category}, "
                             + (e.spent_on.isoformat() if e.spent_on else "?"))),
                    {"category": e.category, "status": None,
                     "date": e.spent_on})

        # Termine
        for cal in self.calendar.list_all():
            haystack = " ".join(filter(None, [
                cal.title, cal.description, cal.category,
                cal.person_name])).lower()
            if query in haystack:
                yield (SearchHit(
                    source="calendar", entity_id=cal.id or 0,
                    title=cal.title,
                    detail=f"{cal.category} - {cal.due_date.isoformat()}"),
                    {"category": cal.category, "status": None,
                     "date": cal.due_date})

        # Familie
        for m in self.family.list_members():
            haystack = " ".join(filter(None, [m.name, m.role])).lower()
            if query in haystack:
                yield (SearchHit(
                    source="family", entity_id=m.id or 0,
                    title=m.name, detail=m.role),
                    {"category": None, "status": None, "date": None})

        # Auftraege
        for o in self.family.list_orders():
            haystack = " ".join(filter(None, [
                o.title, o.description, o.assignee_name])).lower()
            if query in haystack:
                yield (SearchHit(
                    source="orders", entity_id=o.id or 0,
                    title=o.title,
                    detail=(f"{o.status}, zugewiesen an "
                             f"{o.assignee_name or 'niemand'}")),
                    {"category": None, "status": o.status,
                     "date": o.due_date})

        # Sozialkontakte
        for s in self.social.list_all():
            haystack = " ".join(filter(None, [
                s.name, s.relation, s.notes])).lower()
            if query in haystack:
                yield (SearchHit(
                    source="social", entity_id=s.id or 0,
                    title=s.name, detail=s.relation or "(Kontakt)"),
                    {"category": None, "status": None,
                     "date": s.last_contacted})

        # Vorschlaege
        for p in self.proposals.list():
            haystack = " ".join(filter(None, [
                p.summary, p.target_capability, p.source])).lower()
            if query in haystack:
                yield (SearchHit(
                    source="proposals", entity_id=p.id or 0,
                    title=p.summary,
                    detail=f"{p.status} -> {p.target_capability}"),
                    {"category": None, "status": p.status,
                     "date": p.created_at.date() if p.created_at else None})

        # Notizen
        if self.notes is not None:
            for n in self.notes.list_all():
                haystack = " ".join(filter(None, [
                    n.title, n.content, n.entity_type])).lower()
                if query in haystack:
                    target = (f"-> {n.entity_type}#{n.entity_id}"
                               if n.entity_type else "(frei)")
                    yield (SearchHit(
                        source="notes", entity_id=n.id or 0,
                        title=n.title, detail=target),
                        {"category": None, "status": None, "date": None})
