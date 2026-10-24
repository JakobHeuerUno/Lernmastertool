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

    # Felder der Notiztypen nie ändern: Schema-Änderungen erzwingen in Anki eine vollständige
    # Synchronisation (Gefahr, Handy-Fortschritt zu überschreiben). Neue Infos → Feld „Zusatz“.
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
    zeit = 180 if aktion in ("sync", "importPackage") else 10  # AnkiWeb-Sync kann dauern
    try:
        with urllib.request.urlopen(urllib.request.Request(url, anfrage), timeout=zeit) as antwort:
            daten = json.loads(antwort.read().decode("utf-8"))
    except OSError as e:
        raise LernFehler("AnkiConnect nicht erreichbar – läuft Anki-Desktop mit dem Add-on AnkiConnect "
                         "(Code 2055492159)? Alternativ `lern anki export` nutzen.") from e
    if daten.get("error"):
        raise LernFehler(f"AnkiConnect-Fehler bei {aktion}: {daten['error']}")
    return daten.get("result")


def karten_hash(kurs: Kurs) -> str | None:
    """Fingerabdruck aller Karteninhalte – Push nur, wenn sich daran etwas geändert hat."""
    karten = _gueltige_karten(kurs)
    if not karten:
        return None
    inhalt = sorted((k.id, deck_name(kurs, k), json.dumps(_felder(k), sort_keys=True)) for k in karten)
    return hashlib.sha1(json.dumps(inhalt, ensure_ascii=False).encode("utf-8")).hexdigest()


def push(kurs: Kurs, rufe=ankiconnect) -> int:
    """Karten per AnkiConnect übertragen – als .apkg-Import, damit GUIDs mit `anki export` identisch sind
    (kein Duplikat, egal welcher Weg; bestehende Karten behalten ihre Lernhistorie)."""
    ziel, n = exportiere_apkg(kurs)
    rufe("importPackage", path=str(ziel.resolve()))
    zustand = lade_sync_zustand(kurs)
    zustand.update(karten_hash=karten_hash(kurs), letzter_push=_jetzt())
    _speichere_sync_zustand(kurs, zustand)
    return n


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


# ---------------------------------------------------------------- Sync-Workflow

SYNC_DATEI = "anki-sync.json"


class AnkiNichtErreichbar(LernFehler):
    pass


def _jetzt() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def lade_sync_zustand(kurs: Kurs) -> dict:
    datei = kurs.lernstand / SYNC_DATEI
    return json.loads(datei.read_text(encoding="utf-8")) if datei.is_file() else {}


def _speichere_sync_zustand(kurs: Kurs, zustand: dict) -> None:
    datei = kurs.lernstand / SYNC_DATEI
    datei.parent.mkdir(parents=True, exist_ok=True)
    datei.write_text(json.dumps(zustand, ensure_ascii=False, indent=1), encoding="utf-8")


def _ankiweb_sync(rufe) -> bool:
    """True = synchronisiert, False = kein AnkiWeb-Login (nur lokal). Andere Fehler → Abbruch."""
    try:
        rufe("sync")
        return True
    except LernFehler as e:
        text = str(e).lower()
        if "auth" in text or "login" in text:
            return False
        raise LernFehler(f"AnkiWeb-Sync fehlgeschlagen – es wurde nichts übertragen. ({e})\n"
                         "Meist ist eine vollständige Synchronisation nötig: siehe Skill `anki`, Abschnitt Probleme.") from e


def synchronisiere(kurs: Kurs, rufe=None, mit_push: bool = True) -> list[str]:
    """Sicherer Abgleich in fester Reihenfolge:
    1. AnkiWeb → Desktop (Handy-Wiederholungen holen, bevor irgendetwas geändert wird)
    2. Statistik ziehen  3. geänderte Karten importieren  4. Desktop → AnkiWeb (fürs Handy)."""
    rufe = rufe or ankiconnect
    try:
        rufe("version")
    except LernFehler as e:
        raise AnkiNichtErreichbar(str(e)) from e
    protokoll = []
    web = _ankiweb_sync(rufe)
    protokoll.append("AnkiWeb → Desktop synchronisiert" if web else
                     "WARNUNG: kein AnkiWeb-Login in Anki-Desktop – Handy-Fortschritt fehlt, nur lokaler Abgleich")
    in_anki = pull(kurs, rufe)
    protokoll.append(f"Statistik für {in_anki} Karten geholt")
    zustand = lade_sync_zustand(kurs)
    h = karten_hash(kurs)
    fehlen = len(_gueltige_karten(kurs)) - in_anki  # z. B. nach „Herunterladen“ bei vollständiger Synchronisation
    if not mit_push:
        protokoll.append("Push übersprungen (--ohne-push)")
    elif h is None:
        protokoll.append("Keine Karten im Kurs – nichts zu übertragen")
    elif h == zustand.get("karten_hash") and fehlen <= 0:
        protokoll.append("Karten unverändert – kein Push nötig")
    else:
        protokoll.append(f"{push(kurs, rufe)} Karten importiert (neu/aktualisiert)")
        if web:
            _ankiweb_sync(rufe)
            protokoll.append("Desktop → AnkiWeb hochgeladen (Handy jetzt synchronisieren)")
    zustand = lade_sync_zustand(kurs)
    zustand["letzter_abgleich"] = _jetzt()
    if web:
        zustand["letzter_ankiweb_sync"] = zustand["letzter_abgleich"]
    _speichere_sync_zustand(kurs, zustand)
    return protokoll
