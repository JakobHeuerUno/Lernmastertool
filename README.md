# LERNECKE

Persönliche Lernumgebung für Uni-Kurse. Man öffnet sie mit **Claude Code** oder **Codex** (CLI oder Desktop-App) und lernt einfach weiter.
Jede Session weiß automatisch, wo du stehst, welche Fehler offen sind und welche Erklärungen dir geholfen haben.

## Schnellstart

1. Einrichten (einmalig pro Rechner – nach dem Klonen, auf einem neuen PC/Mac oder wenn der Ordner kopiert wurde):
   - **macOS / Linux:** `sh setup.sh` (installiert bei Bedarf Python 3.12 über Homebrew)
   - **Windows:** `powershell -ExecutionPolicy Bypass -File .\setup.ps1` (installiert bei Bedarf Python 3.12 über winget)

   Das Setup erkennt das Betriebssystem, legt `.venv` an (bzw. neu an, wenn sie von einem anderen Rechner/OS stammt),
   installiert das Tool `lern` und verlinkt die Skills. Vergisst du es, erledigt das der Sessionstart-Hook automatisch,
   sobald ein Python ≥ 3.11 vorhanden ist.
2. Repo-Ordner öffnen in
   - **Claude Desktop → Tab „Code“** (empfohlen: Bilder/PDFs per Drag & Drop) oder `claude` im Terminal,
   - **Codex-App** oder `codex` im Terminal. Beim ersten Start mit `/hooks` den Lernstand-Hook als vertrauenswürdig bestätigen.
3. Loslegen, z. B.:
   - „Lass uns lernen“ → Warm-up + Plan (Skill `lernen`)
   - „Hier ist Aufgabe 3 von Übung 5“ + Foto/PDF → geführtes Durcharbeiten (Skill `aufgabe`)
   - „Erklär mir die NTU-Methode“ (Skill `thema`)
   - „Mach Anki-Karten zu heute“ (Skill `karten`)
   - „Analysier die Altklausuren“ / „Simulier eine Klausur“ (Skill `klausur`)
   - „Schluss für heute“ → Sitzungsnotiz, Karten-Export, Dashboard, Commit (Skill `sitzung-ende`)

## Mit Kommilitonen teilen / Einstieg in einen bestehenden Kurs

Das Repo enthält kein Originalmaterial (Urheberrecht, Größe) – nur Struktur, Themen, Aufgabenkatalog und Wegweiser.

```sh
git clone https://github.com/JakobHeuerUno/Lernmastertool LERNECKE && cd LERNECKE
git checkout kurs/waerme-stoffuebertragung        # geteiltes Kursgerüst, Lernstand 0 %
git checkout -b <deinname>/waerme-stoffuebertragung   # dein persönlicher Branch für den Lernstand
sh setup.sh                                        # Windows: powershell -ExecutionPolicy Bypass -File .\setup.ps1
./lern abgleich "<Pfad zum Moodle-Export>"         # zeigt, was zugeordnet wird; danach mit --los ausführen
```

`lern abgleich` erkennt jede Datei an ihrer Prüfsumme (auch in `.imscc`-Archiven) und legt sie in genau den Pfad, auf den
Themen und Aufgaben verweisen; danach werden die Texte erzeugt. Unbekannte Dateien (neues Material) meldet es – die sortiert der Agent ein.
Updates holen: `git pull` auf `kurs/<id>`, dann im eigenen Branch `git merge kurs/<id>`. Branch-Regeln: `AGENTS.md` Abschnitt 6.

## Neuen Kurs anlegen

Sag dem Agenten „Neuer Kurs: <Name>“ (Skill `kurs-einrichten`) oder manuell:

```sh
./lern kurs neu technische-mechanik-2 "Technische Mechanik 2" --kuerzel tm2   # Windows PowerShell: .\lern.cmd …
./lern kurs aktiv technische-mechanik-2
```

Danach Unterlagen in `kurse/<kurs>/inbox/` legen. Der Agent sortiert sie ein, liest sie und baut die Themenlandkarte.

## Wie der Fortschritt gemessen wird

Das Sprachmodell **beurteilt** (Fehlerursachen, Missverständnisse), das Tool `lern` **zählt** (deterministisch, aus `lernstand/ereignisse.jsonl`):

| Stufe | Bedeutung |
|---|---|
| 0 neu | noch nicht behandelt |
| 1 gesehen | erklärt bekommen / nachvollzogen |
| 2 mit Hilfe | mit Hinweisen gelöst oder Abruffragen richtig |
| 3 selbstständig | Übungsaufgabe ohne Hilfe gelöst |
| 4 klausurfest | ≥ 2× selbst gelöst mit ≥ 7 Tagen Abstand, oder in der Klausursimulation |

- Offene Fehler im Fehlerbuch deckeln ein Thema auf Stufe 2. Oft vergessene Anki-Karten deckeln auf Stufe 3.
- Ein Thema auf Stufe 3 oder 4, das länger als 21 Tage nicht geübt wurde, wird als „auffrischen“ markiert.
- **Wurde eine Aufgabe nur erklärt, gilt sie nicht als gekonnt.** Sie wird nach 3 Tagen zum Nachrechnen ohne Hilfe eingeplant, nach Erfolg nochmal nach 10 Tagen.
- Abdeckung und Beherrschung sind nach Klausurrelevanz (1–3) gewichtet.

