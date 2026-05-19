"""
Die drei Schnittstellen des Alltagshelfers.

  1. Front-End <-> Modul     ->  ModuleRegistry.dispatch(name, args)
  2. Modul <-> Modul          ->  ModuleContext.call(...)
  3. Dashboard                ->  ModuleRegistry.collect_events(...)

Module kennen weder den Assistenten noch andere Module direkt - sie
melden ihre Faehigkeiten (Capabilities) bei der Registry an und reden
mit anderen Modulen ueber den ModuleContext. So bleibt das System
lose gekoppelt und beliebig erweiterbar.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Optional

from models import Event


# =====================================================================
#  Capability - eine vom Modul angebotene Faehigkeit
# =====================================================================
@dataclass
class Capability:
    """
    Eine benannte Funktion mit beschriebenem Eingabeschema.

    'parameters' folgt einem leichten JSON-Schema-Stil: jeder Eintrag ist
    ein Dict mit 'type' (string|integer|number|boolean|array|object),
    optional 'description' und optional dem Marker '_required'.
    """
    name: str
    description: str
    parameters: dict
    handler: Callable[..., dict]
    module_id: str = ""                 # wird bei der Registrierung gesetzt

    def required_params(self) -> list[str]:
        """Liste der Pflichtparameter (markiert mit '_required': True)."""
        return [n for n, spec in self.parameters.items()
                if isinstance(spec, dict) and spec.get("_required")]

    def to_tool_schema(self) -> dict:
        """Ergibt das Tool-Use-Schema fuer die Anthropic-API."""
        properties: dict = {}
        for n, spec in self.parameters.items():
            if not isinstance(spec, dict):
                continue
            entry = {k: v for k, v in spec.items() if not k.startswith("_")}
            entry.setdefault("type", "string")
            properties[n] = entry
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": self.required_params(),
            },
        }


# =====================================================================
#  ModuleInterface - Basisklasse fuer ein Fachmodul
# =====================================================================
class ModuleInterface:
    """
    Vertrag, den jedes Fachmodul erfuellen muss.

    Pflichtangaben:
      - module_id      (kurzer Bezeichner, z.B. 'contracts')
      - display_name   (lesbarer Name)
      - get_context_summary()  -> kurzer Zustandstext fuer die Sidebar
      - get_capabilities()     -> Liste der angebotenen Capabilities

    Optional:
      - on_register(context)   -> bekommt den ModuleContext fuer Modul-zu-
                                  Modul-Aufrufe; Standard: ignoriert.
      - get_events(horizon_days) -> Dashboard-Ereignisse; Standard: keine.
    """

    @property
    def module_id(self) -> str:
        raise NotImplementedError

    @property
    def display_name(self) -> str:
        raise NotImplementedError

    def get_context_summary(self) -> str:
        return ""

    def get_capabilities(self) -> list[Capability]:
        return []

    def on_register(self, context: "ModuleContext") -> None:
        """Default: nichts tun. Module mit Querverweisen ueberschreiben das."""
        return None

    def get_events(self, horizon_days: int = 90) -> list[Event]:
        """Default: keine Ereignisse. Module mit Fristen ueberschreiben das."""
        return []


# =====================================================================
#  ModuleContext - die Bruecke fuer Modul-zu-Modul-Aufrufe
# =====================================================================
class ModuleContext:
    """
    Wird einem Modul bei der Registrierung uebergeben.

    Erlaubt einem Modul, Capabilities ANDERER Module aufzurufen, ohne sie
    direkt zu kennen (lose Kopplung). Es ist ein duenner Adapter, der die
    Aufrufe an die Registry weiterleitet.
    """

    def __init__(self, registry: "ModuleRegistry", caller_id: str):
        self._registry = registry
        self._caller_id = caller_id

    def call(self, capability_name: str, **kwargs) -> dict:
        """Fuehrt eine Capability eines beliebigen Moduls aus."""
        return self._registry.dispatch(capability_name, kwargs)

    def has_capability(self, capability_name: str) -> bool:
        """Prueft, ob die Capability angeboten wird (lose Kopplung)."""
        return self._registry.has_capability(capability_name)


# =====================================================================
#  ModuleRegistry - das zentrale Verzeichnis aller Module
# =====================================================================
class ModuleRegistry:
    """
    Steckbrett fuer alle Module. Der Assistent und die GUI sprechen
    ausschliesslich ueber die Registry mit dem Rest des Systems.
    """

    def __init__(self) -> None:
        self._modules: dict[str, ModuleInterface] = {}
        self._capabilities: dict[str, Capability] = {}

    # ---- Registrierung ------------------------------------------------
    def register(self, module: ModuleInterface) -> None:
        """Nimmt ein Modul auf und sammelt seine Capabilities ein."""
        mid = module.module_id
        if not mid:
            raise ValueError("Modul hat keine module_id")
        if mid in self._modules:
            raise ValueError(f"Modul '{mid}' bereits registriert")
        self._modules[mid] = module
        for cap in module.get_capabilities():
            cap.module_id = mid
            self._capabilities[cap.name] = cap
        # Modul ueber seinen Context informieren (Modul-zu-Modul-Bruecke)
        module.on_register(ModuleContext(self, mid))

    # ---- Schnittstelle 1: dispatch -----------------------------------
    def dispatch(self, capability_name: str,
                 args: Optional[dict] = None) -> dict:
        """
        Fuehrt eine Capability aus. Der einzige Weg, wie Front-Ends
        und andere Module Modulfunktionen aufrufen.
        """
        if capability_name not in self._capabilities:
            return {"error": f"Capability '{capability_name}' nicht gefunden"}
        cap = self._capabilities[capability_name]
        kwargs = dict(args or {})
        # fehlende Pflichtparameter freundlich abfangen
        missing = [p for p in cap.required_params() if p not in kwargs]
        if missing:
            return {"error": f"Fehlende Pflichtparameter: {', '.join(missing)}"}
        try:
            result = cap.handler(**kwargs)
        except TypeError as exc:
            return {"error": f"Ungueltige Parameter fuer '{capability_name}': {exc}"}
        except Exception as exc:                       # noqa: BLE001
            return {"error": f"Fehler in '{capability_name}': {exc}"}
        return result if isinstance(result, dict) else {"result": result}

    def has_capability(self, capability_name: str) -> bool:
        return capability_name in self._capabilities

    # ---- Auflistung / Schemata ---------------------------------------
    def all_capabilities(self) -> list[Capability]:
        return list(self._capabilities.values())

    def modules(self) -> list[ModuleInterface]:
        return list(self._modules.values())

    def tool_schemas(self) -> list[dict]:
        """Tool-Use-Schemata aller Capabilities (fuer das LLM)."""
        return [c.to_tool_schema() for c in self._capabilities.values()]

    # ---- Sidebar / Kontext-Ueberblick --------------------------------
    def context_overview(self) -> str:
        """Kurzfassung des Modulstatus - genau das, was die GUI-Sidebar zeigt."""
        if not self._modules:
            return "Keine Module registriert."
        lines: list[str] = []
        for module in self._modules.values():
            summary = module.get_context_summary() or "(keine Daten)"
            lines.append(f"[{module.display_name}]")
            lines.append(f"  {summary}")
            lines.append("")
        return "\n".join(lines).rstrip()

    # ---- Schnittstelle 3: Dashboard ----------------------------------
    def collect_events(self, horizon_days: int = 90) -> list[Event]:
        """
        Fragt jedes Modul nach Ereignissen und gibt sie chronologisch
        sortiert zurueck. Module ohne 'get_events' liefern einfach nichts.
        """
        events: list[Event] = []
        for module in self._modules.values():
            try:
                events.extend(module.get_events(horizon_days))
            except Exception:                          # noqa: BLE001
                continue                               # ein Modul darf andere nicht abschiessen
        events.sort(key=lambda e: e.due_date)
        return events
