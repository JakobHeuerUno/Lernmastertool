"""Kompakter Lernstand für Sessionstart (Hook), `lern brief` und STAND.md."""

from __future__ import annotations

import json
import re
from datetime import date

from lern.auswertung import STUFEN, empfehlungen, fortschritt, offene_fehler, themen_stand
from lern.daten import Kurs, Repo, als_datum


def _prozent(x: float) -> str:
    return f"{round(x * 100)} %"


def kurzprofil(repo: Repo) -> list[str]:
    """Abschnitt '## Kurzprofil' aus profil/lernprofil.md (max. 8 Zeilen)."""
    datei = repo.wurzel / "profil" / "lernprofil.md"
    if not datei.is_file():
        return []
    text = datei.read_text(encoding="utf-8")
    m = re.search(r"^## Kurzprofil\s*\n(.*?)(?=^## |\Z)", text, flags=re.S | re.M)
    if not m:
        return []
    zeilen = [z for z in m.group(1).strip().splitlines() if z.strip() and not z.strip().startswith("<!--")]
    return zeilen[:8]


def kurs_zeile(kurs: Kurs, heute: date) -> str:
    f = fortschritt(kurs, heute)
    klausur = f" · Klausur in {f.tage_bis_klausur} Tagen" if f.tage_bis_klausur is not None else ""
    return (f"{kurs.name} ({kurs.id}): Abdeckung {_prozent(f.abdeckung)}, Beherrschung {_prozent(f.beherrschung)}, "
            f"{f.fehler_offen} offene Fehler{klausur}")


def letzte_sitzung(kurs: Kurs) -> dict | None:
    sitzungen = [e for e in kurs.ereignisse() if e.get("typ") == "sitzung"]
    return sitzungen[-1] if sitzungen else None


def git_branch(repo: Repo) -> str | None:
    """Aktueller Git-Branch aus .git/HEAD (ohne git-Aufruf); None ohne Repo oder bei detached HEAD."""
    head = repo.wurzel / ".git" / "HEAD"
    if not head.is_file():
        return None
    m = re.match(r"ref: refs/heads/(.+)", head.read_text(encoding="utf-8").strip())
    return m.group(1) if m else None


def kurs_branches(repo: Repo) -> list[str]:
    """Lokale Kurs-Branches (kurs/<id>), auch gepackte Refs."""
    git = repo.wurzel / ".git"
    heads = git / "refs" / "heads"
    namen = {p.relative_to(heads).as_posix() for p in (heads / "kurs").rglob("*") if p.is_file()}
    packed = git / "packed-refs"
    if packed.is_file():
        namen |= set(re.findall(r"refs/heads/(kurs/\S+)", packed.read_text(encoding="utf-8")))
    return sorted(namen)


def branch_hinweis(repo: Repo, kurs_id: str | None) -> list[str]:
    """Warnt, wenn der ausgecheckte Branch nicht zum Kurs passt (master = nur Grundgerüst, kurs/<id> = Kurs)."""
    branch = git_branch(repo)
    if branch is None or kurs_id is None or branch == f"kurs/{kurs_id}":
        return []
    return [f"**Achtung Branch:** ausgecheckt ist `{branch}`, Kurs `{kurs_id}` gehört auf `kurs/{kurs_id}`. "
            f"Lernstand nur dort committen (`git checkout kurs/{kurs_id}`); master nur für Tool/Skills.", ""]


