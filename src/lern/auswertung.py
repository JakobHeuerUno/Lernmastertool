"""Deterministische Auswertung: Mastery-Stufen, Nachrechen-Plan, Fortschritt, Empfehlungen.

Bewusst einfache, nachvollziehbare Regeln statt Black-Box: Das LLM diagnostiziert,
dieser Code zählt.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta

from lern.daten import Kurs, als_datum

STUFEN = {
    0: "neu",
    1: "gesehen",
    2: "mit Hilfe",
    3: "selbstständig",
    4: "klausurfest",
}
REDO_NACH_HILFE = 3      # Tage bis zum ersten selbstständigen Nachrechnen
REDO_ZWEITE_RUNDE = 10   # Tage bis zur Bestätigung
KLAUSURFEST_ABSTAND = 7  # Tage zwischen zwei selbstständigen Lösungen
ANKI_LAPSES_SCHWACH = 3
_RANG = {"falsch": 0, "erklaert": 1, "hinweise": 2, "selbst": 3}


@dataclass
class ThemaStand:
    id: str
    titel: str
    kapitel: str
    relevanz: int
    stufe: int = 0
    roh_stufe: int = 0
    letzte_aktivitaet: date | None = None
    letzter_erfolg: date | None = None
    offene_fehler: list[str] = field(default_factory=list)
    anki_schwach: int = 0
    auffrischen: bool = False
    gruende: list[str] = field(default_factory=list)


@dataclass
class AufgabeStand:
    id: str
    titel: str
    status: str            # offen | bearbeitet | selbst | gefestigt
    faellig: date | None   # Nachrechnen fällig am
    letztes_ergebnis: str | None = None


def _tag(e: dict) -> date:
    return als_datum(e["ts"])


def offene_fehler(ereignisse: list[dict]) -> dict[str, dict]:
    fehler = {e["id"]: e for e in ereignisse if e.get("typ") == "fehler"}
    for e in ereignisse:
        if e.get("typ") == "fehler_behoben":
            fehler.pop(e.get("id"), None)
    return fehler


def themen_stand(kurs: Kurs, heute: date | None = None, ereignisse: list[dict] | None = None) -> dict[str, ThemaStand]:
    heute = heute or date.today()
    ereignisse = kurs.ereignisse() if ereignisse is None else ereignisse
    auffrischen_nach = int((kurs.meta.get("einstellungen") or {}).get("auffrischen_nach_tagen", 21))

    staende: dict[str, ThemaStand] = {}
    for t in kurs.themen:
        if "id" not in t:
            continue
        staende[t["id"]] = ThemaStand(t["id"], t.get("titel", t["id"]), t.get("kapitel", ""),
                                      int(t.get("klausurrelevanz", 2) or 2))

    def stand(tid: str) -> ThemaStand:
        if tid not in staende:  # Thema noch nicht in themen.yaml → trotzdem mitzählen
            staende[tid] = ThemaStand(tid, tid, "(ohne Kapitel)", 2)
        return staende[tid]

    selbst_tage: dict[str, list[date]] = defaultdict(list)
    for e in ereignisse:
        if e.get("typ") != "versuch":
            continue
        tag, erg, art = _tag(e), e.get("ergebnis"), e.get("art", "aufgabe")
        for tid in e.get("themen", []):
            s = stand(tid)
            s.letzte_aktivitaet = max(filter(None, [s.letzte_aktivitaet, tag]))
            neu = 1
            if erg in ("hinweise", "selbst"):
                neu = 2
                s.letzter_erfolg = max(filter(None, [s.letzter_erfolg, tag]))
            if erg == "selbst" and art in ("aufgabe", "klausur"):
                neu = 3
                selbst_tage[tid].append(tag)
                if art == "klausur":
                    neu = 4
            if erg == "falsch" and s.roh_stufe >= 3:
                s.roh_stufe -= 1  # Rückschlag nach bereits gekonntem Thema
                s.gruende.append(f"falsch am {tag:%d.%m.}")
            s.roh_stufe = max(s.roh_stufe, neu)

    for tid, tage in selbst_tage.items():
        if len(tage) >= 2 and (max(tage) - min(tage)).days >= KLAUSURFEST_ABSTAND:
            staende[tid].roh_stufe = max(staende[tid].roh_stufe, 4)

    for fid, f in offene_fehler(ereignisse).items():
        for tid in f.get("themen", []):
            stand(tid).offene_fehler.append(fid)

    karten_themen = _karten_themen(kurs)
    for kid, st in kurs.anki_stats().items():
        tid = karten_themen.get(kid)
        if tid and int(st.get("lapses", 0)) >= ANKI_LAPSES_SCHWACH:
            stand(tid).anki_schwach += 1

    for s in staende.values():
        s.stufe = s.roh_stufe
        if s.offene_fehler and s.stufe > 2:
            s.stufe = 2
            s.gruende.append(f"offene Fehler: {', '.join(s.offene_fehler)}")
        if s.anki_schwach and s.stufe > 3:
            s.stufe = 3
            s.gruende.append(f"{s.anki_schwach} Anki-Karte(n) oft vergessen")
        if s.stufe >= 3 and s.letzter_erfolg and (heute - s.letzter_erfolg).days > auffrischen_nach:
            s.auffrischen = True
    return staende


def _karten_themen(kurs: Kurs) -> dict[str, str]:
    try:
        from lern.karten import lade_karten
        return {k.id: k.thema for k in lade_karten(kurs) if k.thema}
    except Exception:
        return {}


def aufgaben_stand(kurs: Kurs, heute: date | None = None, ereignisse: list[dict] | None = None) -> dict[str, AufgabeStand]:
    """Nachrechen-Plan: Wer Hilfe brauchte, rechnet nach 3 Tagen selbst nach, nach Erfolg nochmal nach 10 Tagen."""
    ereignisse = kurs.ereignisse() if ereignisse is None else ereignisse
    titel = {a["id"]: a.get("titel", a["id"]) for a in kurs.aufgaben if "id" in a}

    # pro Aufgabe und Tag das schlechteste Ergebnis (ein Tag = ein Durchgang)
    pro_tag: dict[str, dict[date, str]] = defaultdict(dict)
    for e in ereignisse:
        if e.get("typ") != "versuch" or not e.get("aufgabe"):
            continue
        aid, tag, erg = e["aufgabe"], _tag(e), e.get("ergebnis")
        bisher = pro_tag[aid].get(tag)
        if bisher is None or _RANG[erg] < _RANG[bisher]:
            pro_tag[aid][tag] = erg

    staende = {aid: AufgabeStand(aid, t, "offen", None) for aid, t in titel.items()}
    for aid, tage in pro_tag.items():
        brauchte_hilfe, serie, faellig, status = False, 0, None, "bearbeitet"
        for tag in sorted(tage):
            erg = tage[tag]
            if erg != "selbst":
                brauchte_hilfe, serie = True, 0
                faellig, status = tag + timedelta(days=REDO_NACH_HILFE), "bearbeitet"
            elif not brauchte_hilfe or serie >= 1:
                serie += 1
                faellig, status = None, ("gefestigt" if brauchte_hilfe else "selbst")
            else:
                serie = 1
                faellig, status = tag + timedelta(days=REDO_ZWEITE_RUNDE), "selbst"
        letzte = tage[max(tage)]
        staende[aid] = AufgabeStand(aid, titel.get(aid, aid), status, faellig, letzte)
    return staende


@dataclass
class Fortschritt:
    themen_gesamt: int
    abdeckung: float          # gewichteter Anteil Themen mit Stufe >= 1
    beherrschung: float       # gewichtete Ø-Stufe / 4
    stufen_verteilung: dict[int, int]
    aufgaben_gesamt: int
    aufgaben_bearbeitet: int
    aufgaben_selbst: int
    fehler_offen: int
    fehler_behoben: int
    fehlertypen: dict[str, int]
    fragen: int
    sitzungen: int
    lerntage: list[date]
    kalibrierung: dict[str, int]  # sicher_falsch, sicher_gesamt
    klausur_datum: date | None
    tage_bis_klausur: int | None
    prognose: str | None


def fortschritt(kurs: Kurs, heute: date | None = None) -> Fortschritt:
    heute = heute or date.today()
    ereignisse = kurs.ereignisse()
    themen = themen_stand(kurs, heute, ereignisse)
    aufgaben = aufgaben_stand(kurs, heute, ereignisse)

    gewicht = sum(t.relevanz for t in themen.values()) or 1
    abdeckung = sum(t.relevanz for t in themen.values() if t.stufe >= 1) / gewicht
    beherrschung = sum(t.relevanz * t.stufe / 4 for t in themen.values()) / gewicht

    fehler_alle = [e for e in ereignisse if e.get("typ") == "fehler"]
    offen = offene_fehler(ereignisse)
    sicher = [e for e in ereignisse if e.get("typ") == "versuch" and e.get("ergebnis") != "erklaert"
              and int(e.get("konfidenz", 0) or 0) >= 4]

    klausur = als_datum((kurs.meta.get("klausur") or {}).get("datum"))
    tage = (klausur - heute).days if klausur else None

    return Fortschritt(
        themen_gesamt=len(themen),
        abdeckung=abdeckung if themen else 0.0,
        beherrschung=beherrschung if themen else 0.0,
        stufen_verteilung=dict(Counter(t.stufe for t in themen.values())),
        aufgaben_gesamt=len(aufgaben),
        aufgaben_bearbeitet=sum(1 for a in aufgaben.values() if a.status != "offen"),
        aufgaben_selbst=sum(1 for a in aufgaben.values() if a.status in ("selbst", "gefestigt")),
        fehler_offen=len(offen),
        fehler_behoben=len(fehler_alle) - len(offen),
        fehlertypen=dict(Counter(e.get("fehlertyp", "sonstiges") for e in fehler_alle)),
        fragen=sum(1 for e in ereignisse if e.get("typ") == "frage"),
        sitzungen=sum(1 for e in ereignisse if e.get("typ") == "sitzung"),
        lerntage=sorted({_tag(e) for e in ereignisse}),
        kalibrierung={"sicher_gesamt": len(sicher),
                      "sicher_falsch": sum(1 for e in sicher if e.get("ergebnis") == "falsch")},
        klausur_datum=klausur,
        tage_bis_klausur=tage,
        prognose=_prognose(themen, ereignisse, heute, tage),
    )


def _prognose(themen: dict[str, ThemaStand], ereignisse: list[dict], heute: date, tage: int | None) -> str | None:
    if not tage or tage <= 0 or not themen:
        return None
    rest = sum(1 for t in themen.values() if t.stufe < 3)
    if rest == 0:
        return "Alle Themen mindestens selbstständig – jetzt festigen (Klausursimulation)."
    seit = heute - timedelta(days=14)
    neu_selbst = {tid for e in ereignisse if e.get("typ") == "versuch" and e.get("ergebnis") == "selbst"
                  and _tag(e) >= seit for tid in e.get("themen", [])}
    tempo = len(neu_selbst) / 2  # Themen pro Woche
    noetig = rest / (tage / 7)
    if tempo == 0:
        return f"{rest} Themen fehlen noch bis „selbstständig“; nötig ≈ {noetig:.1f} Themen/Woche."
    status = "im Plan" if tempo >= noetig else "zu langsam"
    return f"Tempo ≈ {tempo:.1f} Themen/Woche, nötig ≈ {noetig:.1f} → {status} ({rest} Themen offen)."


@dataclass
class Empfehlung:
    art: str
    text: str
    prio: int


def empfehlungen(kurs: Kurs, heute: date | None = None, anzahl: int = 6) -> list[Empfehlung]:
    heute = heute or date.today()
    ereignisse = kurs.ereignisse()
    themen = themen_stand(kurs, heute, ereignisse)
    aufgaben = aufgaben_stand(kurs, heute, ereignisse)
    liste: list[Empfehlung] = []

    for a in sorted(aufgaben.values(), key=lambda a: a.faellig or date.max):
        if a.faellig and a.faellig <= heute:
            liste.append(Empfehlung("nachrechnen", f"Aufgabe {a.id} ({a.titel}) ohne Hilfe nachrechnen – fällig seit {a.faellig:%d.%m.}", 1))

    for fid, f in sorted(offene_fehler(ereignisse).items()):
        if (heute - _tag(f)).days >= 1:
            liste.append(Empfehlung("recheck", f"{fid} überprüfen ({', '.join(f.get('themen', [])) or '–'}): {f.get('kurz', '')}", 2))

    for t in themen.values():
        if t.auffrischen:
            liste.append(Empfehlung("auffrischen", f"Thema {t.titel} auffrischen (zuletzt sicher am {t.letzter_erfolg:%d.%m.})", 3))

    reihenfolge = [t["id"] for t in kurs.themen if "id" in t]

    def voraussetzungen_ok(tid: str) -> bool:
        info = kurs.themen_index().get(tid, {})
        return all(themen.get(v) is None or themen[v].stufe >= 2 for v in info.get("voraussetzungen") or [])

    schwach = sorted((themen[tid] for tid in reihenfolge if tid in themen and 1 <= themen[tid].stufe <= 2
                      and voraussetzungen_ok(tid)), key=lambda t: (t.stufe, -t.relevanz))
    for t in schwach[:2]:
        liste.append(Empfehlung("ueben", f"Thema {t.titel} (Stufe {t.stufe} „{STUFEN[t.stufe]}“) mit einer Aufgabe festigen", 4))

    for tid in reihenfolge:
        if themen[tid].stufe == 0 and voraussetzungen_ok(tid):
            liste.append(Empfehlung("neu", f"Neues Thema: {themen[tid].titel}", 5))
            break

    if not liste and not kurs.themen:
        liste.append(Empfehlung("einrichten", "Kurs einrichten: Material in inbox/ legen und Skill `kurs-einrichten` nutzen", 0))
    return sorted(liste, key=lambda e: e.prio)[:anzahl]
