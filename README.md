# LERNECKE

Persönliche Lernumgebung für Uni-Kurse. Man öffnet sie mit **Claude Code** oder **Codex** (CLI oder Desktop-App) und lernt einfach weiter.
Jede Session weiß automatisch, wo du stehst, welche Fehler offen sind und welche Erklärungen dir geholfen haben.

## Schnellstart

1. Einmalig (oder nach dem Klonen auf einen neuen PC): `powershell -ExecutionPolicy Bypass -File .\setup.ps1`
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

## Neuen Kurs anlegen

Sag dem Agenten „Neuer Kurs: <Name>“ (Skill `kurs-einrichten`) oder manuell:

```powershell
.\lern.cmd kurs neu technische-mechanik-2 "Technische Mechanik 2" --kuerzel tm2
.\lern.cmd kurs aktiv technische-mechanik-2
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

## Befehle (`.\lern.cmd …` bzw. `.venv/Scripts/python -m lern …`)

| Befehl | Zweck |
|---|---|
| `brief` / `status` / `weiter` / `aufgaben` | Lernstand kompakt / ausführlich / Empfehlung / Aufgabenstatus |
| `dashboard` | `ausgabe/dashboard.html` erzeugen (im Browser öffnen) |
| `kurs neu\|aktiv\|liste` | Kurse verwalten |
| `inbox`, `einsortieren`, `einlesen`, `seite` | Material aufnehmen, PDFs → Text, Seite als Bild |
| `log versuch\|fehler\|frage\|sitzung`, `fehler behoben` | Lernereignisse (macht normalerweise der Agent) |
| `karten naechste-id\|liste`, `anki export\|push\|pull` | Karteikarten und Anki |
| `pruefen` | Konsistenzcheck aller Kursdaten |

## Anki

- Standard: `lern anki export` erzeugt `ausgabe/<kurs>.apkg`. In Anki über **Datei → Importieren** einlesen. Ein erneuter Import aktualisiert die Karten, dein Lernfortschritt bleibt erhalten.
- Komfortabler: Anki-Desktop installieren und das Add-on **AnkiConnect** hinzufügen (Code `2055492159`). Dann schickt der Agent die Karten direkt in Anki (`anki push`). Mit `anki pull` liest er aus, welche Karten du oft vergisst, und berücksichtigt das bei Lernstand und Empfehlungen. Pro Kurs nur einen der beiden Wege nutzen.
- Handy: Anki über AnkiWeb synchronisieren (AnkiDroid/AnkiMobile).

## Aufbau

- `AGENTS.md`: Tutor-Regeln für Claude und Codex. `CLAUDE.md` importiert diese Datei.
- `.agents/skills/`: Skills für beide Agenten. `.claude/skills` ist eine Junction darauf.
- `.claude/settings.json` und `.codex/hooks.json`: Sie spielen beim Sessionstart den Lernstand ein (`lern brief --hook`).
- `STAND.md`: Lernstand als Datei, für Umgebungen ohne Hooks (z. B. Claude Cowork oder ChatGPT Work).
- `profil/lernprofil.md`: kursübergreifendes Lernprofil.
- `kurse/<kurs>/`: siehe Abschnitt 5 in `AGENTS.md`. Originalmaterial (`material/`, `inbox/`) und `text/` sind von Git ausgeschlossen.
- `src/lern/` + `tests/`: das Python-Tool. Tests laufen mit `.venv\Scripts\python -m pytest`.
