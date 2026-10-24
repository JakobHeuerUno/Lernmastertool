"""Kommandozeile: `python -m lern <befehl>` bzw. `lern <befehl>`."""

from __future__ import annotations

import argparse
import io
import sys

from lern.daten import ARTEN, ERGEBNISSE, FEHLERTYPEN, MATERIALTYPEN, LernFehler, Repo


def _utf8() -> None:
    for strom in ("stdout", "stderr"):
        s = getattr(sys, strom)
        if isinstance(s, io.TextIOWrapper) and (s.encoding or "").lower() != "utf-8":
            s.reconfigure(encoding="utf-8")


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="lern", description="Lernstand-Tool der LERNECKE")
    p.add_argument("--kurs", help="Kurs-ID (Standard: aktiver Kurs aus lern.yaml)")
    sub = p.add_subparsers(dest="befehl", required=True)

    k = sub.add_parser("kurs", help="Kurse anlegen/wechseln/auflisten").add_subparsers(dest="aktion", required=True)
    kn = k.add_parser("neu")
    kn.add_argument("id")
    kn.add_argument("name")
    kn.add_argument("--kuerzel")
    k.add_parser("aktiv").add_argument("id")
    k.add_parser("liste")

    sub.add_parser("inbox", help="Dateien in inbox/ auflisten")
    es = sub.add_parser("einsortieren", help="Dateien aus inbox/ nach material/<typ>/ verschieben und einlesen")
    es.add_argument("dateien", nargs="+")
    es.add_argument("--typ", required=True, choices=MATERIALTYPEN)
    es.add_argument("--vertrauen", choices=("offiziell", "inoffiziell"))
    ei = sub.add_parser("einlesen", help="material/ indexieren, PDFs → text/*.md")
    ei.add_argument("--neu", action="store_true", help="alles neu umwandeln")
    se = sub.add_parser("seite", help="PDF-Seite als PNG rendern (für Formeln/Bilder)")
    se.add_argument("datei")
    se.add_argument("seite", type=int)
    se.add_argument("--zoom", type=float, default=2.0)

    b = sub.add_parser("brief", help="kompakter Lernstand (Sessionstart)")
    b.add_argument("--hook", action="store_true", help="JSON für SessionStart-Hooks")
    sub.add_parser("status", help="ausführlicher Fortschritt")
    sub.add_parser("weiter", help="Empfehlung, was als Nächstes dran ist")
    sub.add_parser("aufgaben", help="Aufgabenkatalog mit Status und Nachrechen-Terminen")

    log = sub.add_parser("log", help="Lernereignis protokollieren").add_subparsers(dest="art_log", required=True)
    lv = log.add_parser("versuch")
    lv.add_argument("--thema", help="Themen-ID(s), kommagetrennt")
    lv.add_argument("--aufgabe")
    lv.add_argument("--teil")
    lv.add_argument("--ergebnis", required=True, choices=ERGEBNISSE)
    lv.add_argument("--art", default="aufgabe", choices=ARTEN)
    lv.add_argument("--konfidenz", type=int)
    lv.add_argument("--notiz")
    lf = log.add_parser("fehler")
    lf.add_argument("--thema", required=True)
    lf.add_argument("--typ", required=True, choices=FEHLERTYPEN)
    lf.add_argument("--aufgabe")
    lf.add_argument("--teil")
    lf.add_argument("kurz", help="ein Satz: was schiefging")
    lq = log.add_parser("frage")
    lq.add_argument("--thema", required=True)
    lq.add_argument("--hilfreich", help="welche Erklärung/Analogie geholfen hat")
    lq.add_argument("frage")
    ls = log.add_parser("sitzung")
    ls.add_argument("zusammenfassung")
    ls.add_argument("--naechster", action="append", default=[], help="nächster Schritt (mehrfach möglich)")
    ls.add_argument("--dauer", type=int)
    ls.add_argument("--datei")

    fb = sub.add_parser("fehler", help="Fehlerbuch-Aktionen").add_subparsers(dest="aktion", required=True)
    fbb = fb.add_parser("behoben")
    fbb.add_argument("id")
    fbb.add_argument("--notiz")

    ka = sub.add_parser("karten", help="Karteikarten").add_subparsers(dest="aktion", required=True)
    ka.add_parser("naechste-id")
    ka.add_parser("liste")
    an = sub.add_parser("anki", help="Anki-Export/-Sync").add_subparsers(dest="aktion", required=True)
    an.add_parser("export", help=".apkg nach ausgabe/ schreiben")
    an.add_parser("push", help="per AnkiConnect direkt in Anki (ohne AnkiWeb-Sync)")
    an.add_parser("pull", help="Statistik (lapses) per AnkiConnect holen (ohne AnkiWeb-Sync)")
    asy = an.add_parser("sync", help="Standard mit AnkiConnect: AnkiWeb holen → Statistik → Karten → AnkiWeb hochladen")
    asy.add_argument("--still", action="store_true", help="nicht als Fehler werten, wenn Anki geschlossen ist")
    asy.add_argument("--ohne-push", action="store_true", help="nur synchronisieren und Statistik holen")
    af = an.add_parser("fremd", help="fremde Stapel (z. B. von Kommilitonen) erkennen/übernehmen").add_subparsers(
        dest="fremd_aktion", required=True)
    af.add_parser("liste", help="übernommene und neu erkannte Stapel anzeigen")
    afu = af.add_parser("uebernehmen", help="Stapel dem Kurs zuordnen und nach karten-fremd/ spiegeln")
    afu.add_argument("name", help="Name des Hauptstapels in Anki")
    afu.add_argument("--thema", help="Standard-Thema für alle Notizen (einzeln in der YAML überschreibbar)")
    afu.add_argument("--quelle", default="", help="Herkunft, z. B. StudyDrive, Kommilitone")
    afu.add_argument("--vertrauen", default="inoffiziell", choices=["inoffiziell", "offiziell"])
    af.add_parser("ignorieren", help="Stapel nicht mehr als neu melden").add_argument("name")

    sub.add_parser("dashboard", help="ausgabe/dashboard.html erzeugen")
    sub.add_parser("pruefen", help="Kursdaten auf Konsistenz prüfen")
    return p


