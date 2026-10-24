---
name: kurs-einrichten
description: Neuen Kurs in der LERNECKE anlegen oder neues Kursmaterial aufnehmen (Folien, Skript, Übungen, Lösungen, Altklausuren, StudyDrive). Nutzen bei "neuer Kurs", "ich hab neue Folien/Unterlagen", "Material einsortieren", "Themenübersicht erstellen".
---

# Kurs einrichten / Material aufnehmen

## 1. Kurs anlegen (nur wenn neu)
- `lern kurs neu <id> "<Name>" --kuerzel <3-4 Buchstaben>` (id: kebab-case ohne Umlaute, z. B. `technische-mechanik-2`), dann `lern kurs aktiv <id>`.
- Mit dem Nutzer `kurs.yaml` füllen: Semester, Uni, Dozent, **Klausur** (Datum JJJJ-MM-TT, Dauer, Hilfsmittel, Format). Unbekanntes leer lassen und später nachfragen.

## 2. Material einsortieren
- Nutzer legt Dateien in `kurse/<id>/inbox/` (oder nennt einen Ordner). `lern inbox` listet sie.
- Pro Datei Typ bestimmen (Dateiname/Inhalt ansehen; im Zweifel fragen):
  `folien` · `skript` · `uebungen` (Aufgabenblätter, Selbstrechenübungen) · `loesungen` · `altklausuren` · `studydrive` · `sonstiges`.
- `lern einsortieren <dateien…> --typ <typ>` (StudyDrive automatisch `inoffiziell`; Altklausur-Lösungen von Studis: `--vertrauen inoffiziell`).
- `lern einlesen` wandelt neue/geänderte PDFs nach `text/` (Markdown mit `<!-- seite N -->`). Stichprobe prüfen: Sind Formeln brauchbar? Wenn nicht, beim Unterrichten Originalseiten per `lern seite` ansehen und in `KURS.md` vermerken („Skript-Formeln nur als Bild lesbar“).

## 3. Themenlandkarte (`themen.yaml`)
- Aus Skript-Gliederung (bevorzugt) und Folientiteln die Themen ableiten. Granularität: ein Thema = etwas, das man in einer Übungsaufgabe anwendet (typisch 15–40 Themen pro Kurs). Reihenfolge = Vorlesungsreihenfolge.
- Pro Thema: `id` (kebab-case, **danach nie ändern**), `titel`, `kapitel`, `voraussetzungen` (ids), `quellen` (z. B. `skript S. 12-18`, `folien/VL03 S. 4-20`), `lernziele` (2–4, als „kann …“), `klausurrelevanz` (1–3; ohne Altklausuren vorläufig 2).
- **Dem Nutzer als kompakte Liste zur Bestätigung zeigen**, dann schreiben, `lern pruefen`.
- Bei neuem Material: bestehende ids behalten, nur ergänzen; `quellen` erweitern.

## 4. Aufgabenkatalog (`aufgaben.yaml`)
- Für Übungsblätter / Selbstrechenübungen / Altklausuren: jede Aufgabe als Eintrag (id-Schema siehe Skill `aufgabe`), mit `quelle`, `loesung` (falls vorhanden), `loesung_vertrauen`, `themen`. Die `.md`-Datei pro Aufgabe wird erst beim Bearbeiten angelegt (`datei` dann ergänzen).
- `lern pruefen`.

## 5. Klausur-Infos & Kurshinweise
- Altklausuren vorhanden → Skill `klausur` (Klausur-Radar setzt `klausurrelevanz`).
- `KURS.md`: Besonderheiten festhalten (Notation, Lösungsschema der Übung, Schwerpunkte des Profs, Qualität der Materialien). `kurs.yaml: notation` für Symbole (z. B. `alpha: "Wärmeübergangskoeffizient α"`).

## 6. Abschluss
- `lern status` zeigen; `lern dashboard`; Git-Commit („Kurs <id> eingerichtet“ / „Material ergänzt“). Originale in `material/` sind per .gitignore ausgeschlossen – nur Index/Struktur werden versioniert.
