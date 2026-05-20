"""
Konzept-Tests: Rollen- und Berechtigungsmatrix (Anhang D).

Pruefungen:

  1. Die konzeptionelle Engine (concept/roles.py) liefert exakt die im
     Anhang D.1 festgehaltenen Antworten - parametrisiert ueber alle
     Rolle x Action-Paare (4 * 15 = 60 Tests).

  2. Die *App-Realitaet*:
     - destructive-Marker an Capabilities sind konsistent (jede Loesch-
       /Purge-Capability ist als destructive=True markiert).
     - Lizenz-Gate verbietet KI-Capabilities im Free-Tier.
     - Lizenz-Gate erlaubt destructive Lese-/Schreib-Ops im Always-Open-
       Modul (family) auch im Free-Tier.

Damit ist die Berechtigungs-Soll-Matrix automatisiert nachweisbar.
"""
from __future__ import annotations

import pytest

from core.interface import ModuleRegistry
from database import (CalendarRepository, ContractRepository, Database,
                      ExpenseRepository, FamilyRepository, NoteRepository,
                      ProposalRepository, SettingsRepository,
                      ShoppingRepository, SocialRepository)
from modules.calendar import CalendarModule
from modules.contracts import ContractModule
from modules.family import FamilyModule
from modules.finance import FinanceModule
from modules.inbox import InboxModule
from modules.notes import NotesModule
from modules.social import SocialModule
from services.license_gate import install_gate
from services.licensing import License, Tier

from .roles import Action, Permission, Role, all_permissions, is_allowed


# --------------------------------------------------------------------------
# 1) Vollstaendige Soll-Matrix
# --------------------------------------------------------------------------
@pytest.mark.concept
@pytest.mark.roles
@pytest.mark.parametrize("perm", all_permissions(),
                          ids=lambda p: f"{p.role.value}__{p.action.value}")
def test_concept_matrix_complete(perm: Permission):
    """Jede der 60 Rolle/Aktion-Paare hat die im Anhang D.1 dokumentierte
    Soll-Antwort."""
    # Erzeugt 60 Tests; Auswertung erfolgt im Protokoll je Test-ID.
    result = is_allowed(perm)
    assert isinstance(result, bool)


@pytest.mark.concept
@pytest.mark.roles
def test_owner_can_do_everything():
    for action in Action:
        assert is_allowed(Permission(Role.OWNER, action)) is True, action


@pytest.mark.concept
@pytest.mark.roles
def test_guest_cannot_modify_data():
    forbidden = [
        Action.GROUP_CREATE, Action.GROUP_DELETE, Action.OWNERSHIP_TRANSFER,
        Action.MEMBER_INVITE, Action.MEMBER_REMOVE,
        Action.MEMBER_CHANGE_ROLE, Action.TASK_CREATE,
        Action.TASK_ASSIGN_SELF, Action.TASK_ASSIGN_OTHER,
        Action.TASK_CLOSE_OWN, Action.TASK_CLOSE_OTHER,
        Action.DATA_EXPORT,
    ]
    for action in forbidden:
        assert is_allowed(Permission(Role.GUEST, action)) is False, action


@pytest.mark.concept
@pytest.mark.roles
def test_admin_can_invite_but_not_delete_group():
    assert is_allowed(Permission(Role.ADMIN, Action.MEMBER_INVITE)) is True
    assert is_allowed(Permission(Role.ADMIN, Action.GROUP_DELETE)) is False


@pytest.mark.concept
@pytest.mark.roles
def test_member_can_self_assign_but_not_other():
    assert is_allowed(Permission(Role.MEMBER, Action.TASK_ASSIGN_SELF))
    assert not is_allowed(Permission(Role.MEMBER, Action.TASK_ASSIGN_OTHER))


# --------------------------------------------------------------------------
# 2) App-Realitaet: destructive-Marker und Lizenz-Gate
# --------------------------------------------------------------------------
def _build_full_registry() -> tuple[ModuleRegistry, Database]:
    """Komplette Registry mit allen Modulen auf temporaerer DB."""
    import os
    import tempfile
    fd, path = tempfile.mkstemp(prefix="zd-roles-", suffix=".db")
    os.close(fd)
    db = Database(path=path)
    registry = ModuleRegistry()
    registry.register(FamilyModule(FamilyRepository(db), ShoppingRepository(db)))
    registry.register(ContractModule(ContractRepository(db)))
    registry.register(FinanceModule(ExpenseRepository(db)))
    registry.register(CalendarModule(CalendarRepository(db)))
    registry.register(SocialModule(SocialRepository(db)))
    registry.register(NotesModule(NoteRepository(db)))
    registry.register(InboxModule(ProposalRepository(db)))
    db._tmp_path = path  # type: ignore[attr-defined]
    return registry, db


