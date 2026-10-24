"""Anki-Anbindung: .apkg-Export (genanki) und optional AnkiConnect (Push + Statistik-Pull)."""

from __future__ import annotations

import hashlib
import html
import json
import re
import urllib.request
from datetime import datetime
from pathlib import Path

from lern.daten import Kurs, LernFehler
from lern.karten import Karte, lade_karten

MODELL_BASIS = "Lernecke Basis"
MODELL_CLOZE = "Lernecke Lückentext"
ANKICONNECT_URL = "http://127.0.0.1:8765"

_CSS = """.card { font-family: Segoe UI, Arial, sans-serif; font-size: 20px; text-align: left; color: #1d1d1f; background: #fff; }
.nightMode.card, .night_mode .card { color: #e8e8ea; background: #1e1e20; }
.quelle, .thema { font-size: 13px; opacity: .6; margin-top: 14px; }
.zusatz { font-size: 16px; margin-top: 12px; padding-top: 8px; border-top: 1px solid #8884; }
.cloze { font-weight: bold; color: #2f6fdb; }"""

_FUSS = '{{#Zusatz}}<div class="zusatz">{{Zusatz}}</div>{{/Zusatz}}<div class="quelle">{{Quelle}}</div>'


def _stabile_zahl(text: str) -> int:
    return int(hashlib.sha1(text.encode("utf-8")).hexdigest()[:8], 16) | (1 << 30)


