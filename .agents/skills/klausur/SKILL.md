---
name: klausur
description: Klausurvorbereitung in der LERNECKE – Altklausuren analysieren (Klausur-Radar, welche Themen wie oft und mit wie vielen Punkten drankommen) und Klausursimulationen unter Zeitdruck mit Punktebewertung durchführen. Nutzen bei "Altklausur", "Probeklausur", "was kommt in der Klausur dran", "Klausur simulieren".
---

# Klausur

## A. Klausur-Radar (Altklausuren analysieren)
1. Alle Altklausuren in `material/altklausuren/` (ggf. erst einsortieren, Skill `kurs-einrichten`). Text in `text/altklausuren/`.
2. Jede Aufgabe → Eintrag in `aufgaben.yaml` (id `ak<jahr>[-<termin>]-a<nr>`, themen, Punkte im Titel oder als Feld `punkte`).
3. Auswertung pro Thema: in wie vielen Klausuren, Punkteanteil. Ergebnis als Tabelle dem Nutzer zeigen und in `KURS.md` unter „Klausur-Radar“ speichern (mit Stand-Datum).
4. `klausurrelevanz` in `themen.yaml` setzen: 3 = in ≥ 60 % der Klausuren, 2 = gelegentlich, 1 = selten/nie. `lern pruefen`.
5. Muster notieren: wiederkehrende Aufgabentypen („Aufgabe 1 ist immer Rohr mit Isolierung“), typische Fallen, Punktverteilung.

## B. Klausursimulation
1. Rahmen klären: ganze Altklausur oder gemischte Aufgaben (Interleaving über mehrere Themen – bevorzugt, sobald die meisten Themen ≥ Stufe 2 sind), Zeit wie in `kurs.yaml: klausur.dauer_min` bzw. anteilig nach Punkten, erlaubte Hilfsmittel wie in der echten Klausur.
2. Aufgaben stellen, **keine Hinweise** während der Bearbeitungszeit. Der Nutzer rechnet auf Papier und schickt Ergebnisse/Fotos.
3. Korrektur wie ein Prüfer: Punkte pro Teilaufgabe nach offizieller Lösung / Punkteschema, Folgefehler fair berücksichtigen.
4. Loggen pro Teilaufgabe: `lern log versuch --aufgabe <id> --teil <x> --art klausur --ergebnis selbst|falsch` (Teilpunkte: ≥ 70 % = selbst). Fehler mit Typ ins Fehlerbuch.
5. Auswertung: Punkte/Note-Schätzung, Zeitverbrauch, Fehlertypen-Muster (Konzept vs. Rechnung vs. Zeit), 3 konkrete Prioritäten für die nächsten Tage.
6. Danach ggf. die falschen Teile mit Skill `aufgabe` nacharbeiten.

## C. Lernplan bis zur Klausur (auf Wunsch)
Aus `lern status` (Prognose, Stufen) und Klausur-Radar: Wochenplan mit Themen nach (Relevanz × Lücke), Puffer für Nachrechnen und 2–3 Simulationen in den letzten zwei Wochen. In `KURS.md` unter „Lernplan“ ablegen.