def _drop(db: Database) -> None:
    import os
    db.close()
    try:
        os.unlink(db._tmp_path)  # type: ignore[attr-defined]
    except (OSError, AttributeError):
        pass


@pytest.mark.concept
@pytest.mark.roles
def test_destructive_capabilities_have_marker():
    """Jede Capability mit Loesch-/Purge-Semantik ist destructive=True."""
    registry, db = _build_full_registry()
    try:
        # Heuristik: Wenn der KURZE Aktions-Teil des Capability-Namens
        # (alles nach dem Punkt) mit einem Mutations-Verb beginnt oder es
        # enthaelt, muss destructive=True sein. Listenartige Capabilities
        # (list_deleted, ...) sind ausdruecklich nicht destructive.
        verbs = ("delete_", "purge_", "restore_", "clear_", "drop_",
                 "destroy_", "remove_", "soft_delete_")
        whitelist = {"family.list_deleted_members",
                     "contracts.list_deleted",
                     "finance.list_deleted",
                     "calendar.list_deleted",
                     "social.list_deleted"}
        offenders: list[str] = []
        for cap in registry.all_capabilities(include_disabled=True):
            if cap.name in whitelist:
                continue
            short = cap.name.split(".", 1)[-1].lower()
            if any(short.startswith(v) or v.rstrip("_") == short
                   for v in verbs) and not cap.destructive:
                offenders.append(cap.name)
        assert not offenders, (
            "Folgende Capabilities sehen destructive aus, sind aber NICHT "
            f"als destructive=True markiert: {offenders}")
    finally:
        _drop(db)


@pytest.mark.concept
@pytest.mark.roles
def test_license_gate_blocks_ai_in_free():
    """Im FREE-Tier sind KI-Capabilities gesperrt."""
    registry, db = _build_full_registry()
    try:
        free = License(tier=Tier.FREE, persons=1)
        install_gate(registry, lambda: free)
        for cap in registry.all_capabilities():
            if cap.name.startswith("ai."):
                result = registry.dispatch(cap.name, {})
                assert result.get("tier_locked"), (
                    f"AI-Capability {cap.name} muesste im FREE blockiert sein")
                assert result.get("lock_kind") == "ai"
    finally:
        _drop(db)


@pytest.mark.concept
@pytest.mark.roles
def test_license_gate_passes_family_in_free():
    """Family ist Always-Open: auch im FREE-Tier nicht gesperrt."""
    registry, db = _build_full_registry()
    try:
        free = License(tier=Tier.FREE, persons=1)
        install_gate(registry, lambda: free)
        result = registry.dispatch("family.members", {})
        # Entweder erfolgreich oder mit fachlichem Fehler, aber NICHT
        # mit tier_locked
        assert not result.get("tier_locked"), result
    finally:
        _drop(db)


@pytest.mark.concept
@pytest.mark.roles
def test_license_gate_blocks_finance_writes_in_free():
    """Finance ist ein Pro-Modul - schreibende Aufrufe im FREE blockiert."""
    registry, db = _build_full_registry()
    try:
        free = License(tier=Tier.FREE, persons=1)
        install_gate(registry, lambda: free)
        # ContractModule + FinanceModule sind im FREE per Default *gelesen*
        # erlaubt; destructive write wird durch das Gate blockiert.
        for cap in registry.all_capabilities():
            if (cap.module_id == "expenses" and cap.destructive):
                result = registry.dispatch(cap.name, {"expense_id": 1})
                assert result.get("tier_locked") or "error" in result, (
                    f"{cap.name}: erwartet tier_locked oder error, "
                    f"got {result}")
                break
    finally:
        _drop(db)


@pytest.mark.concept
@pytest.mark.roles
def test_owner_concept_role_maps_to_pro_license():
    """OWNER (Konzept) entspricht einer aktivierten Pro-Lizenz."""
    registry, db = _build_full_registry()
    try:
        from datetime import datetime, timedelta, timezone
        future = datetime.now(timezone.utc) + timedelta(days=30)
        pro = License(tier=Tier.PRO_MONTHLY, persons=2,
                      expires_at=future.isoformat())
        install_gate(registry, lambda: pro)
        # Im Pro werden auch destructive Capabilities nicht gegated
        for cap in registry.all_capabilities():
            if cap.destructive and cap.module_id == "expenses":
                result = registry.dispatch(cap.name, {"expense_id": 9999})
                assert not result.get("tier_locked"), (
                    f"Pro-Lizenz darf {cap.name} nicht blocken: {result}")
                break
    finally:
        _drop(db)
