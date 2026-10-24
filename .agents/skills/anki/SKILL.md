---
name: anki
description: Anki einrichten, synchronisieren und Sync-Probleme lösen (Anki-Desktop, AnkiConnect, AnkiWeb, AnkiDroid/AnkiMobile am Handy). Nutzen, sobald der Nutzer Anki ausdrücklich erwähnt – "Anki", "Karten aufs Handy", "AnkiDroid", "synchronisieren", "Sync-Fehler", "was hab ich in Anki vergessen", "Anki-Statistik". Karten schreiben selbst → Skill `karten`.
---

# Anki-Abgleich (Desktop ⇄ AnkiWeb ⇄ Handy)

Datenfluss: Repo → **Anki-Desktop** (per AnkiConnect, `127.0.0.1:8765`) ⇄ **AnkiWeb** ⇄ **Handy**.
Der Agent erreicht nur Anki-Desktop – und nur, solange es geöffnet ist. Ans Handy kommt alles ausschließlich über AnkiWeb.

## Standardbefehl: `lern anki sync`

Feste, konfliktarme Reihenfolge (nicht durch Einzelbefehle ersetzen):
1. AnkiWeb → Desktop: Handy-Wiederholungen holen, **bevor** irgendetwas geändert wird
2. Statistik ziehen → `lernstand/anki-stats.json` (lapses fließen in Mastery und Brief)
3. Nur wenn sich Karten geändert haben: Karten importieren (.apkg-Import, gleiche IDs wie `anki export` → keine Duplikate, Lernhistorie bleibt)
4. Desktop → AnkiWeb hochladen, damit das Handy die neuen Karten bekommt

Schlägt Schritt 1 fehl, bricht der Befehl ab, **bevor** etwas verändert wurde. Dann den Abschnitt „Probleme“ befolgen, nicht mit `push` erzwingen.
- `--still`: Anki geschlossen ist kein Fehler (für Sessionstart/-ende). `--ohne-push`: nur holen.
- `lern anki push` / `pull` sind Einzelschritte ohne AnkiWeb und nur für die Fehlersuche gedacht.
- Ohne Anki-Desktop: `lern anki export` → `.apkg` (Import am PC oder direkt am Handy). Dabei gibt es keine Statistik zurück.

## Vor dem Sync immer an den Nutzer

„Hast du am Handy nach dem letzten Lernen synchronisiert?“ Wenn nicht: erst das Handy synchronisieren lassen, dann `lern anki sync`.
(Nach Einrichtung mit Auto-Sync entfällt das meist. Dann nur kurz erinnern.)

## Einmalige Einrichtung (Schritt für Schritt begleiten)

1. Anki-Desktop installieren von **https://apps.ankiweb.net** (Download → Windows, kostenlos). Starten, Profil öffnen.
2. AnkiConnect installieren: Extras → Erweiterungen → „Erweiterungen herunterladen…“ → Code **2055492159** → OK.
3. **Anki komplett schließen und neu starten.** Ohne Neustart lädt Anki die Erweiterung nicht, und der Port 8765 bleibt zu.
   Häufigster Einrichtungsfehler: Die Erweiterung ist installiert, aber Anki läuft noch als derselbe Prozess.
   Fragt die Windows-Firewall nach Netzwerkzugriff, erlauben. AnkiConnect nimmt nur Verbindungen vom eigenen PC an.
4. Verbindung prüfen (Agent):
   `.venv/Scripts/python -c "from lern.anki import ankiconnect as a; print(a('version'), a('getActiveProfile'), a('deckNames'))"`
   Die Version muss 6 oder höher sein. Bei „nicht erreichbar“ in dieser Reihenfolge prüfen:
   - Läuft Anki?
   - Gibt es `%APPDATA%\Anki2\addons21\2055492159\`?
   - Wurde Anki nach der Installation neu gestartet? (PowerShell: `Get-Process anki | Select StartTime` mit dem Installationszeitpunkt vergleichen.)
   - Ist die Erweiterung unter Extras → Erweiterungen aktiviert?
5. Kostenloses AnkiWeb-Konto auf https://ankiweb.net anlegen. In Anki-Desktop auf „Synchronisieren“ klicken und anmelden.
   In den Einstellungen → Synchronisierung „Beim Öffnen/Schließen des Profils automatisch synchronisieren“ aktivieren.
6. Handy: AnkiDroid (Android, kostenlos) oder AnkiMobile (iOS, kostenpflichtig) installieren, mit demselben AnkiWeb-Konto anmelden, automatische Synchronisierung einschalten.
7. **Erster Abgleich, Reihenfolge wichtig:** Hat das Handy schon eigene Karten oder Fortschritt, zuerst das Handy synchronisieren, dann den Desktop.
   Fragt Anki dabei „Hochladen oder Herunterladen?“, siehe „Probleme“. Danach `lern anki sync`.
8. Prüfen: Im Handy taucht der Stapel `Lernecke::<Kurs>::…` auf.

## Probleme

- **„Anki nicht erreichbar“**: Anki-Desktop ist nicht offen, oder AnkiConnect fehlt bzw. ist deaktiviert. Anki starten und den Befehl wiederholen.
- **WARNUNG kein AnkiWeb-Login**: Einrichtung Schritt 5. Bis dahin findet nur ein lokaler Abgleich statt.
- **„AnkiWeb-Sync fehlgeschlagen“ / Anki fragt „Hochladen auf AnkiWeb oder Herunterladen?“** (vollständige Synchronisation nötig).
  Eine Seite wird dabei komplett überschrieben, deshalb mit dem Nutzer gemeinsam entscheiden:
  - Liegt der wertvollere Lernstand auf dem **Handy** oder auf AnkiWeb (Normalfall: dort wird gelernt) → am Desktop **„Herunterladen“** wählen.
    Danach `lern anki sync`: Die Lernecke-Karten werden dabei automatisch erneut importiert (Notizen kommen aus dem Repo, nichts geht verloren).
  - Wurde nur am Desktop gelernt und das Handy ist leer oder veraltet → **„Hochladen“** wählen, danach am Handy „Herunterladen“.
  - Im Zweifel: vorher in Anki-Desktop über Datei → Exportieren → „Sammlungspaket (.colpkg)“ ein Backup anlegen.
- **Duplikate**: Zu Duplikaten kommt es nur, wenn Karten außerhalb des Repos von Hand kopiert wurden. Lernecke-Karten tragen feste GUIDs. Export und Push sind kompatibel.
- **Karte am Handy/Desktop bearbeitet**: Beim nächsten geänderten Import überschreibt das Repo den Text. Verbesserungen deshalb in `karten/*.md` machen (Skill `karten`).

## Regeln für den Agenten

- Felder der Notiztypen „Lernecke Basis“ und „Lernecke Lückentext“ **nie ändern**. Das ist eine Schema-Änderung und erzwingt eine vollständige Synchronisation. Neue Infos gehören ins Feld „Zusatz“.
- Karten-IDs nie ändern oder wiederverwenden. Gelöschte Karten in Anki manuell löschen lassen (der Sync löscht nichts).
- Nach dem Sync die Ausgabe kurz zusammenfassen. Oft vergessene Karten (Brief bzw. `anki-stats.json`) als Anlass nehmen, das Thema neu zu erklären oder die Karte aufzuteilen.
