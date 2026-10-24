import json
import sqlite3
import zipfile
from datetime import date

import pytest

from conftest import schreibe
from lern import anki, lernstand
from lern.auswertung import aufgaben_stand, empfehlungen, fortschritt, themen_stand
from lern.brief import brief, hook_json, schreibe_stand
from lern.cli import main
from lern.daten import LernFehler
from lern.karten import lade_karten, naechste_id
from lern.pruefen import pruefe_kurs

HEUTE = date(2026, 11, 20)


def v(ts, ergebnis, themen=("a",), aufgabe=None, art="aufgabe", **extra):
    return {"ts": f"{ts}T10:00:00", "typ": "versuch", "art": art, "themen": list(themen),
            "aufgabe": aufgabe, "ergebnis": ergebnis, **extra}


# ------------------------------------------------------------------ Mastery

def test_stufen_steigen_mit_evidenz(kurs):
    schreibe(kurs, v("2026-11-01", "erklaert", ["a", "b"]), v("2026-11-02", "hinweise", ["b"]), v("2026-11-03", "selbst", ["c"]))
    st = themen_stand(kurs, HEUTE)
    assert (st["a"].stufe, st["b"].stufe, st["c"].stufe) == (1, 2, 3)


def test_klausurfest_braucht_abstand(kurs):
    schreibe(kurs, v("2026-11-01", "selbst"), v("2026-11-04", "selbst"))
    assert themen_stand(kurs, HEUTE)["a"].stufe == 3
    schreibe(kurs, v("2026-11-09", "selbst"))
    assert themen_stand(kurs, HEUTE)["a"].stufe == 4


def test_abruf_zaehlt_nicht_als_selbststaendig(kurs):
    schreibe(kurs, v("2026-11-01", "selbst", art="abruf"))
    assert themen_stand(kurs, HEUTE)["a"].stufe == 2


def test_offener_fehler_deckelt_stufe(kurs):
    schreibe(kurs, v("2026-11-01", "selbst"))
    lernstand.log_fehler(kurs, "a", "einheit", "W und kW verwechselt")
    s = themen_stand(kurs, HEUTE)["a"]
    assert s.stufe == 2 and s.roh_stufe == 3 and s.offene_fehler == ["F-001"]
    lernstand.fehler_behoben(kurs, "F-001")
    assert themen_stand(kurs, HEUTE)["a"].stufe == 3
    assert "status: behoben" in (kurs.lernstand / "fehlerbuch.md").read_text(encoding="utf-8")


def test_auffrischen_nach_pause(kurs):
    schreibe(kurs, v("2026-10-01", "selbst"))
    assert themen_stand(kurs, HEUTE)["a"].auffrischen


# ------------------------------------------------------------------ Nachrechnen

def test_nachrechnen_nach_erklaerung(kurs):
    schreibe(kurs, v("2026-11-10", "erklaert", aufgabe="ue1-a1"), v("2026-11-10", "selbst", aufgabe="ue1-a1"))
    a = aufgaben_stand(kurs, HEUTE)["ue1-a1"]
    assert a.status == "bearbeitet" and a.faellig == date(2026, 11, 13)  # schlechtestes Ergebnis des Tages zählt
    schreibe(kurs, v("2026-11-14", "selbst", aufgabe="ue1-a1"))
    a = aufgaben_stand(kurs, HEUTE)["ue1-a1"]
    assert a.status == "selbst" and a.faellig == date(2026, 11, 24)
    schreibe(kurs, v("2026-11-25", "selbst", aufgabe="ue1-a1"))
    a = aufgaben_stand(kurs, HEUTE)["ue1-a1"]
    assert a.status == "gefestigt" and a.faellig is None


def test_sofort_selbst_geloest_braucht_kein_nachrechnen(kurs):
    schreibe(kurs, v("2026-11-10", "selbst", aufgabe="ue1-a1"))
    assert aufgaben_stand(kurs, HEUTE)["ue1-a1"].faellig is None


def test_empfehlungen_reihenfolge(kurs):
    schreibe(kurs, v("2026-11-10", "erklaert", aufgabe="ue1-a1"))
    lernstand.log_fehler(kurs, "a", "konzept", "Wärmestrom vs. Wärmestromdichte")
    arten = [e.art for e in empfehlungen(kurs, date(2099, 1, 1))]
    assert arten[0] == "nachrechnen" and arten[1] == "recheck"
    assert "neu" not in arten or arten.index("neu") > arten.index("recheck")


def test_voraussetzungen_blockieren_neues_thema(kurs):
    texte = [e.text for e in empfehlungen(kurs, HEUTE)]
    assert any("Thema A" in t for t in texte) and not any("Thema B" in t for t in texte)


def test_fortschritt_gewichtet(kurs):
    schreibe(kurs, v("2026-11-01", "selbst", ["a"]))
    f = fortschritt(kurs, HEUTE)
    assert f.abdeckung == pytest.approx(3 / 6)
    assert f.beherrschung == pytest.approx(3 * 3 / 4 / 6)


# ------------------------------------------------------------------ Log / IDs

