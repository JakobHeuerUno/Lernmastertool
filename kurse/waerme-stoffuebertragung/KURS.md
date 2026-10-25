# Kurshinweise für den Tutor – WSÜ I (RWTH, WSA)

**Navigation: zuerst `INDEX.md` lesen** (Thema → Formelsammlung/Skript/Folien/Aufgaben). Erst danach gezielt in `text/` greppen.

## Lernmodus (Wunsch des Nutzers)
- Vorgehen **entlang der Vorlesungs-Themen** (Reihenfolge `themen.yaml`): pro Thema **erst verstehen** (Skill `thema`), **dann Aufgaben rechnen** (Skill `aufgabe`): SRU/VRU des Themas → passende Altklausur-Teilaufgaben.
- Erklärungen am **Skript** orientieren (Kapitel-Bände `material/skript/*`), aber auf dem Niveau des Nutzers – Niveau dynamisch an Lernstand/Fehlerbuch/Lernprofil anpassen.
- Folien/Videos der Lerneinheit (L-Nummer) als Ergänzung nennen, nicht als Pflicht.

## Änderungen WS 26/27 (Abgleich am 25.10.2026, Moodle-Stand bis PV04)
- **Folien L01–L17 (Wärmeleitung), Videos, VÜ01 sind byte-identisch** mit WS 25/26 → alte Unterlagen gelten weiter. Später folgende Einheiten beim Erscheinen wieder per Prüfsumme abgleichen.
- **Skript neu als Gesamtband** `skript/Skript_v1.1.1c.pdf` (377 S., gleiche Gliederung wie die alten 4 Bände) → **Hauptquelle**, Seiten in themen.yaml. Übungsteil stark erweitert (S. 311–377: II.1–20, III.1–16, IV.1–9, V.1–10, **ohne Lösungen**; als `sk-*` in aufgaben.yaml). Alte Bände `skript/{WL,KV,ST,SU}_*.pdf` nur noch Referenz (beim Greppen `--glob '!**/skript/[WKS][LVTU]_*'`).
- **Formelsammlung WS 26/27** `sonstiges/formelsammlung/FS_WS26-27.pdf` = V25/26 mit eingearbeiteten Korrekturen, **gleiche Seitenzahlen**: Betragsstriche bei Gr/Ar/Gr_s; D.11 jetzt Lewis-Zahl Le = Sc/Pr (Lewis-Gesetz g = α/c_p steht weiter in S.23, FS S. 42); Klammer bei Nu∞ = 3,66(η∞/ηW)^0,14; ṁ″ im Fickschen Gesetz; WÜ.5-Folgezeile „Lokale“ statt „Mittlere“ Nußelt-Zahl (nat. Konvektion, vertikale Platte, q̇″ = konst.); Heisler-Wärmeverlust-Diagramme mit vereinfachter Beschriftung (Q0 = mc(T0 − TU)).
- Neu: Einführungsvorlesung WS26, Lernpfad Wärmeleitung WS26 (SÜ 01–03), VRU01-Zusatz „Größenvergleich“ (kritischer Radius bei Kupfer ≈ 124 m) und interaktives Modell Warmwasserleitung (HTML).
- **Termine/Organisation:** Klausur voraussichtlich **Mi 10.02.2027**; Sprechstunde Mi 10:30 (Raum 315), ab 2027 Mi+Fr; vor der Klausur 01.–03., 05. und 09.02.2027.
- **Bonuspunkte (HeatQuiz):** 75 % der Lernpfad-Fragen richtig → 1 Punkt je Lernpfad, max. 3 aus 4. Frist = Sonntag nach letzter VRÜ des Themas: **Wärmeleitung 22.11.2026**, Konvektion 13.12.2026, Stoffübertragung 17.01.2027, Strahlung 07.02.2027 (Moodle-Tabelle nennt bei den letzten beiden versehentlich 2026). Login mit Code/Matrikelnummer prüfen!

