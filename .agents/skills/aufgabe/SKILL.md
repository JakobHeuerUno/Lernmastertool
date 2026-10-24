---
name: aufgabe
description: Eine Uni-Übungsaufgabe (Übungsblatt, Selbstrechenübung, Altklausur, StudyDrive) gemeinsam durcharbeiten und erklären – Hauptarbeitsmodus der LERNECKE. Nutzen, wenn der Nutzer eine Aufgabe als Bild/PDF/Text in den Chat gibt, eine Datei in inbox/ legt oder eine Aufgabe aus dem Material nennt ("Aufgabe 3.2", "Übung 5").
---

# Aufgabe durcharbeiten

## A. Aufgabe erfassen
1. **Quelle klären**
   - Datei in `kurse/<kurs>/inbox/` → `lern inbox`, Typ bestimmen (uebungen/loesungen/altklausuren/studydrive/…), dann
     `lern einsortieren <datei> --typ <typ> [--vertrauen inoffiziell]` (wandelt automatisch in `text/` um).
   - Bild/Text im Chat → Inhalt ist nicht gespeichert, also gleich in Schritt 2 vollständig transkribieren.
   - Aus vorhandenem Material → in `text/` suchen (Grep nach „Aufgabe 2“ o. ä.), ggf. `lern seite <pdf> <nr>` für Skizzen/Formeln.
2. **Aufgabe anlegen** (falls noch nicht in `aufgaben.yaml`):
   - ID-Schema: `ue03-a2` (Übung 3 Aufg. 2), `sru05-a1` (Selbstrechenübung), `ak2023-a1` (Altklausur), `sd-<kurz>` (StudyDrive).
   - Eintrag in `aufgaben.yaml`: id, titel (3–5 Wörter), quelle (Datei + Seite), loesung (Datei + Seite oder null), loesung_vertrauen, themen [ids aus themen.yaml], datei.
   - Datei `aufgaben/<id>.md` nach der Vorlage unten. Aufgabenstellung **wörtlich** mit allen Zahlenwerten und Einheiten, Formeln in LaTeX.
   - `lern pruefen`.
3. **Lösung suchen**: `material.yaml` / `text/loesungen/` durchsuchen. Offizielle Lösung = Referenz für deine Erklärung (nicht dem Nutzer vorlesen!). Inoffiziell → selbst nachrechnen.
4. **Vorgeschichte**: Brief/Fehlerbuch auf Fehler zu den Themen dieser Aufgabe prüfen. Gab es schon Versuche zu dieser Aufgabe (`lern aufgaben`)? Dann ist das ein Nachrechnen-Durchgang → so wenig Hilfe wie möglich.

## B. Durcharbeiten (geführt, Lösung auf Wunsch)
Für jede Teilaufgabe **der Reihe nach**:
1. Kurz orientieren: Gegeben / Gesucht / Skizze bzw. Systemgrenze / Annahmen. Den Nutzer das möglichst selbst benennen lassen.
2. „Wie würdest du anfangen?“ – auf Antwort warten.
3. Bei Hängern gestufte Hinweise, je eine Stufe pro Nachricht:
   1. Konzept („Was passiert physikalisch? Welcher Mechanismus dominiert?“)
   2. Ansatz („Bilanz um … / Gleichung aus Skript S. …“)
   3. nächster konkreter Schritt (Formel eingesetzt, aber nicht ausgerechnet)
4. „Lösung“ / „erklär einfach“ / „mach vor“ → vollständiger, sauber begründeter Weg (Kursnotation, Quelle). Danach eine kurze Verständnisfrage (z. B. „Was ändert sich, wenn die Wand doppelt so dick ist?“).
5. Ergebnis immer auf Plausibilität prüfen (Einheit, Größenordnung, Vorzeichen) und mit offizieller Lösung abgleichen.
6. **Sofort loggen** pro Teilaufgabe: `lern log versuch --aufgabe <id> --teil <x> --ergebnis …`.
   Bei einem echten Fehler (nicht Tippfehler): `lern log fehler --aufgabe <id> --teil <x> --thema <id> --typ <typ> "…"` und im `fehlerbuch.md` Ursache + „Richtig ist“ ergänzen.
   Verständnisfragen des Nutzers: `lern log frage …`.
7. Proaktiv auf bekannte Stolperstellen hinweisen, bevor der Nutzer reinläuft – aber als Frage, nicht als Lösung.

## C. Abschluss der Aufgabe
1. `aufgaben/<id>.md` vervollständigen: Lösungsweg (kompakt, nachvollziehbar), Ergebnisse, **Meine Stolperstellen** (konkret, mit Fehler-IDs), Merksatz.
2. 1–3 Karteikarten vorschlagen (Skill `karten`), z. B. zur Kernidee oder zum gemachten Fehler.
3. Hat der Nutzer Hilfe gebraucht, sag ihm, dass die Aufgabe in ca. 3 Tagen zum selbstständigen Nachrechnen eingeplant ist.

## Vorlage `aufgaben/<id>.md`

```markdown
# <id> – <Titel>

- **Quelle:** material/uebungen/Uebung03.pdf S. 2
- **Lösung:** material/loesungen/Loesung03.pdf S. 4 (offiziell)
- **Themen:** waermeleitung-zylinder, waermedurchgang

## Aufgabenstellung
<wörtlich, mit allen Werten; Skizze beschreiben>

## Lösungsweg
### a)
...

## Ergebnisse
- a) $\dot Q = 1{,}23\,\mathrm{kW}$

## Meine Stolperstellen
- (F-004) …

## Merksatz
...
```
