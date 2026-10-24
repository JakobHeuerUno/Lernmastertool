"""Fremde Anki-Stapel (z. B. von Kommilitonen, StudyDrive): erkennen, übernehmen, Statistik, Bearbeitung durch den Agenten.

Übernommene Stapel werden als `kurse/<kurs>/karten-fremd/<slug>.yaml` gespiegelt. Der Agent bearbeitet dort Felder und
ordnet Themen zu; `lern anki sync` gleicht in beide Richtungen ab (3-Wege-Vergleich gegen den letzten gemeinsamen Stand),
die Notizen bleiben dieselben → Lernhistorie bleibt erhalten.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
from datetime import date
from pathlib import Path

import yaml

from lern.daten import Kurs, LernFehler, lade_yaml, speichere_yaml

REGISTER = "anki-fremd.yaml"
ORDNER = "karten-fremd"
BASIS = "anki-fremd-basis.json"
EIGENER_STAPEL = "Lernecke"

_KOPF = ("# Fremder Anki-Stapel – vom Agenten bearbeitbar (siehe Skill `anki`, Abschnitt „Fremde Stapel“).\n"
         "# Erlaubt: Werte unter `felder` ändern, `thema` setzen, `notiz` ergänzen. Nicht ändern: id, modell, Feldnamen.\n"
         "# Danach `lern anki sync` – Änderungen gehen an dieselbe Anki-Notiz, die Lernhistorie bleibt.\n")


def _q(name: str) -> str:
    """Anki-Suche nach Stapel inkl. Unterstapeln; Sonderzeichen escapen."""
    return '"deck:' + re.sub(r'([\\"*_])', r"\\\1", name) + '"'


def _slug(name: str) -> str:
    s = name.lower().translate(str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}))
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:60] or "stapel"


def _hash(felder: dict) -> str:
    return hashlib.sha1(json.dumps(felder, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def kurztext(felder: dict, n: int = 50) -> str:
    erstes = next(iter(felder.values()), "") if felder else ""
    text = html.unescape(re.sub(r"<[^>]+>", " ", str(erstes)))
    text = re.sub(r"\s+", " ", text).strip()
    return text[:n] + ("…" if len(text) > n else "")


# ---------------------------------------------------------------- Register

def lade_register(kurs: Kurs) -> dict:
    daten = lade_yaml(kurs.pfad / REGISTER, {}) or {}
    daten.setdefault("stapel", [])
    daten.setdefault("ignoriert", [])
    return daten


def _speichere_register(kurs: Kurs, daten: dict) -> None:
    speichere_yaml(kurs.pfad / REGISTER, daten)


def _bekannte_namen(kurs: Kurs) -> set[str]:
    """Registrierte oder ignorierte Stapel aller Kurse (ein Stapel gehört genau zu einem Kurs)."""
    namen = {EIGENER_STAPEL}
    for kid in kurs.repo.kurs_ids():
        reg = lade_register(kurs.repo.kurs(kid))
        namen |= {s["name"] for s in reg["stapel"]} | set(reg["ignoriert"])
    return namen


def erkenne(kurs: Kurs, rufe) -> list[dict]:
    """Neue, nicht leere Hauptstapel in Anki, die noch keinem Kurs zugeordnet sind."""
    bekannt = _bekannte_namen(kurs)
    neu = []
    for name in sorted({d.split("::")[0] for d in rufe("deckNames") or []} - bekannt):
        anzahl = len(rufe("findNotes", query=_q(name)) or [])
        if anzahl:
            neu.append({"name": name, "notizen": anzahl})
    return neu


def ignorieren(kurs: Kurs, name: str) -> None:
    reg = lade_register(kurs)
    if name not in reg["ignoriert"]:
        reg["ignoriert"].append(name)
    _speichere_register(kurs, reg)


def uebernehmen(kurs: Kurs, name: str, rufe, thema: str | None = None, quelle: str = "",
                vertrauen: str = "inoffiziell") -> list[str]:
    reg = lade_register(kurs)
    if any(s["name"] == name for s in reg["stapel"]):
        raise LernFehler(f"Stapel '{name}' ist bereits übernommen")
    if "::" in name:
        raise LernFehler("Nur Hauptstapel übernehmen (Unterstapel sind automatisch enthalten)")
    if not rufe("findNotes", query=_q(name)):
        raise LernFehler(f"Stapel '{name}' in Anki nicht gefunden oder leer")
    if thema and thema not in kurs.themen_index():
        raise LernFehler(f"Unbekanntes Thema '{thema}' (themen.yaml)")
    datei = f"{ORDNER}/{_slug(name)}.yaml"
    reg["ignoriert"] = [i for i in reg["ignoriert"] if i != name]
    reg["stapel"].append({"name": name, "datei": datei, "thema": thema, "quelle": quelle, "vertrauen": vertrauen,
                          "uebernommen": date.today().isoformat()})
    _speichere_register(kurs, reg)
    return abgleich(kurs, rufe, nur=name)


# ---------------------------------------------------------------- Spiegel-Datei

def _lade_spiegel(pfad: Path) -> dict:
    daten = lade_yaml(pfad, {}) or {}
    return {int(n["id"]): n for n in daten.get("notizen") or [] if "id" in n}


def _speichere_spiegel(pfad: Path, name: str, notizen: dict[int, dict]) -> None:
    pfad.parent.mkdir(parents=True, exist_ok=True)
    inhalt = yaml.safe_dump({"stapel": name, "notizen": [notizen[i] for i in sorted(notizen)]},
                            allow_unicode=True, sort_keys=False, width=120)
    pfad.write_text(_KOPF + inhalt, encoding="utf-8", newline="\n")


def _lade_basis(kurs: Kurs) -> dict[str, str]:
    datei = kurs.lernstand / BASIS
    return json.loads(datei.read_text(encoding="utf-8")) if datei.is_file() else {}


def _speichere_basis(kurs: Kurs, basis: dict[str, str]) -> None:
    datei = kurs.lernstand / BASIS
    datei.parent.mkdir(parents=True, exist_ok=True)
    datei.write_text(json.dumps(basis, indent=0, sort_keys=True), encoding="utf-8")


def notiz_themen(kurs: Kurs) -> dict[int, str]:
    """Notiz-ID → Thema (Notiz-Thema, sonst Stapel-Thema) für alle übernommenen Stapel."""
    zuordnung = {}
    for s in lade_register(kurs)["stapel"]:
        for nid, n in _lade_spiegel(kurs.pfad / s["datei"]).items():
            tid = n.get("thema") or s.get("thema")
            if tid:
                zuordnung[nid] = tid
    return zuordnung


def abgleich(kurs: Kurs, rufe, nur: str | None = None) -> list[str]:
    """3-Wege-Abgleich Spiegel-Datei ⇄ Anki. Gibt Protokollzeilen zurück."""
    protokoll = []
    basis = _lade_basis(kurs)
    for s in lade_register(kurs)["stapel"]:
        if nur and s["name"] != nur:
            continue
        pfad = kurs.pfad / s["datei"]
        datei = _lade_spiegel(pfad)
        ids = rufe("findNotes", query=_q(s["name"])) or []
        anki = {int(n["noteId"]): n for n in (rufe("notesInfo", notes=ids) or []) if n}
        neu = geaendert_anki = geschrieben = 0
        konflikte, ungueltig = [], []
        for nid, info in anki.items():
            felder_anki = {f: v["value"] for f, v in sorted(info["fields"].items(), key=lambda kv: kv[1].get("order", 0))}
            h_anki, eintrag = _hash(felder_anki), datei.get(nid)
            if eintrag is None:
                datei[nid] = {"id": nid, "modell": info.get("modelName", ""), "thema": None, "felder": felder_anki}
                basis[str(nid)] = h_anki
                neu += 1
                continue
            felder_datei = {f: "" if v is None else str(v) for f, v in (eintrag.get("felder") or {}).items()}
            h_datei, h_basis = _hash(felder_datei), basis.get(str(nid))
            if h_datei == h_anki:
                basis[str(nid)] = h_anki
            elif h_datei == h_basis:  # nur in Anki geändert → Datei nachziehen
                eintrag["felder"] = felder_anki
                basis[str(nid)] = h_anki
                geaendert_anki += 1
            elif h_anki == h_basis:  # nur vom Agenten geändert → nach Anki schreiben
                fremd = set(felder_datei) - set(felder_anki)
                if fremd:
                    ungueltig.append(f"{nid} (unbekannte Felder: {', '.join(sorted(fremd))})")
                    continue
                rufe("updateNoteFields", note={"id": nid, "fields": felder_datei})
                basis[str(nid)] = h_datei
                geschrieben += 1
            else:  # beide Seiten geändert → Anki gewinnt, Agenten-Fassung bleibt zum Nacharbeiten erhalten
                eintrag["konflikt_agent"] = felder_datei
                eintrag["felder"] = felder_anki
                basis[str(nid)] = h_anki
                konflikte.append(str(nid))
        geloescht = [nid for nid in datei if nid not in anki]
        for nid in geloescht:
            del datei[nid]
            basis.pop(str(nid), None)
        _speichere_spiegel(pfad, s["name"], datei)
        zaehler = {"neu": neu, "aus Anki aktualisiert": geaendert_anki, "nach Anki geschrieben": geschrieben,
                   "in Anki gelöscht": len(geloescht)}
        teile = [f"{len(anki)} Notizen"] + [f"{n} {text}" for text, n in zaehler.items() if n]
        protokoll.append(f"Fremder Stapel „{s['name']}“: " + ", ".join(teile) + f" → {s['datei']}")
        if konflikte:
            protokoll.append(f"  KONFLIKT (Anki-Fassung behalten, Agenten-Fassung unter konflikt_agent): {', '.join(konflikte)}")
        if ungueltig:
            protokoll.append(f"  NICHT übertragen: {', '.join(ungueltig)}")
    _speichere_basis(kurs, basis)
    return protokoll


def hat_aenderungen(protokoll: list[str]) -> bool:
    return any("nach Anki geschrieben" in z for z in protokoll)


def statistik(kurs: Kurs, rufe) -> dict[str, dict]:
    """Statistik der übernommenen Stapel, Schlüssel n<Notiz-ID> (mit Thema und Kurztext für Brief/Mastery)."""
    themen = notiz_themen(kurs)
    stats: dict[str, dict] = {}
    for s in lade_register(kurs)["stapel"]:
        karten = rufe("findCards", query=_q(s["name"])) or []
        if not karten:
            continue
        for info in rufe("cardsInfo", cards=karten) or []:
            nid = int(info.get("note", 0))
            schluessel = f"n{nid}"
            alt = stats.get(schluessel, {"lapses": 0, "reps": 0, "interval": 0})
            stats[schluessel] = {
                "lapses": alt["lapses"] + int(info.get("lapses", 0)),
                "reps": alt["reps"] + int(info.get("reps", 0)),
                "interval": max(alt["interval"], int(info.get("interval", 0))),
                "thema": themen.get(nid),
                "stapel": s["name"],
                "kurz": kurztext({k: v.get("value", "") for k, v in sorted((info.get("fields") or {}).items(),
                                                                          key=lambda kv: kv[1].get("order", 0))}),
            }
    return stats