def zu_anki_html(text: str) -> str:
    """Markdown-light → Anki-HTML. $$…$$ → \\[…\\], $…$ → \\(…\\) (MathJax)."""
    t = html.escape(text, quote=False)
    t = re.sub(r"\$\$(.+?)\$\$", r"\\[\1\\]", t, flags=re.S)
    t = re.sub(r"(?<![\\$])\$(?!\s)(.+?)(?<!\s)\$", r"\\(\1\\)", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    return t.replace("\n", "<br>")


def _kapitel(kurs: Kurs, karte: Karte) -> str:
    info = kurs.themen_index().get(karte.thema, {})
    return info.get("kapitel") or "Allgemein"


def deck_name(kurs: Kurs, karte: Karte) -> str:
    kap = re.sub(r"::+", ":", _kapitel(kurs, karte))
    return f"Lernecke::{kurs.name}::{kap}"


def _felder(karte: Karte) -> dict[str, str]:
    basis = {"ID": karte.id, "Quelle": html.escape(karte.quelle), "Thema": html.escape(karte.thema),
             "Zusatz": zu_anki_html(karte.zusatz)}
    if karte.ist_cloze:
        return {"Text": zu_anki_html(karte.cloze), **basis}
    return {"Vorderseite": zu_anki_html(karte.frage), "Rückseite": zu_anki_html(karte.antwort), **basis}


def _gueltige_karten(kurs: Kurs) -> list[Karte]:
    karten = lade_karten(kurs)
    ids = [k.id for k in karten]
    doppelt = {i for i in ids if ids.count(i) > 1}
    if doppelt:
        raise LernFehler(f"Doppelte Karten-IDs: {', '.join(sorted(doppelt))}")
    return [k for k in karten if not k.probleme]


# ---------------------------------------------------------------- .apkg-Export

def exportiere_apkg(kurs: Kurs, ziel: Path | None = None) -> tuple[Path, int]:
    import genanki

    basis = genanki.Model(
        _stabile_zahl(MODELL_BASIS), MODELL_BASIS,
        fields=[{"name": n} for n in ("Vorderseite", "Rückseite", "ID", "Quelle", "Thema", "Zusatz")],
        templates=[{"name": "Karte",
                    "qfmt": "{{Vorderseite}}",
                    "afmt": "{{FrontSide}}<hr id=answer>{{Rückseite}}" + _FUSS}],
        css=_CSS, sort_field_index=2)
    cloze = genanki.Model(
        _stabile_zahl(MODELL_CLOZE), MODELL_CLOZE,
        fields=[{"name": n} for n in ("Text", "ID", "Quelle", "Thema", "Zusatz")],
        templates=[{"name": "Lückentext", "qfmt": "{{cloze:Text}}", "afmt": "{{cloze:Text}}" + _FUSS}],
        css=_CSS, model_type=genanki.Model.CLOZE)

    decks: dict[str, genanki.Deck] = {}
    karten = _gueltige_karten(kurs)
    for k in karten:
        name = deck_name(kurs, k)
        deck = decks.setdefault(name, genanki.Deck(_stabile_zahl(name), name))
        felder = _felder(k)
        modell = cloze if k.ist_cloze else basis
        deck.add_note(genanki.Note(model=modell, fields=[felder[f["name"]] for f in modell.fields],
                                   guid=genanki.guid_for(k.id), tags=[f"lernecke::{kurs.id}", f"thema::{k.thema or 'ohne'}"]))
    if not karten:
        raise LernFehler("Keine (gültigen) Karten in karten/*.md gefunden")
    ziel = ziel or kurs.repo.wurzel / "ausgabe" / f"{kurs.id}.apkg"
    ziel.parent.mkdir(parents=True, exist_ok=True)
    genanki.Package(list(decks.values())).write_to_file(str(ziel))
    return ziel, len(karten)


# ---------------------------------------------------------------- AnkiConnect

def ankiconnect(aktion: str, url: str = ANKICONNECT_URL, **params):
    anfrage = json.dumps({"action": aktion, "version": 6, "params": params}).encode("utf-8")
    try:
        with urllib.request.urlopen(urllib.request.Request(url, anfrage), timeout=10) as antwort:
            daten = json.loads(antwort.read().decode("utf-8"))
    except OSError as e:
        raise LernFehler("AnkiConnect nicht erreichbar – läuft Anki-Desktop mit dem Add-on AnkiConnect "
                         "(Code 2055492159)? Alternativ `lern anki export` nutzen.") from e
    if daten.get("error"):
        raise LernFehler(f"AnkiConnect-Fehler bei {aktion}: {daten['error']}")
    return daten.get("result")


def _modelle_sicherstellen(rufe) -> None:
    vorhanden = set(rufe("modelNames"))
    if MODELL_BASIS not in vorhanden:
        rufe("createModel", modelName=MODELL_BASIS, css=_CSS,
             inOrderFields=["Vorderseite", "Rückseite", "ID", "Quelle", "Thema", "Zusatz"],
             cardTemplates=[{"Name": "Karte", "Front": "{{Vorderseite}}",
                             "Back": "{{FrontSide}}<hr id=answer>{{Rückseite}}" + _FUSS}])
    if MODELL_CLOZE not in vorhanden:
        rufe("createModel", modelName=MODELL_CLOZE, css=_CSS, isCloze=True,
             inOrderFields=["Text", "ID", "Quelle", "Thema", "Zusatz"],
             cardTemplates=[{"Name": "Lückentext", "Front": "{{cloze:Text}}", "Back": "{{cloze:Text}}" + _FUSS}])


def push(kurs: Kurs, rufe=ankiconnect) -> dict[str, int]:
    _modelle_sicherstellen(rufe)
    neu = aktualisiert = 0
    for k in _gueltige_karten(kurs):
        deck = deck_name(kurs, k)
        rufe("createDeck", deck=deck)
        modell = MODELL_CLOZE if k.ist_cloze else MODELL_BASIS
        felder = _felder(k)
        treffer = rufe("findNotes", query=f'"note:{modell}" "ID:{k.id}"')
        if treffer:
            rufe("updateNoteFields", note={"id": treffer[0], "fields": felder})
            aktualisiert += 1
        else:
            rufe("addNote", note={"deckName": deck, "modelName": modell, "fields": felder,
                                  "tags": [f"lernecke::{kurs.id}", f"thema::{k.thema or 'ohne'}"],
                                  "options": {"allowDuplicate": False}})
            neu += 1
    return {"neu": neu, "aktualisiert": aktualisiert}


def pull(kurs: Kurs, rufe=ankiconnect) -> int:
    karten_ids = rufe("findCards", query=f'"tag:lernecke::{kurs.id}"')
    stats: dict[str, dict] = {}
    if karten_ids:
        for info in rufe("cardsInfo", cards=karten_ids):
            kid = (info.get("fields", {}).get("ID") or {}).get("value")
            if not kid:
                continue
            alt = stats.get(kid, {"lapses": 0, "reps": 0, "interval": 0})
            stats[kid] = {  # bei Lückentext mehrere Karten pro Notiz → zusammenfassen
                "lapses": alt["lapses"] + int(info.get("lapses", 0)),
                "reps": alt["reps"] + int(info.get("reps", 0)),
                "interval": max(alt["interval"], int(info.get("interval", 0))),
            }
    datei = kurs.lernstand / "anki-stats.json"
    datei.parent.mkdir(parents=True, exist_ok=True)
    datei.write_text(json.dumps({"stand": datetime.now().replace(microsecond=0).isoformat(), "karten": stats},
                                ensure_ascii=False, indent=1), encoding="utf-8")
    return len(stats)