def test_log_ids_und_warnungen(kurs):
    _, w = lernstand.log_frage(kurs, "a", "Warum ln bei Zylinder?", "Analogie Zwiebelschalen")
    e2, _ = lernstand.log_frage(kurs, "a", "Noch eine")
    assert e2["id"] == "Q-002" and w == []
    _, w = lernstand.log_versuch(kurs, "unbekannt", "selbst")
    assert w and "unbekannt" in w[0]
    with pytest.raises(LernFehler):
        lernstand.log_versuch(kurs, "a", "super")


def test_versuch_uebernimmt_themen_der_aufgabe(kurs):
    e, _ = lernstand.log_versuch(kurs, None, "hinweise", aufgabe="ue1-a2")
    assert e["themen"] == ["b"]


# ------------------------------------------------------------------ Brief / Hook / STAND

def test_brief_und_hook(repo, kurs):
    repo.setze_config("aktiver_kurs", "demo")
    lernstand.log_sitzung(kurs, "Wärmeleitung begonnen", ["Aufgabe ue1-a1 nachrechnen"])
    text = brief(repo, heute=HEUTE)
    assert "Demo-Kurs" in text and "Aufgabe ue1-a1 nachrechnen" in text and "versteht Analogien" in text
    daten = json.loads(hook_json(repo))
    assert daten["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert "Demo-Kurs" in daten["hookSpecificOutput"]["additionalContext"]
    schreibe_stand(repo)
    assert "Demo-Kurs" in (repo.wurzel / "STAND.md").read_text(encoding="utf-8")


def test_hook_ohne_repo_ist_gueltiges_json():
    assert json.loads(hook_json(None))["hookSpecificOutput"]["additionalContext"]


def test_cli_hook_ausserhalb_repo(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["brief", "--hook"]) == 0
    json.loads(capsys.readouterr().out)


# ------------------------------------------------------------------ Karten / Anki

KARTEN = """# Wärmeleitung

### dem-0001 · thema: a · quelle: Skript S. 12
F: Fourier-Gesetz?
B: $\\dot q = -\\lambda \\frac{dT}{dx}$
mit **Minus**

### dem-0002 · thema: b
C: Widerstand ebene Wand: {{c1::$R = s/(\\lambda A)$}}
Z: Reihenschaltung addiert

### dem-0003 · thema: a
F: kaputt ohne Antwort
"""


def test_karten_parser(kurs):
    (kurs.pfad / "karten" / "wl.md").write_text(KARTEN, encoding="utf-8")
    karten = {k.id: k for k in lade_karten(kurs)}
    assert karten["dem-0001"].antwort.endswith("mit **Minus**")
    assert karten["dem-0001"].quelle == "Skript S. 12"
    assert karten["dem-0002"].ist_cloze and karten["dem-0002"].zusatz == "Reihenschaltung addiert"
    assert karten["dem-0003"].probleme
    assert naechste_id(kurs) == "dem-0004"
    assert any("dem-0003" in p for p in pruefe_kurs(kurs))


def test_anki_html():
    assert anki.zu_anki_html("a < b, $x^2$ und $$y$$ **fett**") == "a &lt; b, \\(x^2\\) und \\[y\\] <b>fett</b>"


def test_apkg_export_stabile_guid(kurs, tmp_path):
    (kurs.pfad / "karten" / "wl.md").write_text(KARTEN, encoding="utf-8")
    ziel, n = anki.exportiere_apkg(kurs, tmp_path / "x.apkg")
    assert n == 2

    def notizen(pfad):
        with zipfile.ZipFile(pfad) as z:
            (tmp_path / "db").write_bytes(z.read("collection.anki2"))
        with sqlite3.connect(tmp_path / "db") as con:
            return dict(con.execute("select guid, flds from notes"))

    vorher = notizen(ziel)
    (kurs.pfad / "karten" / "wl.md").write_text(KARTEN.replace("Fourier-Gesetz?", "Fourier-Gesetz (1D)?"), encoding="utf-8")
    nachher = notizen(anki.exportiere_apkg(kurs, tmp_path / "y.apkg")[0])
    assert set(vorher) == set(nachher)  # gleiche GUIDs trotz geändertem Text
    assert any("Fourier-Gesetz (1D)?" in f for f in nachher.values())


class FakeAnki:
    def __init__(self, sync_fehler=None):
        self.aufrufe, self.sync_fehler = [], sync_fehler

    def __call__(self, aktion, **p):
        self.aufrufe.append(aktion)
        if aktion == "sync" and self.sync_fehler:
            raise LernFehler(f"AnkiConnect-Fehler bei sync: {self.sync_fehler}")
        return {"version": 6, "findCards": [1, 2], "importPackage": True,
                "cardsInfo": [{"fields": {"ID": {"value": "dem-0001"}}, "lapses": 4, "reps": 9, "interval": 3},
                              {"fields": {"ID": {"value": "dem-0002"}}, "lapses": 0, "reps": 2, "interval": 10}]}.get(aktion)


def test_ankiconnect_sync(kurs, tmp_path):
    (kurs.pfad / "karten" / "wl.md").write_text(KARTEN, encoding="utf-8")
    anki_ = FakeAnki()
    anki.synchronisiere(kurs, anki_)
    # Reihenfolge: erst holen, dann Statistik, dann importieren, dann hochladen
    assert anki_.aufrufe == ["version", "sync", "findCards", "cardsInfo", "importPackage", "sync"]
    schreibe(kurs, v("2026-11-01", "selbst"), v("2026-11-09", "selbst"))
    s = themen_stand(kurs, HEUTE)["a"]
    assert s.roh_stufe == 4 and s.stufe == 3 and s.anki_schwach == 1

    anki_.aufrufe.clear()  # Karten unverändert → kein Import, kein zweiter Sync
    anki.synchronisiere(kurs, anki_)
    assert anki_.aufrufe == ["version", "sync", "findCards", "cardsInfo"]
    assert "Anki:" in brief(kurs.repo, heute=HEUTE)

    leer = FakeAnki()  # Karten fehlen in Anki (z. B. nach vollständigem Download) → trotz gleichem Hash importieren
    anki.synchronisiere(kurs, lambda aktion, **p: [] if aktion in ("findCards", "cardsInfo") else leer(aktion, **p))
    assert "importPackage" in leer.aufrufe


def test_ankiconnect_sync_fehler_bricht_vor_import_ab(kurs):
    (kurs.pfad / "karten" / "wl.md").write_text(KARTEN, encoding="utf-8")
    anki_ = FakeAnki(sync_fehler="Sync status 3 not one of [0, 1]")
    with pytest.raises(LernFehler, match="nichts übertragen"):
        anki.synchronisiere(kurs, anki_)
    assert "importPackage" not in anki_.aufrufe

    ohne_login = FakeAnki(sync_fehler="sync: auth not configured")
    protokoll = anki.synchronisiere(kurs, ohne_login)
    assert "importPackage" in ohne_login.aufrufe and ohne_login.aufrufe.count("sync") == 1
    assert protokoll[0].startswith("WARNUNG")


def test_anki_sync_still_ohne_anki(kurs, monkeypatch, capsys):
    def weg(aktion, **p):
        raise LernFehler("AnkiConnect nicht erreichbar")
    monkeypatch.setattr(anki, "ankiconnect", weg)
    assert main(["--kurs", kurs.id, "anki", "sync", "--still"]) == 0
    assert "übersprungen" in capsys.readouterr().out


# ------------------------------------------------------------------ Einlesen / Dashboard / Prüfen

def test_einlesen_pdf(kurs):
    import pymupdf
    doc = pymupdf.open()
    for i in range(2):
        doc.new_page().insert_text((72, 72), f"Folie {i + 1}: Waermeleitung")
    (kurs.pfad / "inbox" / "VL01.pdf").write_bytes(doc.tobytes())
    from lern.einlesen import einlesen, einsortieren, seite_rendern
    einsortieren(kurs, ["VL01.pdf"], "folien")
    bericht = einlesen(kurs)
    assert bericht["neu"] == ["material/folien/VL01.pdf"]
    text = (kurs.pfad / "text" / "folien" / "VL01.md").read_text(encoding="utf-8")
    assert "<!-- seite 2 -->" in text and "Folie 2" in text
    assert einlesen(kurs)["unveraendert"] == ["material/folien/VL01.pdf"]
    assert seite_rendern(kurs, "VL01.pdf", 1).is_file()


def test_dashboard(repo, kurs):
    schreibe(kurs, v("2026-11-01", "selbst"), v("2026-11-02", "erklaert", aufgabe="ue1-a1"))
    lernstand.log_fehler(kurs, "b", "formel", "<falsche> Formel")
    from lern.dashboard import erzeuge
    html = erzeuge(repo, HEUTE).read_text(encoding="utf-8")
    assert "Demo-Kurs" in html and "&lt;falsche&gt;" in html and "Thema A" in html


def test_pruefen_findet_fehler(kurs):
    assert pruefe_kurs(kurs) == []
    schreibe(kurs, v("2026-11-01", "selbst", ["gibtsnicht"]))
    assert any("gibtsnicht" in p for p in pruefe_kurs(kurs))


def test_materialpfade_nfc(kurs):
    """macOS liefert Umlaute in Dateinamen teils als NFD – im Index immer NFC."""
    import unicodedata
    from lern.einlesen import _rel
    nfd = unicodedata.normalize("NFD", "Übung.pdf")
    assert _rel(kurs, kurs.pfad / "material" / "uebungen" / nfd) == "material/uebungen/Übung.pdf"


def test_einrichten_erkennt_os_und_venv_pfad():
    import importlib.util
    from conftest import WURZEL
    spec = importlib.util.spec_from_file_location("einrichten", WURZEL / "einrichten.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.os_name() in ("windows", "macos", "linux")
    assert mod.venv_python("windows").as_posix().endswith(".venv/Scripts/python.exe")
    assert mod.venv_python("macos").as_posix().endswith(".venv/bin/python")
    assert "brew" in mod.python_hinweis("macos")
