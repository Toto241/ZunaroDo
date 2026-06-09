# Geräte-Smoke-Checkliste (vor Play-Store-Upload)

Auf **mindestens einem echten Android-Gerät** (API 24 und API 33+) durchführen.

## Installation

- [ ] Debug- oder Release-AAB/APK installieren (`adb install`)
- [ ] App startet ohne Crash (Cold Start)

## Navigation

- [ ] Bottom-Nav: alle 5 Tabs öffnen (Dashboard, Verträge, Finanzen, Kalender, Mehr)
- [ ] Zurück-Navigation aus Untermenüs funktioniert

## CRUD

- [ ] Vertrag anlegen → in Liste sichtbar
- [ ] Ausgabe anlegen → in Liste sichtbar
- [ ] Termin anlegen → in Liste sichtbar
- [ ] Eintrag löschen → verschwindet aus Liste

## Recht & Datenschutz

- [ ] Erststart: Datenschutz-Dialog erscheint, Akzeptieren wird persistiert
- [ ] Mehr → Datenschutz / Impressum / AGB / Widerruf öffnen sich
- [ ] Mehr → Alle Daten löschen (separates Testgerät!)

## Benachrichtigungen (API 33+)

- [ ] Erinnerung auslösen → System-Permission-Dialog erscheint
- [ ] Nach Erteilung: Benachrichtigung sichtbar

## Play Billing (optional für v1.0)

- [ ] Mehr → Lizenz → „Pro über Play Store“ sichtbar (wenn Billing verfügbar)
- [ ] Kauf mit License-Tester-Konto → `purchaseToken` erhalten
- [ ] Server `/verify/play` verifiziert Token → Pro-Tier aktiv

## Native Bridges

- [ ] OCR (falls genutzt): ML Kit liefert Text
- [ ] DB-Key: Keystore-Zugriff ohne Crash

## Stabilität

- [ ] App-Killer-Test: App schließen, neu öffnen → Daten noch da
- [ ] Rotation Portrait ↔ Landscape: kein Crash

## Ergebnis

Datum: ___________  
Gerät / API: ___________  
Tester: ___________  
Status: [ ] GO  [ ] NO-GO  
Notizen: ___________
