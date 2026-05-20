"""
Konzept-Tests: automatisierte Umsetzung des Testkonzepts aus TESTING.md.

Aufbau (entspricht den Abschnitten 1-10 / A-K des Konzepts):

  fixtures.py             - synthetische Nutzer/Gruppen M-01..M-09 (Seed)
  pairwise.py             - All-Pairs-Algorithmus fuer Anhang C
  matrix.py               - Dimensionen + Constraints fuer die Matrix
  roles.py                - Berechtigungsmatrix (Anhang D)
  test_members_scenarios  - Mitglieder-Szenarien (Kapitel 2)
  test_roles_permissions  - Rollen-/Berechtigungstests (Anhang D)
  test_tasks_matrix       - kombinatorische Tests (Kapitel 3 + Anhang C/E)
  test_properties_concept - Property-Tests (Kapitel 8)
  test_release_gate       - Release-Gate (Kapitel 4.5 + Anhang J)
"""
