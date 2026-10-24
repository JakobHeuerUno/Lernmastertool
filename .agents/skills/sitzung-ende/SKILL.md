---
name: sitzung-ende
description: Lernsession in der LERNECKE sauber abschließen – Sitzungsnotiz mit nächsten Schritten schreiben, Lernprofil aktualisieren, Karten exportieren, Dashboard erzeugen, Lernstand committen. Nutzen bei "Schluss für heute", "ich mach Schluss", "fertig", "Pause", "bis morgen".
---

# Sitzung abschließen

1. **Nachloggen**: Ist alles aus dieser Session in `lernstand/` (Versuche, Fehler, Fragen)? Fehlendes jetzt mit `lern log …` nachtragen. Fehlerbuch-Einträge ohne „Ursache“/„Richtig ist“ ergänzen.
2. **Sitzungsnotiz** `kurse/<kurs>/lernstand/sitzungen/JJJJ-MM-TT-HHMM.md`:
   ```markdown
   # Sitzung JJJJ-MM-TT HH:MM (ca. N min)
   ## Bearbeitet
   - …
   ## Was gut lief / was geklickt hat
   - …
   ## Schwierigkeiten
   - … (F-…)
   ## Nächste Schritte
   - …
   ```
3. **Ereignis**: `lern log sitzung "<Zusammenfassung in einem Satz>" --naechster "<Schritt 1>" --naechster "<Schritt 2>" --dauer <min> --datei lernstand/sitzungen/<datei>.md`
   (Die nächsten Schritte erscheinen beim nächsten Sessionstart im Brief – konkret formulieren.)
4. **Lernprofil** `profil/lernprofil.md`: nur aktualisieren, wenn sich ein **Muster** zeigt (z. B. dritte Einheiten-Verwechslung, eine Erklärart funktioniert wiederholt). „Kurzprofil“ ≤ 8 Zeilen halten.
5. **Karten**: neue Karten dieser Session vorhanden → `lern pruefen`, dann `lern anki export` (bzw. `push`, wenn der Nutzer AnkiConnect nutzt) und Hinweis zum Import geben.
6. **Dashboard**: `lern dashboard` → Pfad nennen (`ausgabe/dashboard.html`).
7. **Commit** des Lernstands (Repo-Wurzel):
   `git add -A` und `git commit -m "Sitzung JJJJ-MM-TT: <Kurzbeschreibung>"`. (Originalmaterial ist per .gitignore ausgeschlossen.)
8. **Verabschiedung**: 2–3 Sätze – Fortschritt heute, nächster Schritt, ggf. wann Nachrechnen fällig ist.