def brief(repo: Repo, kurs_id: str | None = None, heute: date | None = None) -> str:
    heute = heute or date.today()
    zeilen = [f"# LERNECKE – Lernstand ({heute:%d.%m.%Y})", ""]
    ids = repo.kurs_ids()
    if not ids:
        branches = kurs_branches(repo)
        if branches:
            return "\n".join(zeilen + [f"Branch `{git_branch(repo)}` enthält keinen Kurs (master = nur Grundgerüst). "
                                       "Zum Lernen Kurs-Branch auschecken:"] + [f"- `git checkout {b}`" for b in branches])
        return "\n".join(zeilen + ["Noch kein Kurs angelegt. Skill `kurs-einrichten` nutzen."])
    try:
        kurs = repo.kurs(kurs_id)
    except Exception as e:  # kein aktiver Kurs
        return "\n".join(zeilen + [str(e), "", "Kurse:"] + [f"- {i}" for i in ids])
    zeilen += branch_hinweis(repo, kurs.id)

    f = fortschritt(kurs, heute)
    meta = kurs.meta
    klausur = meta.get("klausur") or {}
    zeilen.append(f"**Aktiver Kurs:** {kurs.name} (`{kurs.id}`)")
    if f.klausur_datum:
        zeilen.append(f"**Klausur:** {f.klausur_datum:%d.%m.%Y} (in {f.tage_bis_klausur} Tagen)"
                      + (f" · Hilfsmittel: {klausur.get('hilfsmittel')}" if klausur.get("hilfsmittel") else ""))
    else:
        zeilen.append("**Klausur:** Datum noch nicht eingetragen (kurs.yaml)")
    zeilen.append(f"**Fortschritt:** {f.themen_gesamt} Themen · Abdeckung {_prozent(f.abdeckung)} · "
                  f"Beherrschung {_prozent(f.beherrschung)} · Aufgaben {f.aufgaben_bearbeitet}/{f.aufgaben_gesamt} bearbeitet, "
                  f"{f.aufgaben_selbst} selbst gelöst · Fehler {f.fehler_offen} offen/{f.fehler_behoben} behoben")
    if f.prognose:
        zeilen.append(f"**Prognose:** {f.prognose}")

    sitzung = letzte_sitzung(kurs)
    if sitzung:
        tag = als_datum(sitzung["ts"])
        zeilen += ["", f"## Letzte Sitzung ({tag:%d.%m.})", sitzung.get("kurz", "")]
        for s in sitzung.get("naechste_schritte", []):
            zeilen.append(f"- Nächster Schritt: {s}")

    emp = empfehlungen(kurs, heute)
    if emp:
        zeilen += ["", "## Empfohlen als Nächstes"] + [f"{i}. {e.text}" for i, e in enumerate(emp, 1)]

    ereignisse = kurs.ereignisse()
    offen = offene_fehler(ereignisse)
    if offen:
        zeilen += ["", "## Offene Fehler (Fehlerbuch) – im Unterricht proaktiv ansprechen"]
        for fid, e in list(offen.items())[-6:]:
            zeilen.append(f"- {fid} [{e.get('fehlertyp')}] {', '.join(e.get('themen', []))}: {e.get('kurz', '')}")

    fragen = [e for e in ereignisse if e.get("typ") == "frage"][-4:]
    if fragen:
        zeilen += ["", "## Letzte Nachfragen"]
        for e in fragen:
            hilf = f" → half: {e['hilfreich']}" if e.get("hilfreich") else ""
            zeilen.append(f"- {e['id']} ({', '.join(e.get('themen', []))}): {e.get('kurz', '')}{hilf}")

    themen = themen_stand(kurs, heute, ereignisse)
    schwach = [t for t in themen.values() if t.gruende and t.stufe < t.roh_stufe]
    if schwach:
        zeilen += ["", "## Abgewertete Themen"]
        zeilen += [f"- {t.titel}: Stufe {t.stufe} „{STUFEN[t.stufe]}“ ({'; '.join(t.gruende)})" for t in schwach[:5]]

    stats = kurs.anki_stats()
    vergessen = sorted(((k, v) for k, v in stats.items() if int(v.get("lapses", 0)) >= 3),
                       key=lambda kv: -int(kv[1]["lapses"]))[:5]
    from lern.anki import lade_sync_zustand
    sync = lade_sync_zustand(kurs).get("letzter_abgleich")
    if sync:
        tage = (heute - date.fromisoformat(sync[:10])).days
        zeilen += ["", f"**Anki:** letzter Abgleich {date.fromisoformat(sync[:10]):%d.%m.} (vor {tage} Tagen) – "
                       "bei Anki-Bezug Skill `anki`; Abgleich: `lern anki sync --still`"]
    if vergessen:
        zeilen += ["", "## Anki: oft vergessene Karten"] + [f"- {k}{' „' + v['kurz'] + '“ (' + v['stapel'] + ')' if v.get('stapel') else ''} ({v['lapses']}× vergessen)"
                                                           for k, v in vergessen]

    profil = kurzprofil(repo)
    if profil:
        zeilen += ["", "## Lernprofil (Kurzfassung)"] + profil

    andere = [i for i in ids if i != kurs.id]
    if andere:
        zeilen += ["", "## Weitere Kurse"] + [f"- {kurs_zeile(repo.kurs(i), heute)}" for i in andere]

    zeilen += ["", "_Details: `lern status`, Fehlerbuch: kurse/" + kurs.id + "/lernstand/fehlerbuch.md_"]
    return "\n".join(zeilen)


def schreibe_stand(repo: Repo) -> None:
    """STAND.md für Umgebungen ohne Hook/Code (Cowork, ChatGPT Work)."""
    try:
        text = brief(repo)
    except Exception as e:  # STAND.md darf nie einen Log-Befehl scheitern lassen
        text = f"# LERNECKE – Lernstand\n\nFehler beim Erzeugen: {e}"
    (repo.wurzel / "STAND.md").write_text(
        "<!-- automatisch erzeugt von `lern` – nicht von Hand bearbeiten -->\n" + text + "\n",
        encoding="utf-8", newline="\n")


def hook_json(repo: Repo | None) -> str:
    """Ausgabe für SessionStart-Hooks (Claude Code + Codex): immer gültiges JSON."""
    try:
        text = brief(repo) if repo else "LERNECKE nicht gefunden."
        text += ("\n\n(Automatisch beim Sessionstart eingespielt. Nutze diesen Lernstand; "
                 "logge während der Session mit `lern log …` gemäß AGENTS.md.)")
    except Exception as e:
        text = f"Lernstand konnte nicht geladen werden ({e}). Bitte `lern brief` ausführen."
    # ASCII-only: übersteht jede Konsolen-Codepage (PowerShell 5.1 re-encodiert Ausgaben)
    return json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}},
                      ensure_ascii=True)
