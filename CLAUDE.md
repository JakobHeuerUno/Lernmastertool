@AGENTS.md

## Nur für Claude Code

- Vor jedem Commit Branch prüfen: Kursarbeit nur auf `kurs/<id>`, Tool/Skills nur auf `master` (AGENTS.md Abschnitt 6).
- Skills liegen in `.claude/skills/` (Link auf `.agents/skills/`, angelegt vom Setup) und sind als `/lernen`, `/aufgabe`, … aufrufbar.
- Lerntool im Bash-Tool immer als `./lern <befehl>` aufrufen (funktioniert unter Windows/Git Bash und macOS gleich).
- PDFs kannst du auch direkt mit dem Read-Tool lesen (`pages`-Parameter). Für Suche trotzdem `kurse/<kurs>/text/` nutzen.
- Vom Nutzer in den Chat eingefügte Bilder/Screenshots sind nicht als Datei gespeichert: Aufgabenstellung deshalb immer nach `kurse/<kurs>/aufgaben/<id>.md` transkribieren.
