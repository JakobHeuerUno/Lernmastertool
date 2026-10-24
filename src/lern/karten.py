"""Karteikarten im Markdown-Format.

Format (je Karte):

    ### wsu-0042 · thema: rippen · quelle: Skript S. 34
    F: Frage (mehrzeilig möglich)
    B: Antwort

    ### wsu-0043 · thema: rippen
    C: Der Rippenwirkungsgrad ist {{c1::das Verhältnis ...}}.
    Z: optionaler Zusatz / Merkhilfe
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from lern.daten import Kurs

_KOPF = re.compile(r"^###\s+(?P<id>[A-Za-z0-9_-]+)\s*(?P<rest>.*)$")
_FELD = re.compile(r"^(?P<k>[FBCZ]):\s?(?P<v>.*)$")


@dataclass
class Karte:
    id: str
    datei: Path
    zeile: int
    thema: str = ""
    quelle: str = ""
    frage: str = ""
    antwort: str = ""
    cloze: str = ""
    zusatz: str = ""
    probleme: list[str] = field(default_factory=list)

    @property
    def ist_cloze(self) -> bool:
        return bool(self.cloze)


def parse_datei(pfad: Path) -> list[Karte]:
    karten: list[Karte] = []
    aktuell: Karte | None = None
    feld: str | None = None
    im_code = False
    for nr, zeile in enumerate(pfad.read_text(encoding="utf-8").splitlines(), 1):
        if zeile.lstrip().startswith("```"):
            im_code = not im_code
            continue
        if im_code:
            continue
        kopf = _KOPF.match(zeile)
        if kopf:
            aktuell = Karte(kopf["id"], pfad, nr)
            for teil in kopf["rest"].split("·"):
                if ":" in teil:
                    k, v = teil.split(":", 1)
                    k = k.strip().lower()
                    if k in ("thema", "quelle"):
                        setattr(aktuell, k, v.strip())
            karten.append(aktuell)
            feld = None
            continue
        if aktuell is None:
            continue
        if zeile.startswith("#"):
            aktuell, feld = None, None
            continue
        m = _FELD.match(zeile)
        if m:
            feld = {"F": "frage", "B": "antwort", "C": "cloze", "Z": "zusatz"}[m["k"]]
            setattr(aktuell, feld, m["v"])
        elif feld:
            setattr(aktuell, feld, getattr(aktuell, feld) + "\n" + zeile)
    for k in karten:
        for name in ("frage", "antwort", "cloze", "zusatz"):
            setattr(k, name, getattr(k, name).strip())
        if k.cloze:
            if "{{c" not in k.cloze:
                k.probleme.append("C:-Karte ohne {{c1::…}}-Lücke")
        elif not (k.frage and k.antwort):
            k.probleme.append("F: und B: (oder C:) fehlen")
    return karten


def lade_karten(kurs: Kurs) -> list[Karte]:
    ordner = kurs.pfad / "karten"
    if not ordner.is_dir():
        return []
    karten: list[Karte] = []
    for datei in sorted(ordner.glob("*.md")):
        if datei.name.lower() == "readme.md":
            continue
        karten.extend(parse_datei(datei))
    return karten


def naechste_id(kurs: Kurs) -> str:
    praefix = f"{kurs.kuerzel}-"
    hoechste = 0
    for k in lade_karten(kurs):
        if k.id.startswith(praefix) and k.id[len(praefix):].isdigit():
            hoechste = max(hoechste, int(k.id[len(praefix):]))
    return f"{praefix}{hoechste + 1:04d}"
