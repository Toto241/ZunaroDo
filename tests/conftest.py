"""
Pytest-Konfiguration auf Test-Wurzelebene.

Definiert Marker, damit die Konzept-Tests vom Protokoll-Generator
gezielt selektierbar sind.
"""
from __future__ import annotations


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "concept: Tests aus dem Konzept (tests/concept/)")
    config.addinivalue_line(
        "markers", "members: Mitglieder-Szenarien M-01..M-09")
    config.addinivalue_line(
        "markers", "roles: Rollen-/Berechtigungs-Matrix (Anhang D)")
    config.addinivalue_line(
        "markers", "combinatorics: Pairwise-Matrix (Anhang C)")
    config.addinivalue_line(
        "markers", "property: Property-/Fuzz-Tests (Kapitel 8)")
    config.addinivalue_line(
        "markers", "release_gate: Release-Gate (Kapitel 4.5 / Anhang J)")
    config.addinivalue_line(
        "markers", "negative: Negativtests (Teil II Abschnitt 11)")
    config.addinivalue_line(
        "markers", "privacy: Datenschutz-/Compliance-Tests (Teil II 12-13)")
    config.addinivalue_line(
        "markers", "security: Security-Negativtests (Teil II 11.3 D)")
    config.addinivalue_line(
        "markers", "playstore: Play-Store-Sync-Tests")
    config.addinivalue_line(
        "markers", "slow: Tests > 1s")
