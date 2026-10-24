---
name: anki
description: Anki einrichten, synchronisieren und Sync-Probleme lösen (Anki-Desktop, AnkiConnect, AnkiWeb, AnkiDroid/AnkiMobile am Handy). Nutzen, sobald der Nutzer Anki ausdrücklich erwähnt – "Anki", "Karten aufs Handy", "AnkiDroid", "synchronisieren", "Sync-Fehler", "was hab ich in Anki vergessen", "Anki-Statistik", "ich hab einen Stapel/Deck importiert", "Deck von Kommilitonen/StudyDrive", "überarbeite meinen Anki-Stapel". Karten schreiben selbst → Skill `karten`.
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

## Fremde Stapel (z. B. von Kommilitonen, StudyDrive, AnkiWeb-Shared-Decks)

Auslöser: Der Nutzer sagt, er habe einen Stapel importiert, oder `lern anki sync` meldet „NEUER STAPEL erkannt“.
Erkannt werden neue, nicht leere Hauptstapel außerhalb von `Lernecke::`, die noch keinem Kurs zugeordnet sind (`lern anki fremd liste`).

1. **Erst synchronisieren**, damit der Stapel vollständig auf dem Desktop ist: `lern anki sync`. Wurde er am Handy importiert, vorher das Handy synchronisieren lassen.
2. **Nachfragen** (kurz): Zu welchem Kurs gehört der Stapel (ggf. `--kurs <id>`)? Woher stammt er? Soll er übernommen werden?
   Gehört er nicht zur Lernecke: `lern anki fremd ignorieren "<Name>"`.
3. **Übernehmen**: `lern anki fremd uebernehmen "<Name>" --quelle "StudyDrive …" [--thema <id>]`.
   Das spiegelt alle Notizen nach `kurse/<kurs>/karten-fremd/<slug>.yaml`. Ab dann fließt die Statistik bei jedem Sync in den Lernstand ein.
   Die Notizen bleiben in ihrem Stapel, ihrem Notiztyp und ihrer Lernhistorie.
4. **Angebot an den Nutzer** (er wählt):
   a) **nur Statistik**: fertig.
   b) **Themen zuordnen**: in der YAML pro Notiz `thema:` aus `themen.yaml` setzen. Erst dann zählen oft vergessene Karten in die Mastery des Themas.
      Bei großen Stapeln in Blöcken von ca. 30 Notizen arbeiten und zwischendurch `lern pruefen`.
   c) **Qualitätscheck und Überarbeitung**: Fremde Karten gelten als **inoffiziell**. Gegen Skript und Folien prüfen (`text/`, Seitenangaben) und Folgendes korrigieren:
      - fachliche Fehler und Notation (Kurs-Notation aus `kurs.yaml`),
      - unklare Fragen.
      Auffälliges in `notiz:` vermerken (z. B. „falsch laut Skript S. 42, korrigiert“) und dem Nutzer eine Liste der Änderungen zeigen.
      Überladene Karten nicht in der YAML aufspalten. Stattdessen eigene Karten in `karten/*.md` schreiben (Skill `karten`) und dem Nutzer vorschlagen, die alte Karte in Anki auszusetzen.
5. **Übertragen**: `lern anki sync`. Geänderte Felder gehen an dieselbe Anki-Notiz, die Lernhistorie bleibt, das Handy bekommt die Änderungen über AnkiWeb.

Regeln für `karten-fremd/*.yaml`:
- Nur Werte unter `felder` ändern sowie `thema` und `notiz` setzen. `id`, `modell` und Feldnamen nie ändern, keine Notizen hinzufügen. Neue Karten gehören nach `karten/*.md`.
- Feldwerte sind Anki-HTML: Zeilenumbruch `<br>`, Formeln `\( … \)` bzw. `\[ … \]`. Vorhandene Bilder (`<img …>`) und Formatierung unverändert lassen.
- Die Datei ist ein Spiegel. Der Sync vergleicht sie dreifach (Datei, Anki, letzter gemeinsamer Stand):
  - Nur in Anki geändert: Die Datei wird nachgezogen.
  - Nur in der Datei geändert: Die Änderung geht nach Anki.
  - Beides geändert: **KONFLIKT**. Die Anki-Fassung gewinnt, die Fassung des Agenten steht unter `konflikt_agent`. Mit dem Nutzer klären, `konflikt_agent` danach entfernen.
- In Anki gelöschte Notizen verschwinden beim nächsten Sync aus der Datei.

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
- **Geänderter Kartentext kommt nach manuellem `.apkg`-Import nicht an**: Im Import-Dialog „Notizen aktualisieren“ auf „Immer“ stellen.
  `lern anki sync` gleicht die Texte selbst an, dort ist das nicht nötig.
- **Karte am Handy/Desktop bearbeitet**: Beim nächsten geänderten Import überschreibt das Repo den Text. Verbesserungen deshalb in `karten/*.md` machen (Skill `karten`).

## Regeln für den Agenten

- Felder der Notiztypen „Lernecke Basis“ und „Lernecke Lückentext“ **nie ändern**. Das ist eine Schema-Änderung und erzwingt eine vollständige Synchronisation. Neue Infos gehören ins Feld „Zusatz“.
- Karten-IDs nie ändern oder wiederverwenden. Gelöschte Karten in Anki manuell löschen lassen (der Sync löscht nichts).
- Nach dem Sync die Ausgabe kurz zusammenfassen. Oft vergessene Karten (Brief bzw. `anki-stats.json`) als Anlass nehmen, das Thema neu zu erklären oder die Karte aufzuteilen.