## Befehle (`./lern …` auf macOS/Linux/Git Bash, `.\lern.cmd …` in Windows PowerShell)

| Befehl | Zweck |
|---|---|
| `brief` / `status` / `weiter` / `aufgaben` | Lernstand kompakt / ausführlich / Empfehlung / Aufgabenstatus |
| `dashboard` | `ausgabe/dashboard.html` erzeugen (im Browser öffnen) |
| `kurs neu\|aktiv\|liste` | Kurse verwalten |
| `inbox`, `einsortieren`, `einlesen`, `seite` | Material aufnehmen, PDFs → Text, Seite als Bild |
| `abgleich <ordner> [--los]` | eigenes Material per Prüfsumme in die Kursstruktur einordnen, neues Material erkennen |
| `index` | `INDEX.md` (Wegweiser Thema → Quellen/Aufgaben) neu erzeugen |
| `log versuch\|fehler\|frage\|sitzung`, `fehler behoben` | Lernereignisse (macht normalerweise der Agent) |
| `karten naechste-id\|liste`, `anki export\|push\|pull` | Karteikarten und Anki |
| `pruefen` | Konsistenzcheck aller Kursdaten |

## Anki

Datenfluss: Repo → Anki-Desktop (AnkiConnect) ⇄ AnkiWeb ⇄ Handy (AnkiDroid/AnkiMobile). Einrichtung und Hilfe bei Problemen: Sag dem Agenten einfach „Anki“ (Skill `anki`).

Einrichtung in Kurzform:
1. Anki-Desktop von https://apps.ankiweb.net installieren.
2. Extras → Erweiterungen → „Erweiterungen herunterladen…“ → Code `2055492159` (AnkiConnect).
3. **Anki komplett schließen und neu starten.** Erst dann ist AnkiConnect aktiv.
4. AnkiWeb-Konto auf https://ankiweb.net anlegen. In Anki auf „Synchronisieren“ klicken und anmelden.
5. Am Handy AnkiDroid (Android) oder AnkiMobile (iOS) mit demselben Konto anmelden.

- **Mit Anki-Desktop + Add-on AnkiConnect** (Code `2055492159`) und AnkiWeb-Login: `lern anki sync`.
  1. Er holt zuerst den Handy-Fortschritt von AnkiWeb.
  2. Dann liest er die Statistik aus, also welche Karten du oft vergisst. Das fließt in Lernstand und Empfehlungen ein.
  3. Danach importiert er nur geänderte oder fehlende Karten.
  4. Zum Schluss lädt er alles für das Handy hoch.

  Schlägt der erste Sync fehl, bricht er ab, bevor sich etwas ändert. Beim Sessionstart und am Sitzungsende läuft der Abgleich automatisch (`--still`: ist Anki zu, wird er übersprungen).
- **Fremde Stapel** (z. B. von Kommilitonen oder StudyDrive): Importiere den Stapel einfach in Anki. `lern anki sync` erkennt ihn und fragt nach.
  Mit `lern anki fremd uebernehmen "<Name>"` wird er dem Kurs zugeordnet. Seine Statistik fließt dann in den Lernstand ein, und der Agent kann die Karten auf Wunsch einem Thema zuordnen, gegen das Skript prüfen und korrigieren (`karten-fremd/*.yaml`).
  Die Änderungen gehen an dieselben Anki-Notizen, die Lernhistorie bleibt erhalten.
- **Ohne Anki-Desktop:** `lern anki export` erzeugt `ausgabe/<kurs>.apkg`. Die Datei über **Datei → Importieren** einlesen, das geht auch direkt am Handy. Ein erneuter Import aktualisiert die Karten, und dein Lernfortschritt bleibt erhalten. So kommt aber keine Statistik zurück ins Repo.
- Beide Wege nutzen dieselben Karten-GUIDs, daher entstehen keine Duplikate.

## Aufbau

- `AGENTS.md`: Tutor-Regeln für Claude und Codex. `CLAUDE.md` importiert diese Datei.
- `.agents/skills/`: Skills für beide Agenten. `.claude/skills` ist ein Link darauf (Windows: Junction, sonst Symlink; legt das Setup an).
- `.claude/settings.json` und `.codex/hooks.json`: Sie spielen beim Sessionstart den Lernstand ein (`lern brief --hook`) und richten auf einem neuen Rechner vorher automatisch die `.venv` ein.
- `setup.sh` / `setup.ps1` → `einrichten.py`: plattformübergreifendes Setup. `lern` / `lern.cmd`: Launcher, die die passende `.venv` finden.
- `STAND.md`: Lernstand als Datei, für Umgebungen ohne Hooks (z. B. Claude Cowork oder ChatGPT Work).
- `profil/lernprofil.md`: kursübergreifendes Lernprofil.
- `kurse/<kurs>/`: siehe Abschnitt 5 in `AGENTS.md`. Originalmaterial (`material/`, `inbox/`) und `text/` sind von Git ausgeschlossen.
- `src/lern/` + `tests/`: das Python-Tool. Tests: `sh setup.sh --tests` bzw. `setup.ps1 -Tests`.
