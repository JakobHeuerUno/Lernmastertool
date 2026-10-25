---
name: lernen
description: Lernsession in der LERNECKE beginnen oder fortsetzen. Nutzen, wenn der Nutzer "lass uns lernen", "weiter", "wo war ich", "was steht an" sagt oder ohne konkreten Auftrag startet. Liest den Lernstand, macht ein kurzes Abruf-Warm-up und schlägt einen Sitzungsplan vor.
---

# Lernsession starten / fortsetzen

1. **Lernstand holen**: Ist der Brief („LERNECKE – Lernstand“) schon im Kontext, nutze ihn. Sonst
   `./lern brief` (Windows PowerShell: `.\lern.cmd brief`; richtet bei Bedarf die `.venv` ein, siehe AGENTS.md Abschnitt 0). Will der Nutzer einen anderen Kurs: `lern kurs liste` → `lern kurs aktiv <id>`.
   Steht im Brief eine Zeile „**Anki:** letzter Abgleich …“ (der Nutzer nutzt AnkiConnect): `lern anki sync --still` ausführen.
   So fließt der Handy-Fortschritt ein. Ist Anki zu, wird der Abgleich still übersprungen. Bei einem Sync-Fehler gilt Skill `anki`.
   **Neuer Nutzer** (Brief zeigt kein Lernprofil, oder Hinweis „geteiltes Kursgerüst“): erst persönlichen Branch anlegen
   (`git checkout -b <name>/<kurs-id>`, Namen erfragen), meldet der Brief **Material fehlt** → `lern material holen` (Link steht in `lern.lokal.yaml`; sonst Nutzer nach Cloud-Link + Passwort fragen
   und mit Einverständnis dort eintragen) bzw. eigenen Moodle-Export mit `lern abgleich <ordner> --los`;
   dann 3 kurze Fragen (Arbeitsweise, gewünschter Tutor-Stil, Karteikarten/Anki ja/nein) → Kurzprofil in `profil/lernprofil.md`.
2. **Begrüßung in 2–3 Sätzen**: wo er steht (Klausur-Countdown, Beherrschung), was letztes Mal als nächster Schritt vereinbart war.
3. **Warm-up (2–3 Fragen, eine nach der anderen)** – Retrieval Practice, kurz und gezielt:
   - bevorzugt zu offenen Fehlern aus dem Fehlerbuch (prüft, ob das Missverständnis noch da ist),
   - sonst zu Themen der letzten Sitzung oder zu „auffrischen“-Themen.
   Erst antworten lassen, dann Feedback. Je Frage loggen: `lern log versuch --thema <id> --art abruf --ergebnis selbst|hinweise|falsch`.
   Ist ein offener Fehler jetzt sicher richtig: `lern fehler behoben F-…`.
   Der Nutzer kann das Warm-up überspringen („direkt los“) – dann nicht drängen.
4. **Sitzungsplan vorschlagen** (aus `lern weiter`), z. B.:
   - fällige Aufgabe ohne Hilfe nachrechnen (höchste Priorität – so wird aus „erklärt bekommen“ echtes Können),
   - dann neue Übungsaufgabe oder neues Thema,
   - Abschluss mit Karten + Sitzungsnotiz.
   Der Nutzer entscheidet. Bringt er eigene Aufgaben mit → Skill `aufgabe`.
5. Während der Session gelten die Log-Regeln aus AGENTS.md (sofort, ehrlich).
6. Signalisiert der Nutzer das Ende → Skill `sitzung-ende`.
