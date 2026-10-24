---
name: thema
description: Ein neues Thema oder Konzept eines Kurses in der LERNECKE erarbeiten (z. B. "erklär mir Rippen", "was ist die NTU-Methode", "Vorlesung 5 nacharbeiten"). Strukturierter Ablauf aus Lernzielen, Vorwissen, Erklärung in Häppchen, Check-Fragen und Mini-Aufgabe.
---

# Thema erarbeiten

1. **Einordnen**: Thema in `themen.yaml` finden (Lernziele, Voraussetzungen, Quellen, Klausurrelevanz).
   Fehlt es: mit dem Nutzer kurz klären und eintragen (`lern pruefen`).
   Voraussetzungen mit niedriger Stufe (Brief/`lern status`)? → erst eine kurze Abruffrage dazu; bei Lücke zuerst die schließen.
2. **Material lesen**: relevante Seiten in `kurse/<kurs>/text/` (Skript vor Folien), ggf. Originalseiten rendern (`lern seite`). Notation und Herleitung wie im Kurs.
3. **Vorwissen aktivieren**: eine Frage, die an Bekanntes anknüpft („Was weißt du noch über den Wärmeleitwiderstand der ebenen Wand?“).
4. **Erklären in Häppchen** (je Nachricht eine Idee):
   physikalische Intuition / Alltagsbild → Skizze/System → Kernformel mit Bedeutung jedes Symbols und Einheit → Gültigkeitsgrenzen/Annahmen → typische Klausurfalle.
   Nach jedem Häppchen eine kurze Check- oder Vorhersagefrage, nicht „verstanden?“.
   Erklärarten aus `profil/lernprofil.md` bevorzugen, die bei diesem Nutzer funktionieren.
5. **Mini-Aufgabe**: kleine Rechen- oder Verständnisaufgabe (selbst ausgedacht oder aus dem Material), geführt nach Skill `aufgabe` Teil B. Loggen mit `--thema` (und `--aufgabe`, falls aus dem Katalog).
6. **Sichern**:
   - Was erklärt wurde: `lern log versuch --thema <id> --ergebnis erklaert` (sofern nicht schon über die Mini-Aufgabe geloggt).
   - Hat eine bestimmte Erklärung/Analogie geklickt → als Notiz nach `notizen/<thema-id>.md` (kurz, in eigenen Worten, mit Quelle) und ggf. `lern log frage --hilfreich …`.
   - 2–4 Karten nach Skill `karten`.
7. Zum Schluss: welche Übungsaufgabe aus `aufgaben.yaml` / dem Material dieses Thema als Nächstes festigt → als nächsten Schritt vorschlagen.
