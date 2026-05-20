"""
Licensing-Durchsetzung: zentrale Stelle, die Capability-Aufrufe gegen
die aktive Lizenz prueft.

Das Modul liefert eine Pre-Dispatch-Hook-Funktion, die in
ModuleRegistry.set_pre_dispatch_hook(...) gehaengt wird. Der Hook
bekommt (capability_name, args) und liefert entweder None (durchlassen)
oder ein Error-Dict mit Schluessel 'tier_locked' (Aufruf wird abgewiesen,
GUI/CLI zeigt einen Upgrade-Hinweis).

Mapping: welche Module sind im FREE-Tier nutzbar? Welche brauchen Pro?
Wird hier zentral festgehalten, damit es nicht ueber 12 Capabilities
verstreut ist.

Special-Cases:
  - 'destructive=True' Capabilities werden im Grandfathered-Modus
    nur dann durchgelassen, wenn das Modul im 'enabled_modules'-Set
    der Lizenz steht (also urspruenglich freigeschaltet war).
  - 'system.*' Capabilities (Suche etc.) sind immer offen - sonst
    wird Free-Tier-UX kaputt.
  - 'inbox.proposals' (reines Listen) ist offen - der LLM-Aufruf
    'inbox.analyze_mail' braucht Pro, weil er KI-Tokens kostet.
"""
from __future__ import annotations

from typing import Callable, Optional

from core.interface import ModuleRegistry
from services.licensing import License


# Module, die im FREE-Tier ohne Einschraenkung verfuegbar sind.
# Alles andere ist Pro/Trial. Module sind hier als Modul-IDs gelistet.
ALWAYS_OPEN_MODULES: frozenset[str] = frozenset({
    "search",          # Volltextsuche muss immer gehen
    "daystructure",   # Tagebuch - reines persoenliches Notiz-Feature
    "statistics",     # Auswertung der eigenen Daten - kein Mehrwert ohne
    "notes",           # Notizen sind App-uebergreifend
})

# Capability-Praefixe der ALWAYS_OPEN-Module - noetig, weil der Praefix
# nicht immer mit der Modul-ID uebereinstimmt (z.B. 'system.search' -> 'search',
# 'stats.*' -> 'statistics').
ALWAYS_OPEN_PREFIXES: tuple[str, ...] = (
    "system.",
    "stats.",
    "daystructure.",
    "notes.",
)

# Capabilities, die KI-Tokens verbrauchen und entsprechend Pro brauchen.
AI_CAPABILITY_PREFIXES: tuple[str, ...] = (
    "inbox.analyze_mail",
    "inbox.suggest_actions",
    "social.draft_message",
)


def _is_ai_capability(name: str) -> bool:
    return any(name.startswith(p) for p in AI_CAPABILITY_PREFIXES)


def make_gate(license_provider: Callable[[], License]
              ) -> Callable[[str, dict], Optional[dict]]:
    """
    Baut einen Pre-Dispatch-Hook.

    'license_provider' ist eine 0-arg Funktion, die die aktuelle
    Lizenz liefert - so kann die Lizenz zur Laufzeit ohne Restart
    geaendert werden (z.B. nach Pro-Aktivierung im Settings-Tab).

    Rueckgabe: Funktion(capability_name, args) -> Optional[Error-Dict].
    """
    def gate(capability_name: str, args: dict,
             *, capability=None) -> Optional[dict]:
        lic = license_provider()

        # 1) Pro-Tier: alles offen (effektiver Tier inkl. Trial/Grace)
        if lic.is_pro():
            return None

        # 2) Free-Tier: KI-Aufrufe immer blocken
        if _is_ai_capability(capability_name):
            return _locked("ai", capability_name,
                           "KI-Funktionen sind im Pro-Tier verfuegbar.")

        # 3) Capability-Praefix-Check (fuer ALWAYS_OPEN-Module, deren
        # Capability-Namen nicht mit der Modul-ID beginnen)
        if any(capability_name.startswith(p) for p in ALWAYS_OPEN_PREFIXES):
            return None

        # 4) Modul-Check: bevorzugt das Capability-Objekt
        module_id = (capability.module_id if capability is not None
                     else _module_id_from_name(capability_name))
        if module_id in ALWAYS_OPEN_MODULES:
            return None

        destructive = bool(getattr(capability, "destructive", False))
        if not lic.allows_module(module_id, writing=destructive):
            return _locked("module", capability_name,
                           f"Modul '{module_id}' ist im Pro-Tier verfuegbar.")
        return None

    return gate


def _module_id_from_name(capability_name: str) -> str:
    """Fallback wenn das Capability-Objekt nicht durchgereicht wurde."""
    return capability_name.split(".", 1)[0] if "." in capability_name else ""


def _locked(kind: str, capability: str, message: str) -> dict:
    return {
        "error": message,
        "tier_locked": True,
        "lock_kind": kind,
        "capability": capability,
    }


def install_gate(registry: ModuleRegistry,
                  license_provider: Callable[[], License]) -> None:
    """
    Haengt den Lizenz-Hook in eine ModuleRegistry ein.

    Verlangt von der Registry, dass sie eine 'set_pre_dispatch_hook'-
    Methode anbietet (siehe core/interface.py).
    """
    if not hasattr(registry, "set_pre_dispatch_hook"):
        raise RuntimeError(
            "ModuleRegistry kennt set_pre_dispatch_hook nicht - "
            "core/interface.py auf den passenden Stand bringen.")
    registry.set_pre_dispatch_hook(make_gate(license_provider))
