"""Material einsortieren, PDFs nach Markdown (mit Seitenmarkern) wandeln, material.yaml pflegen."""

from __future__ import annotations

import hashlib
import shutil
from datetime import date
from pathlib import Path

from lern.daten import MATERIALTYPEN, Kurs, LernFehler, lade_yaml, speichere_yaml

TEXT_ENDUNGEN = {".md", ".txt"}
PDF = ".pdf"


def _sha1(pfad: Path) -> str:
    h = hashlib.sha1()
    with pfad.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def inbox_dateien(kurs: Kurs) -> list[Path]:
    inbox = kurs.pfad / "inbox"
    if not inbox.is_dir():
        return []
    return sorted(p for p in inbox.rglob("*") if p.is_file() and not p.name.startswith("."))


def einsortieren(kurs: Kurs, dateien: list[str], typ: str, vertrauen: str | None = None) -> list[Path]:
    if typ not in MATERIALTYPEN:
        raise LernFehler(f"typ muss eines von {MATERIALTYPEN} sein")
    ziel_dir = kurs.pfad / "material" / typ
    ziel_dir.mkdir(parents=True, exist_ok=True)
    verschoben = []
    for d in dateien:
        quelle = Path(d)
        if not quelle.is_absolute() and not quelle.exists():
            quelle = kurs.pfad / "inbox" / d
        if not quelle.is_file():
            raise LernFehler(f"Datei nicht gefunden: {d}")
        ziel = ziel_dir / quelle.name
        if ziel.exists():
            raise LernFehler(f"Existiert bereits: {ziel.relative_to(kurs.pfad)}")
        shutil.move(str(quelle), ziel)
        verschoben.append(ziel)
    if vertrauen:
        index = _lade_index(kurs)
        for z in verschoben:
            index.setdefault(_rel(kurs, z), {})["vertrauen"] = vertrauen
        _speichere_index(kurs, index)
    return verschoben


def _rel(kurs: Kurs, pfad: Path) -> str:
    return pfad.relative_to(kurs.pfad).as_posix()


def _lade_index(kurs: Kurs) -> dict[str, dict]:
    daten = lade_yaml(kurs.pfad / "material.yaml", {}) or {}
    return {m["datei"]: m for m in daten.get("material") or [] if "datei" in m}


def _speichere_index(kurs: Kurs, index: dict[str, dict]) -> None:
    eintraege = []
    for datei in sorted(index):
        m = {"datei": datei, **{k: v for k, v in index[datei].items() if k != "datei"}}
        eintraege.append(m)
    speichere_yaml(kurs.pfad / "material.yaml", {"material": eintraege})


def pdf_zu_markdown(pdf: Path) -> tuple[str, int, str]:
    """Gibt (markdown, seitenzahl, methode) zurück. Jede Seite beginnt mit <!-- seite N -->."""
    import pymupdf

    with pymupdf.open(pdf) as doc:
        seiten = doc.page_count
    teile: list[str] = []
    methode = "pymupdf4llm"
    try:
        import contextlib
        import io

        import pymupdf4llm
        pymupdf.set_messages(stream=io.StringIO())  # Parser-Hinweise (z. B. fehlendes OCR) nicht in die CLI-Ausgabe
        with contextlib.redirect_stdout(io.StringIO()):
            chunks = pymupdf4llm.to_markdown(str(pdf), page_chunks=True, show_progress=False)
        for i, chunk in enumerate(chunks, 1):
            nr = (chunk.get("metadata") or {}).get("page_number") or (chunk.get("metadata") or {}).get("page") or i
            teile.append(f"<!-- seite {nr} -->\n{chunk.get('text', '').strip()}\n")
    except Exception:
        methode = "pymupdf-text"
        teile = []
        with pymupdf.open(pdf) as doc:
            for i, seite in enumerate(doc, 1):
                teile.append(f"<!-- seite {i} -->\n{seite.get_text().strip()}\n")
    return "\n".join(teile), seiten, methode


def einlesen(kurs: Kurs, neu_erzwingen: bool = False) -> dict[str, list[str]]:
    """Indexiert alles unter material/ und wandelt neue/geänderte PDFs um."""
    index = _lade_index(kurs)
    bericht: dict[str, list[str]] = {"neu": [], "geaendert": [], "unveraendert": [], "nur_index": [], "entfernt": []}
    material = kurs.pfad / "material"
    gefunden = set()
    for datei in sorted(p for p in material.rglob("*") if p.is_file() and not p.name.startswith(".")):
        rel = _rel(kurs, datei)
        gefunden.add(rel)
        typ = datei.relative_to(material).parts[0] if len(datei.relative_to(material).parts) > 1 else "sonstiges"
        eintrag = index.get(rel, {})
        sha = _sha1(datei)
        if eintrag.get("sha1") == sha and not neu_erzwingen and eintrag.get("text") is not None:
            bericht["unveraendert"].append(rel)
            continue
        status = "geaendert" if eintrag.get("sha1") else "neu"
        eintrag.setdefault("typ", typ if typ in MATERIALTYPEN else "sonstiges")
        eintrag.setdefault("vertrauen", "inoffiziell" if typ == "studydrive" else "offiziell")
        eintrag.setdefault("themen", [])
        eintrag["sha1"] = sha
        eintrag["eingelesen"] = date.today().isoformat()
        endung = datei.suffix.lower()
        text_ziel = kurs.pfad / "text" / Path(rel).relative_to("material").with_suffix(".md")
        if endung == PDF:
            md, seiten, methode = pdf_zu_markdown(datei)
            text_ziel.parent.mkdir(parents=True, exist_ok=True)
            kopf = f"<!-- quelle: {rel} · {seiten} Seiten · {methode} -->\n\n"
            text_ziel.write_text(kopf + md, encoding="utf-8", newline="\n")
            eintrag.update(seiten=seiten, text=_rel(kurs, text_ziel))
        elif endung in TEXT_ENDUNGEN:
            text_ziel.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(datei, text_ziel)
            eintrag["text"] = _rel(kurs, text_ziel)
        else:
            eintrag["text"] = ""  # Bilder, pptx, … → Agent sieht sich die Datei direkt an
            status = "nur_index"
        index[rel] = eintrag
        bericht[status].append(rel)
    for rel in list(index):
        if rel not in gefunden:
            bericht["entfernt"].append(rel)
            del index[rel]
    _speichere_index(kurs, index)
    return bericht


def seite_rendern(kurs: Kurs, datei: str, seite: int, zoom: float = 2.0) -> Path:
    import pymupdf

    pfad = Path(datei)
    if not pfad.is_file():
        pfad = kurs.pfad / datei
    if not pfad.is_file():
        treffer = list((kurs.pfad / "material").rglob(Path(datei).name))
        if not treffer:
            raise LernFehler(f"Datei nicht gefunden: {datei}")
        pfad = treffer[0]
    with pymupdf.open(pfad) as doc:
        if not 1 <= seite <= doc.page_count:
            raise LernFehler(f"Seite {seite} existiert nicht (1–{doc.page_count})")
        pix = doc[seite - 1].get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
        ziel = kurs.repo.wurzel / ".cache" / "seiten" / kurs.id / f"{pfad.stem}-s{seite}.png"
        ziel.parent.mkdir(parents=True, exist_ok=True)
        pix.save(str(ziel))
    return ziel
