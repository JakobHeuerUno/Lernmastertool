"""Konsistenzprüfung der Kursdaten (für Agenten nach dem Bearbeiten von YAML/Markdown)."""

from __future__ import annotations

import re

from lern.daten import ERGEBNISSE, FEHLERTYPEN, Kurs, LernFehler
from lern.karten import lade_karten


def pruefe_kurs(kurs: Kurs) -> list[str]:
    probleme: list[str] = []
    p = lambda text: probleme.append(f"[{kurs.id}] {text}")  # noqa: E731

    try:
        meta = kurs.meta
        themen = kurs.themen
        aufgaben = kurs.aufgaben
        ereignisse = kurs.ereignisse()
    except (LernFehler, Exception) as e:
        return [f"[{kurs.id}] Datei nicht lesbar: {e}"]

    if not meta.get("name"):
        p("kurs.yaml: 'name' fehlt")
    datum = (meta.get("klausur") or {}).get("datum")
    if datum and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(datum)):
        p(f"kurs.yaml: klausur.datum '{datum}' nicht im Format JJJJ-MM-TT")

    ids = [t.get("id") for t in themen]
    for t in themen:
        if not t.get("id"):
            p(f"themen.yaml: Thema ohne id: {t}")
    for d in {i for i in ids if ids.count(i) > 1}:
        p(f"themen.yaml: doppelte id '{d}'")
    bekannt = set(ids)
    for t in themen:
        for v in t.get("voraussetzungen") or []:
            if v not in bekannt:
                p(f"themen.yaml: {t.get('id')} → unbekannte Voraussetzung '{v}'")
        rel = t.get("klausurrelevanz", 2)
        if rel not in (1, 2, 3):
            p(f"themen.yaml: {t.get('id')} klausurrelevanz muss 1, 2 oder 3 sein")

    aids = [a.get("id") for a in aufgaben]
    for d in {i for i in aids if aids.count(i) > 1}:
        p(f"aufgaben.yaml: doppelte id '{d}'")
    for a in aufgaben:
        for t in a.get("themen") or []:
            if bekannt and t not in bekannt:
                p(f"aufgaben.yaml: {a.get('id')} → unbekanntes Thema '{t}'")
        if a.get("datei") and not (kurs.pfad / a["datei"]).is_file():
            p(f"aufgaben.yaml: {a.get('id')} → Datei fehlt: {a['datei']}")

    for nr, e in enumerate(ereignisse, 1):
        if e.get("typ") == "versuch" and e.get("ergebnis") not in ERGEBNISSE:
            p(f"ereignisse.jsonl Zeile {nr}: ungültiges ergebnis {e.get('ergebnis')}")
        if e.get("typ") == "fehler" and e.get("fehlertyp") not in FEHLERTYPEN:
            p(f"ereignisse.jsonl Zeile {nr}: ungültiger fehlertyp {e.get('fehlertyp')}")
        for t in e.get("themen", []):
            if bekannt and t not in bekannt:
                p(f"ereignisse.jsonl Zeile {nr}: Thema '{t}' nicht in themen.yaml")
        if e.get("aufgabe") and aids and e["aufgabe"] not in aids:
            p(f"ereignisse.jsonl Zeile {nr}: Aufgabe '{e['aufgabe']}' nicht in aufgaben.yaml")

    karten = lade_karten(kurs)
    kids = [k.id for k in karten]
    for d in {i for i in kids if kids.count(i) > 1}:
        p(f"karten: doppelte Karten-ID '{d}'")
    for k in karten:
        for prob in k.probleme:
            p(f"{k.datei.name}:{k.zeile} ({k.id}): {prob}")
        if k.thema and bekannt and k.thema not in bekannt:
            p(f"{k.datei.name}:{k.zeile} ({k.id}): unbekanntes Thema '{k.thema}'")

    from lern.anki_fremd import _lade_spiegel, lade_register
    try:
        register = lade_register(kurs)
    except Exception as e:
        return probleme + [f"[{kurs.id}] anki-fremd.yaml nicht lesbar: {e}"]
    for st in register["stapel"]:
        if st.get("thema") and bekannt and st["thema"] not in bekannt:
            p(f"anki-fremd.yaml: Stapel „{st['name']}“ → unbekanntes Thema '{st['thema']}'")
        try:
            notizen = _lade_spiegel(kurs.pfad / st["datei"])
        except Exception as e:
            p(f"{st['datei']}: nicht lesbar ({e})")
            continue
        for nid, n in notizen.items():
            if n.get("thema") and bekannt and n["thema"] not in bekannt:
                p(f"{st['datei']}: Notiz {nid} → unbekanntes Thema '{n['thema']}'")
            if not isinstance(n.get("felder"), dict):
                p(f"{st['datei']}: Notiz {nid} → 'felder' fehlt oder ist kein Mapping")
    return probleme
