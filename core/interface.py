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

    'destructive' kennzeichnet Faehigkeiten, die Daten dauerhaft veraendern
    oder Aktionen mit Aussenwirkung anstossen. Der Assistent fragt vor
    solchen Aufrufen ueber den ConfirmCallback nach.
    """
    name: str
    description: str
    parameters: dict
    handler: Callable[..., dict]
    module_id: str = ""
    destructive: bool = False

    def required_params(self) -> list[str]:
        return [n for n, spec in self.parameters.items()
                if isinstance(spec, dict) and spec.get("_required")]

    def _properties(self) -> dict:
        properties: dict = {}
        for n, spec in self.parameters.items():
            if not isinstance(spec, dict):
                continue
            entry = {k: v for k, v in spec.items() if not k.startswith("_")}
            entry.setdefault("type", "string")
            properties[n] = entry
        return properties

    def to_tool_schema(self) -> dict:
        """OpenAPI-Stil-Schema (von Gemini direkt nutzbar)."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": self._properties(),
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
        # Modul-IDs, die fuer Aufrufe deaktiviert sind. Datenschicht bleibt
        # bestehen, nur dispatch() und Dashboard liefern fuer diese Module
        # nichts mehr aus.
        self._disabled: set[str] = set()

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

    def set_module_enabled(self, module_id: str, enabled: bool) -> None:
        """Aktiviert oder deaktiviert ein Modul zur Laufzeit."""
        if module_id not in self._modules:
            raise ValueError(f"Modul '{module_id}' unbekannt")
        if enabled:
            self._disabled.discard(module_id)
        else:
            self._disabled.add(module_id)

    def is_module_enabled(self, module_id: str) -> bool:
        return module_id in self._modules and module_id not in self._disabled

    def module_states(self) -> list[dict]:
        """Zustand aller Module fuer die GUI-Modulverwaltung."""
        return [{"module_id": mid,
                  "display_name": m.display_name,
                  "enabled": mid not in self._disabled,
                  "capabilities":
                      [c.name for c in self._capabilities.values()
                       if c.module_id == mid]}
                for mid, m in self._modules.items()]

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
        if cap.module_id in self._disabled:
            return {"error": f"Modul '{cap.module_id}' ist deaktiviert",
                    "module_disabled": True}
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
        """True nur, wenn die Capability existiert UND ihr Modul aktiv ist."""
        cap = self._capabilities.get(capability_name)
        if cap is None:
            return False
        return cap.module_id not in self._disabled

    def get_capability(self,
                        capability_name: str) -> Optional[Capability]:
        """
        Liefert das Capability-Objekt - oder None, wenn unbekannt oder
        ihr Modul deaktiviert. Wird z.B. von der GUI genutzt, um aus dem
        Parameter-Schema dynamische Formulare zu bauen.
        """
        cap = self._capabilities.get(capability_name)
        if cap is None:
            return None
        if cap.module_id in self._disabled:
            return None
        return cap

    # ---- Auflistung / Schemata ---------------------------------------
    def all_capabilities(self,
                          include_disabled: bool = False) -> list[Capability]:
        if include_disabled:
            return list(self._capabilities.values())
        return [c for c in self._capabilities.values()
                if c.module_id not in self._disabled]

    def modules(self) -> list[ModuleInterface]:
        return list(self._modules.values())

    def tool_schemas(self) -> list[dict]:
        """Tool-Schemata fuer Gemini (nur aktive Module)."""
        return [c.to_tool_schema() for c in self.all_capabilities()]

    def destructive_capability_names(self) -> set[str]:
        return {c.name for c in self.all_capabilities() if c.destructive}

    # ---- Sidebar / Kontext-Ueberblick --------------------------------
    def context_overview(self) -> str:
        if not self._modules:
            return "Keine Module registriert."
        lines: list[str] = []
        for mid, module in self._modules.items():
            tag = " (deaktiviert)" if mid in self._disabled else ""
            summary = (module.get_context_summary() or "(keine Daten)"
                        if mid not in self._disabled else "(deaktiviert)")
            lines.append(f"[{module.display_name}{tag}]")
            lines.append(f"  {summary}")
            lines.append("")
        return "\n".join(lines).rstrip()

    # ---- Schnittstelle 3: Dashboard ----------------------------------
    def collect_events(self, horizon_days: int = 90) -> list[Event]:
        events: list[Event] = []
        for mid, module in self._modules.items():
            if mid in self._disabled:
                continue
            try:
                events.extend(module.get_events(horizon_days))
            except Exception:                          # noqa: BLE001
                continue
        events.sort(key=lambda e: e.due_date)
        return events
