---
name: karten
description: Karteikarten für Anki erstellen, exportieren oder synchronisieren und auf Wunsch im Chat abfragen. Nutzen bei "mach Karten", "Anki", "Karteikarten exportieren", "frag mich ab", und am Ende von Aufgaben/Themen/Sitzungen.
---

# Karteikarten

## Karten schreiben (`kurse/<kurs>/karten/<thema-oder-kapitel>.md`)
Format siehe `karten/README.md`. Nächste freie ID: `lern karten naechste-id` (bei mehreren Karten hochzählen).
IDs **nie ändern oder wiederverwenden** – Anki hängt die Lernhistorie daran; Text darf später verbessert werden.

Gute Karten (Minimum-Information-Prinzip):
- **Eine** Information pro Karte; Antwort in Sekunden abrufbar.
- Frage so präzise, dass genau eine Antwort passt („Wovon hängt die Nußelt-Zahl bei erzwungener laminarer Rohrströmung ab?“).
- Formeln: als Lückentext (`C:` mit `{{c1::…}}`), nicht die ganze Formel als Antwort; Symbole und Einheiten auf der Rückseite/Zusatz erklären.
- **Warum-Karten** für Konzepte („Warum steigt α bei turbulenter Strömung?“) und **Wann-Karten** für Methodenwahl („Wann NTU statt LMTD?“).
- **Jeder Fehler aus dem Fehlerbuch wird eine Karte**, die genau das Missverständnis abfragt (Quelle: `F-007`).
- Kennzahlen (Re, Pr, Nu, Bi, Gr, Ra, Sh, Sc, Le …): Definition, physikalische Bedeutung, typische Werte – je eigene Karte.
- Kurs-Notation verwenden; `thema:` immer setzen (steuert Anki-Deck nach Kapitel und die Mastery-Auswertung), `quelle:` wenn möglich.
- Bei Open-Book-Klausuren weniger Formel-Auswendiglernen, mehr Konzept-/Methodenkarten.
- Nach dem Schreiben: `lern pruefen`.

## Nach Anki bringen
- Standard: `lern anki export` → `ausgabe/<kurs>.apkg`. Dem Nutzer sagen: In Anki **Datei → Importieren**; erneuter Import aktualisiert geänderte Karten, Lernfortschritt bleibt. (Auch AnkiDroid/AnkiMobile können .apkg importieren.)
- Wenn Anki-Desktop mit Add-on **AnkiConnect** (Code 2055492159) läuft: `lern anki push` (direkt einfügen/aktualisieren) und `lern anki pull` (holt, wie oft Karten vergessen wurden → fließt in Mastery und Brief).
  Pro Kurs bei **einem** Weg bleiben (Export *oder* Push), sonst entstehen zwei Notiztypen.
- Oft vergessene Karten (Brief: „Anki: oft vergessene Karten“) → Thema im Chat neu erklären oder Karte umformulieren/aufteilen.

## Abfrage im Chat (nur auf Wunsch)
- Karten bevorzugt aus schwachen Themen, offenen Fehlern oder mit vielen lapses (`lernstand/anki-stats.json`).
- Eine Frage pro Nachricht, Antwort abwarten, dann Rückmeldung + bei Fehler kurze Erklärung.
- Loggen: `lern log versuch --thema <id> --art karte --ergebnis selbst|falsch`.