def _warn(warnungen) -> None:
    for w in warnungen:
        print(w, file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    _utf8()
    args = _parser().parse_args(argv)

    if args.befehl == "brief" and args.hook:
        from lern.brief import hook_json
        try:
            repo = Repo.finde()
        except Exception:
            repo = None
        print(hook_json(repo))
        return 0

    try:
        return _ausfuehren(args)
    except LernFehler as e:
        print(f"Fehler: {e}", file=sys.stderr)
        return 1


def _ausfuehren(args) -> int:  # noqa: C901 – flacher Dispatcher
    repo = Repo.finde()
    from lern.brief import schreibe_stand

    if args.befehl == "kurs":
        from lern.kurs import neuer_kurs, setze_aktiv
        if args.aktion == "neu":
            kurs = neuer_kurs(repo, args.id, args.name, args.kuerzel)
            print(f"Kurs angelegt: {kurs.pfad}")
        elif args.aktion == "aktiv":
            print(f"Aktiver Kurs: {setze_aktiv(repo, args.id).name}")
        else:
            aktiv = repo.config.get("aktiver_kurs")
            for i in repo.kurs_ids():
                print(f"{'*' if i == aktiv else ' '} {i}  –  {repo.kurs(i).name}")
        schreibe_stand(repo)
        return 0

    kurs = repo.kurs(args.kurs)

    if args.befehl == "inbox":
        from lern.einlesen import inbox_dateien
        dateien = inbox_dateien(kurs)
        print("\n".join(str(d.relative_to(kurs.pfad)) for d in dateien) or "inbox/ ist leer.")
    elif args.befehl in ("einsortieren", "einlesen"):
        from lern.einlesen import einlesen, einsortieren
        if args.befehl == "einsortieren":
            for z in einsortieren(kurs, args.dateien, args.typ, args.vertrauen):
                print(f"→ {z.relative_to(kurs.pfad).as_posix()}")
        bericht = einlesen(kurs, getattr(args, "neu", False))
        for status, liste in bericht.items():
            if liste and status != "unveraendert":
                print(f"{status}: " + ", ".join(liste))
        print(f"({len(bericht['unveraendert'])} unverändert) – Index: material.yaml, Text: text/")
    elif args.befehl == "seite":
        from lern.einlesen import seite_rendern
        print(seite_rendern(kurs, args.datei, args.seite, args.zoom))
    elif args.befehl == "brief":
        from lern.brief import brief
        print(brief(repo, args.kurs))
    elif args.befehl == "status":
        _status(kurs)
    elif args.befehl == "weiter":
        from lern.auswertung import empfehlungen
        for i, e in enumerate(empfehlungen(kurs), 1):
            print(f"{i}. [{e.art}] {e.text}")
    elif args.befehl == "aufgaben":
        from lern.auswertung import aufgaben_stand
        for a in aufgaben_stand(kurs).values():
            termin = f" · nachrechnen am {a.faellig:%d.%m.}" if a.faellig else ""
            print(f"{a.id:<14} {a.status:<10} {a.titel}{termin}")
    elif args.befehl == "log":
        from lern import lernstand as ls
        if args.art_log == "versuch":
            e, w = ls.log_versuch(kurs, args.thema, args.ergebnis, args.aufgabe, args.teil, args.art, args.konfidenz, args.notiz)
        elif args.art_log == "fehler":
            e, w = ls.log_fehler(kurs, args.thema, args.typ, args.kurz, args.aufgabe, args.teil)
        elif args.art_log == "frage":
            e, w = ls.log_frage(kurs, args.thema, args.frage, args.hilfreich)
        else:
            e, w = ls.log_sitzung(kurs, args.zusammenfassung, args.naechster, args.dauer, args.datei), []
        _warn(w)
        print(f"protokolliert: {e.get('id', e['typ'])}")
        schreibe_stand(repo)
    elif args.befehl == "fehler":
        from lern.lernstand import fehler_behoben
        fehler_behoben(kurs, args.id, args.notiz)
        print(f"{args.id} als behoben markiert")
        schreibe_stand(repo)
    elif args.befehl == "karten":
        from lern.karten import lade_karten, naechste_id
        if args.aktion == "naechste-id":
            print(naechste_id(kurs))
        else:
            for k in lade_karten(kurs):
                print(f"{k.id:<10} {k.thema:<20} {(k.cloze or k.frage).splitlines()[0][:70] if (k.cloze or k.frage) else ''}")
    elif args.befehl == "anki":
        from lern import anki
        if args.aktion == "export":
            ziel, n = anki.exportiere_apkg(kurs)
            print(f"{n} Karten → {ziel}\nIn Anki: Datei → Importieren (bestehende Karten werden aktualisiert, Lernhistorie bleibt).")
        elif args.aktion == "push":
            print(f"{anki.push(kurs)} Karten in Anki importiert. Für das Handy danach synchronisieren (besser: `lern anki sync`).")
        elif args.aktion == "sync":
            try:
                print("\n".join(anki.synchronisiere(kurs, mit_push=not args.ohne_push)))
            except anki.AnkiNichtErreichbar as e:
                if not args.still:
                    raise
                print("Anki nicht erreichbar (Anki-Desktop geschlossen?) – Abgleich übersprungen.")
                return 0
            schreibe_stand(repo)
        elif args.aktion == "fremd":
            from lern import anki_fremd
            if args.fremd_aktion == "ignorieren":
                anki_fremd.ignorieren(kurs, args.name)
                print(f"„{args.name}“ wird nicht mehr gemeldet (anki-fremd.yaml)")
            elif args.fremd_aktion == "uebernehmen":
                print("\n".join(anki_fremd.uebernehmen(kurs, args.name, anki.ankiconnect, args.thema, args.quelle,
                                                       args.vertrauen)))
                print("Statistik dieses Stapels fließt ab jetzt bei `lern anki sync` in den Lernstand ein.")
            else:
                for st in anki_fremd.lade_register(kurs)["stapel"]:
                    print(f"übernommen: „{st['name']}“ → {st['datei']} (Thema: {st.get('thema') or '–'}, {st.get('quelle') or 'Quelle ?'})")
                for st in anki_fremd.erkenne(kurs, anki.ankiconnect):
                    print(f"NEU: „{st['name']}“ ({st['notizen']} Notizen)")
        else:
            print(f"Statistik für {anki.pull(kurs)} Karten gespeichert (lernstand/anki-stats.json)")
            schreibe_stand(repo)
    elif args.befehl == "dashboard":
        from lern.dashboard import erzeuge
        print(erzeuge(repo))
    elif args.befehl == "pruefen":
        from lern.pruefen import pruefe_kurs
        probleme = [p for i in repo.kurs_ids() for p in pruefe_kurs(repo.kurs(i))]
        print("\n".join(probleme) if probleme else "Alles konsistent.")
        return 1 if probleme else 0
    return 0


def _status(kurs) -> None:
    from lern.auswertung import STUFEN, fortschritt, themen_stand
    f = fortschritt(kurs)
    print(f"{kurs.name}")
    if f.klausur_datum:
        print(f"Klausur: {f.klausur_datum:%d.%m.%Y} (in {f.tage_bis_klausur} Tagen)")
    print(f"Abdeckung {round(f.abdeckung * 100)} % · Beherrschung {round(f.beherrschung * 100)} % · {f.themen_gesamt} Themen")
    print("Stufen: " + ", ".join(f"{STUFEN[s]}: {f.stufen_verteilung.get(s, 0)}" for s in range(5)))
    print(f"Aufgaben: {f.aufgaben_bearbeitet}/{f.aufgaben_gesamt} bearbeitet, {f.aufgaben_selbst} selbst gelöst")
    print(f"Fehler: {f.fehler_offen} offen, {f.fehler_behoben} behoben · Typen: "
          + (", ".join(f"{k} {v}" for k, v in sorted(f.fehlertypen.items(), key=lambda kv: -kv[1])) or "–"))
    if f.kalibrierung["sicher_gesamt"]:
        print(f"Kalibrierung: {f.kalibrierung['sicher_falsch']} von {f.kalibrierung['sicher_gesamt']} „sicheren“ Antworten waren falsch")
    print(f"Lerntage: {len(f.lerntage)} · Sitzungen: {f.sitzungen} · Nachfragen: {f.fragen}")
    if f.prognose:
        print(f"Prognose: {f.prognose}")
    print("\nThemen:")
    kapitel = None
    for t in themen_stand(kurs).values():
        if t.kapitel != kapitel:
            kapitel = t.kapitel
            print(f"  {kapitel}")
        extra = (" ↻ auffrischen" if t.auffrischen else "") + (f" ({'; '.join(t.gruende)})" if t.gruende else "")
        print(f"    [{t.stufe}] {t.titel} – {STUFEN[t.stufe]}{extra}")
