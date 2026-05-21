"""
Pure-Logic-Helper fuer die Mobile-UI.

Diese Datei haengt *nicht* von Kivy ab - sie ist unter unittest
einzeln testbar. Hier landet alles, was zwischen Registry-Capabilities
und dem konkreten Screen liegt: Formatierung, Sortierung, Filterung,
Listen-Aggregation.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Iterable

from services.i18n import AUTO, I18n, resolve_language


def format_currency(amount: float | int, currency: str = "EUR") -> str:
    """`12.5 EUR` -> `12,50 €` (Deutsch)."""
    try:
        val = float(amount)
    except (TypeError, ValueError):
        return ""
    symbol = "€" if currency.upper() == "EUR" else currency
    formatted = f"{val:,.2f}"
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{formatted} {symbol}"


def days_until(iso_date: str | None) -> int | None:
    """Tage von heute bis zum ISO-Datum. None wenn ungueltig."""
    if not iso_date:
        return None
    try:
        d = date.fromisoformat(iso_date)
    except (TypeError, ValueError):
        return None
    return (d - date.today()).days


def relative_when(iso_date: str | None) -> str:
    """`heute` / `morgen` / `in 5 Tagen` / `vor 3 Tagen`."""
    days = days_until(iso_date)
    if days is None:
        return ""
    if days == 0:
        return "heute"
    if days == 1:
        return "morgen"
    if days == -1:
        return "gestern"
    if days < 0:
        return f"vor {-days} Tagen"
    return f"in {days} Tagen"


def urgency_color(days: int | None) -> str:
    """
    Material-Color-Hint fuer Fristen:
      <= 7  Tage  -> 'error'
      <=30 Tage  -> 'warning'
      sonst      -> 'normal'
    """
    if days is None:
        return "normal"
    if days < 0 or days <= 7:
        return "error"
    if days <= 30:
        return "warning"
    return "normal"


def dashboard_summary(registry_dispatch) -> dict[str, Any]:
    """
    Sammelt die wichtigsten Phone-Kacheln in einem Aufruf.

    `registry_dispatch` ist die Funktion `registry.dispatch(name, args)`
    - so kann der Aufrufer auch eine Mock-Funktion uebergeben.
    """
    out: dict[str, Any] = {}
    try:
        contracts = registry_dispatch("contracts.list", {})
        out["contracts_count"] = contracts.get("count", 0)
        out["monthly_total"] = contracts.get("total_monthly_cost", 0.0)
    except Exception:
        out["contracts_count"] = 0
        out["monthly_total"] = 0.0
    try:
        deadlines = registry_dispatch(
            "contracts.upcoming_deadlines", {"within_days": 30})
        out["upcoming_deadlines"] = deadlines.get("deadlines", [])[:3]
    except Exception:
        out["upcoming_deadlines"] = []
    try:
        events = registry_dispatch("calendar.list_upcoming", {"days": 14})
        out["upcoming_events"] = events.get("events", [])[:5]
    except Exception:
        out["upcoming_events"] = []
    return out


def week_agenda(registry_dispatch, horizon_days: int = 7) -> dict[str, Any]:
    """Holt die Tages-/Wochenuebersicht (`system.agenda`) phone-tauglich.

    Liefert immer ein robustes Dict mit `days` (Liste von Tagen, jeweils
    mit `date`/`weekday`/`events`), `overdue` und `total` - auch wenn der
    Aufruf fehlschlaegt (dann leer). `registry_dispatch` kann ein Mock sein.
    """
    try:
        result = registry_dispatch("system.agenda",
                                   {"horizon_days": horizon_days}) or {}
    except Exception:
        result = {}
    return {
        "days": result.get("days", []),
        "overdue": result.get("overdue", []),
        "overdue_count": result.get("overdue_count", len(
            result.get("overdue", []))),
        "total": result.get("total", 0),
    }


def truncate(text: str, max_len: int = 40) -> str:
    """Phone-Listen brauchen kurze Strings."""
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


#: Label fuer die automatische Geraetesprache (zweisprachig, da es vor
#: der Sprachwahl angezeigt wird).
AUTO_LANGUAGE_LABEL = "Automatisch / Auto"


def language_menu_items(current: str | None) -> list[dict[str, Any]]:
    """
    Baut die Eintraege fuer den Sprachumschalter.

    `current` ist der gespeicherte Setting-Wert ('auto', 'de', 'fr' ...);
    None/"" wird wie die Default-Sprache behandelt.

    Liefert eine Liste von Dicts ``{"code", "label", "selected"}``. Der
    erste Eintrag ist immer 'auto' (Geraetesprache), danach folgen alle
    Sprachen, fuer die ein Locale-File existiert, in Registry-Reihenfolge.
    Genau ein Eintrag ist `selected=True`.
    """
    raw = (current or I18n.DEFAULT_LANGUAGE).strip().lower()
    # 'auto' bleibt 'auto'; jeder andere Wert wird auf eine tatsaechlich
    # unterstuetzte Sprache aufgeloest (unbekannt -> Default), damit immer
    # genau ein Eintrag ausgewaehlt ist.
    selected_code = AUTO if raw == AUTO else resolve_language(
        raw, supported=I18n.SUPPORTED_LANGUAGES,
        default=I18n.DEFAULT_LANGUAGE)

    items: list[dict[str, Any]] = [{
        "code": AUTO,
        "label": AUTO_LANGUAGE_LABEL,
        "selected": selected_code == AUTO,
    }]
    for code, name in I18n.available_languages():
        items.append({
            "code": code,
            "label": name,
            "selected": selected_code == code,
        })
    return items


def group_by_module(items: Iterable[dict]) -> dict[str, list[dict]]:
    """Gruppiert beliebige Eintraege nach `module_id` fuer Sektion-Listen."""
    groups: dict[str, list[dict]] = {}
    for item in items:
        mod = item.get("module_id") or item.get("module") or "sonstiges"
        groups.setdefault(mod, []).append(item)
    return groups
