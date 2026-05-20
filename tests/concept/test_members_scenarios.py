"""
Konzept-Tests: Mitglieder-Szenarien M-01 .. M-09  (TESTING.md Kapitel 2).

Stellt sicher, dass die Datenschicht und die family-Capabilities mit
allen im Konzept geforderten Gruppengroessen, Rollenverteilungen und
Statusvarianten klar kommen:

  M-01  Einzelperson
  M-02  Paar
  M-03  Familie 3..5
  M-04  Team 6..11
  M-05  exakt 12 (Play-Mindestzahl)
  M-06  20+ (Skalierungs-/Lasttest)
  M-07  Status-Mischung (active/invited/inactive/removed)
  M-08  nur INVITED (Pending-State)
  M-09  REMOVED-Reactivation

Jeder Testfall ist als eigene Test-ID erkennbar, damit das Protokoll
einen 1:1-Nachweis liefert.
"""
from __future__ import annotations

import pytest

from .fixtures import (PROFILES, STATUS_ACTIVE, STATUS_INACTIVE,
                       STATUS_INVITED, STATUS_REMOVED, fresh_repos,
                       make_household, seed_household)


@pytest.fixture
def repos():
    bundle = fresh_repos()
    try:
        yield bundle
    finally:
        bundle.close()


@pytest.mark.concept
@pytest.mark.members
@pytest.mark.parametrize("profile_id", list(PROFILES.keys()))
def test_M_can_seed_profile(repos, profile_id):
    """Jedes Mitglieder-Profil laesst sich vollstaendig in eine
    frische DB einspielen und gibt konsistente Listen zurueck."""
    fixture = make_household(profile_id)
    seed_household(repos, fixture)

    persisted_active = repos.family.list_members(include_deleted=False)
    persisted_deleted = repos.family.list_deleted_members()

    expected_active_or_invited = [
        m for m in fixture.members
        if m.status != STATUS_REMOVED
    ]
    expected_removed = [m for m in fixture.members
                        if m.status == STATUS_REMOVED]

    assert len(persisted_active) == len(expected_active_or_invited), (
        f"{profile_id}: erwartet {len(expected_active_or_invited)} aktive "
        f"Mitglieder, gefunden {len(persisted_active)}")
    assert len(persisted_deleted) == len(expected_removed), (
        f"{profile_id}: erwartet {len(expected_removed)} entfernte, "
        f"gefunden {len(persisted_deleted)}")


@pytest.mark.concept
@pytest.mark.members
def test_M01_single_owner_no_rotation(repos):
    fx = make_household("M-01")
    seed_household(repos, fx)
    members = repos.family.list_members()
    assert len(members) == 1
    tasks = repos.family.list_tasks()
    assert tasks, "Solo-Profil hat trotzdem Aufgaben (kein Rotationsproblem)"
    # Rotation darf nur den Owner enthalten
    for t in tasks:
        assert len(t.rotation) == 1


@pytest.mark.concept
@pytest.mark.members
def test_M02_minimal_team_two_members(repos):
    fx = make_household("M-02")
    seed_household(repos, fx)
    members = repos.family.list_members()
    assert len(members) == 2
    tasks = repos.family.list_tasks()
    # Eine Rotation mit 2 Mitgliedern muss vorkommen
    assert any(len(t.rotation) == 2 for t in tasks)


@pytest.mark.concept
@pytest.mark.members
def test_M05_meets_play_minimum_12(repos):
    fx = make_household("M-05")
    seed_household(repos, fx)
    assert len(repos.family.list_members()) >= 12, (
        "Closed-Test-Profil muss >=12 Mitglieder haben (Play-Anforderung)")


@pytest.mark.concept
@pytest.mark.members
def test_M06_scales_to_twenty_plus(repos):
    fx = make_household("M-06")
    seed_household(repos, fx)
    members = repos.family.list_members()
    assert len(members) >= 20

    # Auftraege - jeder erzeugte Auftrag ist auch persistiert
    orders = repos.family.list_orders(only_open=False)
    assert orders, "Profil M-06 muss Auftraege erzeugen"


@pytest.mark.concept
@pytest.mark.members
def test_M07_mixed_status_distribution(repos):
    fx = make_household("M-07")
    seed_household(repos, fx)
    active = repos.family.list_members(include_deleted=False)
    deleted = repos.family.list_deleted_members()
    assert deleted, "M-07 muss entfernte Mitglieder enthalten"
    assert active, "M-07 muss aktive/invited Mitglieder enthalten"


@pytest.mark.concept
@pytest.mark.members
def test_M08_invited_only_owner_active(repos):
    fx = make_household("M-08")
    seed_household(repos, fx)
    # Im Profil ist genau ein Mitglied ACTIVE (Owner), Rest INVITED
    active_in_fixture = sum(1 for m in fx.members
                             if m.status == STATUS_ACTIVE)
    invited_in_fixture = sum(1 for m in fx.members
                              if m.status == STATUS_INVITED)
    assert active_in_fixture == 1
    assert invited_in_fixture == len(fx.members) - 1

    # In der DB ist alles vorhanden (INVITED ist Konzept, nicht persistiert)
    persisted = repos.family.list_members(include_deleted=False)
    assert len(persisted) == len(fx.members)


@pytest.mark.concept
@pytest.mark.members
def test_M09_reactivation_restores_member(repos):
    """REMOVED-Mitglied wird wieder eingeladen -> restore_member."""
    fx = make_household("M-09")
    name_map = seed_household(repos, fx)

    removed = [m for m in fx.members if m.status == STATUS_REMOVED]
    assert removed, "M-09 muss mindestens ein removed-Mitglied enthalten"
    target = name_map[removed[0].name]
    assert target.id is not None

    # Vor Reaktivierung: nicht in aktiver Liste, aber in deleted-Liste
    active_names_before = {m.name for m in repos.family.list_members()}
    assert target.name not in active_names_before
    deleted_names_before = {m.name
                            for m in repos.family.list_deleted_members()}
    assert target.name in deleted_names_before

    assert repos.family.restore_member(target.id) is True

    # Danach: wieder in aktiver Liste
    active_names_after = {m.name for m in repos.family.list_members()}
    assert target.name in active_names_after
    assert target.name not in {
        m.name for m in repos.family.list_deleted_members()}


@pytest.mark.concept
@pytest.mark.members
def test_remove_and_readd_preserves_distinct_id(repos):
    """Entfernen + erneutes Hinzufuegen erzeugt eine neue ID."""
    fx = make_household("M-03")
    name_map = seed_household(repos, fx)
    first = next(iter(name_map.values()))
    assert first.id is not None
    repos.family.delete_member(first.id)  # endgueltig

    # Wieder hinzufuegen
    from models import FamilyMember
    re_added = repos.family.add_member(
        FamilyMember(name=first.name, role=first.role))
    assert re_added.id != first.id
    assert re_added.name == first.name


@pytest.mark.concept
@pytest.mark.members
def test_get_events_handles_all_sizes(repos):
    """get_events() liefert fuer alle Profilgroessen widerspruchsfreie Daten."""
    from modules.family import FamilyModule
    for profile_id in PROFILES:
        bundle = fresh_repos()
        try:
            fx = make_household(profile_id)
            seed_household(bundle, fx)
            mod = FamilyModule(bundle.family, bundle.shopping)
            events = mod.get_events(horizon_days=60)
            for ev in events:
                assert ev.title
                assert ev.module_id == "family"
        finally:
            bundle.close()
