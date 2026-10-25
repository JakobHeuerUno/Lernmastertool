"""Material per Prüfsumme abgleichen: Moodle-Export o. Ä. → material/ und medien/ (Pfade wie in material.yaml/medien.yaml).

So kann jeder, der den Kurs-Branch klont, sein eigenes Originalmaterial in exakt die Struktur bringen, auf die
themen.yaml und aufgaben.yaml verweisen. Unbekannte Dateien = neues oder geändertes Material.
"""

from __future__ import annotations

import hashlib
import shutil
import unicodedata
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO

from lern.daten import Kurs, lade_yaml, speichere_yaml

ARCHIVE = {".zip", ".imscc"}


def _sha1_strom(f: BinaryIO) -> str:
    h = hashlib.sha1()
    for block in iter(lambda: f.read(1 << 20), b""):
        h.update(block)
    return h.hexdigest()


def _sha1(pfad: Path) -> str:
    with pfad.open("rb") as f:
        return _sha1_strom(f)


def medien_index(kurs: Kurs) -> dict[str, dict]:
    """medien.yaml aktualisieren (Videos sind nicht in material.yaml; medien/archiv/ bleibt außen vor). Neu gehasht wird nur bei geänderter Größe."""
    datei = kurs.pfad / "medien.yaml"
    alt = {m["datei"]: m for m in (lade_yaml(datei, {}) or {}).get("medien") or []}
    medien = kurs.pfad / "medien"
    neu = {}
    for p in sorted(medien.rglob("*")) if medien.is_dir() else []:
        if not p.is_file() or p.name.startswith(".") or p.relative_to(medien).parts[0] == "archiv":
            continue  # medien/archiv/ = Ablage (entpackte Archive, Duplikate), nicht abgleichen
        rel = unicodedata.normalize("NFC", p.relative_to(kurs.pfad).as_posix())
        groesse = p.stat().st_size
        e = alt.get(rel)
        neu[rel] = e if e and e.get("groesse") == groesse else {"datei": rel, "groesse": groesse, "sha1": _sha1(p)}
    if neu != alt:
        speichere_yaml(datei, {"medien": [neu[k] for k in sorted(neu)]})
    return neu


def _ziele(kurs: Kurs) -> dict[str, list[str]]:
    """sha1 → Zielpfade (eine Datei kann an mehreren Stellen liegen)."""
    ziele: dict[str, list[str]] = {}
    for index, schluessel in (("material.yaml", "material"), ("medien.yaml", "medien")):
        for e in (lade_yaml(kurs.pfad / index, {}) or {}).get(schluessel) or []:
            if e.get("sha1"):
                ziele.setdefault(e["sha1"], []).append(e["datei"])
    return ziele


@dataclass
class Bericht:
    vorhanden: list[str] = field(default_factory=list)
    kopiert: list[str] = field(default_factory=list)    # bzw. „würde kopiert“ ohne --los
    unbekannt: list[str] = field(default_factory=list)  # neu/geändert → mit Agent einsortieren
    fehlen: list[str] = field(default_factory=list)     # im Index, aber weder vorhanden noch in den Quellen


def abgleich(kurs: Kurs, ordner: list[str], los: bool = False) -> Bericht:
    ziele = _ziele(kurs)
    bericht = Bericht()
    gesehen: set[str] = set()

    def treffer(sha: str, herkunft: str, schreiben) -> None:
        if sha not in ziele:
            bericht.unbekannt.append(herkunft)
            return
        for rel in ziele[sha]:
            gesehen.add(rel)
            ziel = kurs.pfad / rel
            if ziel.is_file():
                bericht.vorhanden.append(rel)
                continue
            if los:
                ziel.parent.mkdir(parents=True, exist_ok=True)
                schreiben(ziel)
            bericht.kopiert.append(rel)

    for o in ordner:
        basis = Path(o)
        dateien = [basis] if basis.is_file() else sorted(
            p for p in basis.rglob("*") if p.is_file() and not p.name.startswith("."))
        for p in dateien:
            herkunft = p.as_posix()
            if p.suffix.lower() in ARCHIVE and zipfile.is_zipfile(p):
                with zipfile.ZipFile(p) as z:
                    for info in z.infolist():
                        if info.is_dir():
                            continue
                        with z.open(info) as f:
                            sha = _sha1_strom(f)
                        if sha not in ziele and info.filename.lower().endswith((".xml", ".html", ".css")):
                            continue  # Verpackung des Archivs, kein Material
                        treffer(sha, f"{herkunft}!{info.filename}",
                                lambda ziel, z=z, info=info: ziel.write_bytes(z.read(info)))
                continue
            treffer(_sha1(p), herkunft, lambda ziel, p=p: shutil.copy2(p, ziel))

    alle = {rel for liste in ziele.values() for rel in liste}
    bericht.fehlen = sorted(rel for rel in alle - gesehen if not (kurs.pfad / rel).is_file())
    bericht.vorhanden = sorted(set(bericht.vorhanden))
    bericht.kopiert = sorted(set(bericht.kopiert))
    return bericht