## Material (Basis WS 25/26)
- Neuer Dozent ab WS 25/26 → Inhalt vermutlich weitgehend gleich. Bei neuem Material: Skript/Formelsammlung **diffen**, Änderungen hier unter „Änderungen WS 26/27“ notieren.
- **Formelsammlung** `sonstiges/formelsammlung/FS_WS26-27.pdf` (früher `FS_Klausur_V25-26.pdf`) = einziges Hilfsmittel → immer mit Seite zitieren und üben, die Formel *dort* zu finden. Korrekturen: `FS_Klausur_V25-26_Korrekturen.pdf` (Lewis-Zahl falsch dargestellt, fehlende Klammern/Betragsstriche, fehlender Punkt bei Massenstrom).
- **Skript (alt)**: 4 Bände mit Übungsteil am Ende (`VII Übungsaufgaben`, Übung II.x/V.x mit ★-Schwierigkeit). `skript/en/Heat_Transfer_Course_Reader.pdf` = englisches Gesamtwerk, inhaltsgleich → nur bei Bedarf (beim Greppen ausschließen: `--glob '!**/en/**'`).
- **Altklausuren** 2017H–2025H (+ 2026F leer) mit **offiziellen** Lösungen inkl. Punkteverteilung pro Gleichung (`loesungen/altklausuren/<JJJJ><F|H>_ML.pdf`). F = Februar-, H = Juli/August-Termin. 2021F fand nicht statt.
- **SRU** (Selbstrechenübung 01–11) und **VRU** (Vorrechenübung 01–14) = globale Nummerierung der Übungen. Viele davon sind ältere Klausuraufgaben (Herkunft in `aufgaben.yaml`).
- VRU-Lösungen sind Präsentationen/Handschrift (oft **ohne Textebene** → `lern seite` und Bild ansehen). Videos dazu in `medien/vru/`.
- **Textqualität** (`text/`, pymupdf4llm): Fließtext gut; Formeln in Skript/Formelsammlung oft zerstückelt (Brüche, Indizes) → zum Zitieren/Erklären von Formeln die Originalseite rendern (`lern seite`). 52 PDFs ohne Textebene: Liste in INDEX.md.
- Kochrezepte: Konvektion `sonstiges/erklaerungen/VRU06_Kochrezept_Konvektion.pdf`, Strahlung `folien/st/L12_…Kochrezept…pdf`.
- Das komplette Übungsskript (A1.x Strahlung, A2.x Wärmeleitung, A3.x Konvektion), auf das das FAQ verweist, fehlt; nur Einzelaufgaben liegen in VRU vor.

## Klausur: Format & Bewertungsregeln (aus Klausurinfos 2026)
- 120 min, 60 P., bestanden ab 30 P. ohne Bonuspunkte (Bonus über HeatQuiz nur im Vorlesungssemester).
- Lösungen in **vorgegebene Lösungskästchen** übertragen; nur diese werden bewertet. Kästchen pro Aufgabe doppelt; Nicht-Gewertetes durchstreichen.
- **Alternativlösungen → 0 Punkte** für die ganze Teilaufgabe.
- **Symbole/Indizes der Aufgabenstellung** verwenden; jede Größe gegeben oder als Funktion gegebener Größen definiert.
- „Herleiten“ → Endergebnis allein reicht nicht. „Angeben“ → darf aus der Formelsammlung übernommen werden (überflüssige Terme streichen, Nomenklatur anpassen).
- Physikalisch widersinnige Ergebnisse kommentieren. Anhang der Formelsammlung (Stoffwerte) darf genutzt werden – übernommene Werte kennzeichnen.
- **Skizzen** (A1 fast immer!): Gradienten an Kurvenenden als gestrichelte Tangenten; horizontale Gradienten, Asymptoten, Symmetrien, Geraden/Krümmungen eindeutig kennzeichnen; Achsen/Kurven beschriften, charakteristische Werte (T_U, T_max …) an die Achsen.
- Keine roten/grünen/lila Stifte, kein Bleistift.
- → Beim Üben genau dieses Format trainieren: Bilanz explizit hinschreiben, Symbole der Aufgabe, eine Lösung.

## Typischer Klausuraufbau (17 Klausuren gesichtet)
- A1: 3–4 unabhängige Kurzaufgaben quer durch alle Gebiete, viel Qualitatives (T(x)-/ξ(x)-Verläufe skizzieren, Grenzschichten, Einstrahlzahlen, kurze Abschätzungen).
- A2–A4: je ein Szenario, meist eins pro Gebiet; Wärmeleitung (Rippe/Quelle/Mehrschicht/instationär), Konvektion (fast immer Rohrströmung), Strahlung (Mehrkörper-Bilanz), Stoffübertragung (Diffusion/Stefanstrom) – häufig kombiniert.
- Details/Häufigkeiten: Klausur-Radar (`notizen/klausur-radar.md`).

## Lösungsschema der Übung
Gegeben → Gesucht → Skizze mit Systemgrenze → Annahmen (stationär? 1D? Quellen? Symmetrie?) → Bilanz (infinitesimal oder integral) → Ansatz/WÜK aus Formelsammlung (Gültigkeitsbereich prüfen!) → Rechnung → Plausibilität.
