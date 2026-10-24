"""Schreiben in den Lernstand: Versuche, Fehler, Fragen, Sitzungen."""

from __future__ import annotations

import re
from datetime import date

from lern.daten import ARTEN, ERGEBNISSE, FEHLERTYPEN, Kurs, LernFehler

KOPF_FEHLERBUCH = "# Fehlerbuch\n\nJeder Eintrag: was schiefging, warum, und wie man es richtig macht. Kopfzeile wird von `lern` gepflegt.\n"
KOPF_FRAGEN = "# Nachfragen\n\nFragen zu Erklärungen und was beim Verstehen geholfen hat.\n"


def _liste(wert) -> list[str]:
    if not wert:
        return []
    if isinstance(wert, str):
        wert = wert.split(",")
    return [w.strip() for w in wert if w and w.strip()]


def _pruefe_themen(kurs: Kurs, themen: list[str]) -> list[str]:
    """Gibt Warnungen für unbekannte Themen-IDs zurück (kein Abbruch, Themenkarte kann noch wachsen)."""
    bekannt = kurs.themen_index()
    if not bekannt:
        return []
    return [f"Warnung: Thema '{t}' steht nicht in themen.yaml" for t in themen if t not in bekannt]


def _naechste_id(kurs: Kurs, typ: str, praefix: str) -> str:
    hoechste = 0
    for e in kurs.ereignisse():
        if e.get("typ") == typ and str(e.get("id", "")).startswith(praefix):
            try:
                hoechste = max(hoechste, int(e["id"].split("-")[1]))
            except (IndexError, ValueError):
                pass
    return f"{praefix}{hoechste + 1:03d}"


def _anhaengen(pfad, kopf: str, text: str) -> None:
    pfad.parent.mkdir(parents=True, exist_ok=True)
    if not pfad.is_file():
        pfad.write_text(kopf, encoding="utf-8", newline="\n")
    with pfad.open("a", encoding="utf-8", newline="\n") as f:
        f.write("\n" + text)


def log_versuch(kurs: Kurs, themen, ergebnis: str, aufgabe: str | None = None, teil: str | None = None,
                art: str = "aufgabe", konfidenz: int | None = None, notiz: str | None = None) -> tuple[dict, list[str]]:
    themen = _liste(themen)
    if ergebnis not in ERGEBNISSE:
        raise LernFehler(f"ergebnis muss eines von {ERGEBNISSE} sein")
    if art not in ARTEN:
        raise LernFehler(f"art muss eines von {ARTEN} sein")
    if not themen and not aufgabe:
        raise LernFehler("Mindestens --thema oder --aufgabe angeben")
    if konfidenz is not None and not 1 <= konfidenz <= 5:
        raise LernFehler("konfidenz muss 1–5 sein")
    if aufgabe and not themen:
        themen = next((_liste(a.get("themen")) for a in kurs.aufgaben if a.get("id") == aufgabe), [])
    ereignis = kurs.schreibe_ereignis({
        "typ": "versuch", "art": art, "themen": themen, "aufgabe": aufgabe, "teil": teil,
        "ergebnis": ergebnis, "konfidenz": konfidenz, "notiz": notiz,
    })
    return ereignis, _pruefe_themen(kurs, themen)


def log_fehler(kurs: Kurs, themen, fehlertyp: str, kurz: str, aufgabe: str | None = None,
               teil: str | None = None) -> tuple[dict, list[str]]:
    themen = _liste(themen)
    if fehlertyp not in FEHLERTYPEN:
        raise LernFehler(f"typ muss eines von {FEHLERTYPEN} sein")
    fid = _naechste_id(kurs, "fehler", "F-")
    ereignis = kurs.schreibe_ereignis({
        "typ": "fehler", "id": fid, "themen": themen, "fehlertyp": fehlertyp,
        "aufgabe": aufgabe, "teil": teil, "kurz": kurz,
    })
    heute = date.today().isoformat()
    aufgabe_txt = f"{aufgabe}{' ' + teil if teil else ''}" if aufgabe else "–"
    _anhaengen(kurs.lernstand / "fehlerbuch.md", KOPF_FEHLERBUCH,
               f"## {fid} · {heute} · thema: {', '.join(themen) or '–'} · typ: {fehlertyp} · status: offen\n"
               f"- **Aufgabe:** {aufgabe_txt}\n"
               f"- **Was passiert ist:** {kurz}\n"
               f"- **Ursache:** _(ergänzen)_\n"
               f"- **Richtig ist:** _(ergänzen)_\n")
    return ereignis, _pruefe_themen(kurs, themen)


def fehler_behoben(kurs: Kurs, fid: str, notiz: str | None = None) -> dict:
    offen = {e["id"] for e in kurs.ereignisse() if e.get("typ") == "fehler"}
    if fid not in offen:
        raise LernFehler(f"Fehler {fid} existiert nicht")
    ereignis = kurs.schreibe_ereignis({"typ": "fehler_behoben", "id": fid, "notiz": notiz})
    datei = kurs.lernstand / "fehlerbuch.md"
    if datei.is_file():
        text = datei.read_text(encoding="utf-8")
        neu = re.sub(rf"^(## {re.escape(fid)} · .*?)status: offen\s*$",
                     rf"\1status: behoben ({date.today().isoformat()})", text, flags=re.M)
        datei.write_text(neu, encoding="utf-8", newline="\n")
    return ereignis


def log_frage(kurs: Kurs, themen, frage: str, hilfreich: str | None = None) -> tuple[dict, list[str]]:
    themen = _liste(themen)
    qid = _naechste_id(kurs, "frage", "Q-")
    ereignis = kurs.schreibe_ereignis({
        "typ": "frage", "id": qid, "themen": themen, "kurz": frage, "hilfreich": hilfreich,
    })
    _anhaengen(kurs.lernstand / "fragen.md", KOPF_FRAGEN,
               f"## {qid} · {date.today().isoformat()} · thema: {', '.join(themen) or '–'}\n"
               f"- **Frage:** {frage}\n"
               f"- **Was geholfen hat:** {hilfreich or '_(ergänzen)_'}\n")
    return ereignis, _pruefe_themen(kurs, themen)


def log_sitzung(kurs: Kurs, zusammenfassung: str, naechste: list[str], dauer_min: int | None = None,
                datei: str | None = None) -> dict:
    return kurs.schreibe_ereignis({
        "typ": "sitzung", "kurz": zusammenfassung, "naechste_schritte": naechste,
        "dauer_min": dauer_min, "datei": datei,
    })
