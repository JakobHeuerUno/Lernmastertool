"""INDEX.md: Wegweiser Thema → Quellen/Aufgaben, damit der Agent nicht suchen muss (token-sparend)."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path

from lern.daten import Kurs, lade_yaml

BILD_GRENZE = 150  # Zeichen Text pro Seite – darunter gilt ein PDF als „nur als Bild lesbar“
STERNE = {1: "★", 2: "★★", 3: "★★★"}


def _gruppe(aufgabe_id: str) -> str:
    """ak2025h-a2 → ak, sru03-a1 → sru, vru11-a2 → vru, sd-x → sd."""
    m = re.match(r"[a-z]+", aufgabe_id)
    return m.group(0) if m else "?"


def nur_bild(kurs: Kurs) -> list[tuple[str, int]]:
    """PDFs mit (fast) keiner Textebene: (Pfad, Seiten)."""
    daten = lade_yaml(kurs.pfad / "material.yaml", {}) or {}
    treffer = []
    for m in daten.get("material") or []:
        text, seiten = m.get("text"), m.get("seiten")
        if not text or not seiten:
            continue
        datei = kurs.pfad / text
        if not datei.is_file():
            continue
        inhalt = re.sub(r"<!--.*?-->", "", datei.read_text(encoding="utf-8"))
        if len(re.sub(r"\s+", "", inhalt)) / seiten < BILD_GRENZE:
            treffer.append((m["datei"], seiten))
    return sorted(treffer)


def _medien(kurs: Kurs) -> dict[str, list[str]]:
    medien = kurs.pfad / "medien"
    ordner: dict[str, list[str]] = defaultdict(list)
    if medien.is_dir():
        for p in sorted(medien.rglob("*")):
            if p.is_file():
                ordner[p.parent.relative_to(kurs.pfad).as_posix()].append(p.stem)
    return ordner


def erzeuge_index(kurs: Kurs) -> Path:
    themen = kurs.themen
    aufgaben = kurs.aufgaben
    je_thema: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for a in aufgaben:
        for t in a.get("themen") or []:
            je_thema[t][_gruppe(a["id"])].append(a["id"])

    z = [f"<!-- automatisch erzeugt von `lern index` – nicht von Hand bearbeiten (Quelle: themen.yaml, aufgaben.yaml, material.yaml) -->",
         f"# INDEX – {kurs.name}", "",
         "**Zuerst hier nachsehen, dann gezielt öffnen.** Pfade relativ zu `kurse/" + kurs.id + "/`.",
         "- Volltextsuche: `rg -n \"<Begriff>\" kurse/" + kurs.id + "/text` (Seitenmarker `<!-- seite N -->`; "
         "Duplikate/Englisch ausschließen mit `--glob '!**/en/**'`).",
         "- Originalseite ansehen (Formeln, Skizzen, Bild-PDFs): `lern seite <datei> <seite>` → PNG lesen.",
         "- Aufgabe → Datei/Seite/Lösung: `aufgaben.yaml` (Feld `quelle`, `loesung`, `herkunft`).",
         "- Kursregeln, Notation, Klausurformat: `KURS.md`, `kurs.yaml`; Häufigkeiten: `notizen/klausur-radar.md` (falls vorhanden).", ""]

    kapitel = None
    for t in themen:
        if t.get("kapitel") != kapitel:
            kapitel = t.get("kapitel")
            z += [f"## {kapitel}", ""]
        rel = STERNE.get(t.get("klausurrelevanz"), "")
        z.append(f"### {t.get('titel')} (`{t['id']}`) {rel}")
        if t.get("quellen"):
            z.append("- Quellen: " + " · ".join(t["quellen"]))
        gruppen = je_thema.get(t["id"], {})
        for g in sorted(gruppen, key=lambda g: (g == "ak", g)):
            ids = gruppen[g]
            z.append(f"- {g.upper()} ({len(ids)}): " + ", ".join(ids))
        if not gruppen:
            z.append("- Aufgaben: –")
        z.append("")

    unbekannt = sorted(set(je_thema) - {t["id"] for t in themen})
    if unbekannt:
        z += ["## Themen ohne Eintrag in themen.yaml", ", ".join(unbekannt), ""]

    daten = lade_yaml(kurs.pfad / "material.yaml", {}) or {}
    ordner = Counter()
    seiten = Counter()
    for m in daten.get("material") or []:
        o = Path(m["datei"]).parent.as_posix()
        ordner[o] += 1
        seiten[o] += m.get("seiten") or 0
    if ordner:
        z += ["## Material (Ordner · Dateien · Seiten)", ""]
        z += [f"- `{o}/` · {ordner[o]} · {seiten[o] or '–'}" for o in sorted(ordner)]
        z.append("")

    bild = nur_bild(kurs)
    if bild:
        z += [f"## Nur als Bild lesbar ({len(bild)}) – mit `lern seite` ansehen, nicht in text/ suchen", ""]
        z += [f"- `{d}` ({s} S.)" for d, s in bild]
        z.append("")

    medien = _medien(kurs)
    if medien:
        z += ["## Videos/Medien (`medien/`, nicht eingelesen; Dateiname = Lerneinheit/Übung)", ""]
        z += [f"- `{o}/`: " + ", ".join(namen) for o, namen in medien.items()]
        z.append("")

    ziel = kurs.pfad / "INDEX.md"
    ziel.write_text("\n".join(z).rstrip() + "\n", encoding="utf-8", newline="\n")
    return ziel
