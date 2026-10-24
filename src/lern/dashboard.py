"""Statisches, offline lauffähiges HTML-Dashboard (eine Datei, Inline-CSS/SVG)."""

from __future__ import annotations

from collections import Counter
from datetime import date, timedelta
from html import escape
from pathlib import Path

from lern.auswertung import STUFEN, aufgaben_stand, empfehlungen, fortschritt, offene_fehler, themen_stand
from lern.daten import Kurs, Repo, als_datum

_CSS = """
:root { color-scheme: light;
  --page:#f9f9f7; --surface:#fcfcfb; --ink:#0b0b0b; --ink2:#52514e; --muted:#898781;
  --grid:#e1e0d9; --axis:#c3c2b7; --ring:rgba(11,11,11,.10); --bar:#2a78d6;
  --s0:#e1e0d9; --s1:#86b6ef; --s2:#3987e5; --s3:#256abf; --s4:#104281;
  --h0:#efeee9; --h1:#b7d3f6; --h2:#6da7ec; --h3:#2a78d6; --h4:#1c5cab;
  --crit:#d03b3b; --good:#006300; --t1:#0b0b0b; --t4:#fff; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { color-scheme: dark;
  --page:#0d0d0d; --surface:#1a1a19; --ink:#f0efec; --ink2:#c3c2b7; --muted:#898781;
  --grid:#2c2c2a; --axis:#383835; --ring:rgba(255,255,255,.10); --bar:#3987e5;
  --s0:#383835; --s1:#184f95; --s2:#256abf; --s3:#3987e5; --s4:#86b6ef;
  --h0:#242423; --h1:#104281; --h2:#1c5cab; --h3:#3987e5; --h4:#86b6ef;
  --crit:#e66767; --good:#0ca30c; --t1:#fff; --t4:#0b0b0b; } }
:root[data-theme="dark"] { color-scheme: dark;
  --page:#0d0d0d; --surface:#1a1a19; --ink:#f0efec; --ink2:#c3c2b7; --muted:#898781;
  --grid:#2c2c2a; --axis:#383835; --ring:rgba(255,255,255,.10); --bar:#3987e5;
  --s0:#383835; --s1:#184f95; --s2:#256abf; --s3:#3987e5; --s4:#86b6ef;
  --h0:#242423; --h1:#104281; --h2:#1c5cab; --h3:#3987e5; --h4:#86b6ef;
  --crit:#e66767; --good:#0ca30c; --t1:#fff; --t4:#0b0b0b; }
* { box-sizing: border-box; }
body { margin:0; background:var(--page); color:var(--ink); font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif; }
main { max-width:1100px; margin:0 auto; padding:24px 16px 64px; }
h1 { font-size:24px; margin:0 0 4px; } h2 { font-size:19px; margin:0; } h3 { font-size:15px; margin:0 0 10px; color:var(--ink2); font-weight:600; }
.sub { color:var(--ink2); margin:0 0 24px; }
.kurs { min-width:0; overflow-wrap:anywhere; background:var(--surface); border:1px solid var(--ring); border-radius:12px; padding:20px; margin-bottom:24px; }
.kopf { display:flex; flex-wrap:wrap; justify-content:space-between; gap:8px; align-items:baseline; margin-bottom:16px; }
.countdown { color:var(--ink2); }
.tiles { display:grid; grid-template-columns:repeat(auto-fit,minmax(min(150px,100%),1fr)); gap:12px; margin-bottom:20px; }
.tile { border:1px solid var(--ring); border-radius:10px; padding:12px; }
.tile .w { font-size:26px; font-weight:600; } .tile .l { color:var(--ink2); font-size:13px; }
.track { height:6px; background:var(--grid); border-radius:3px; margin-top:8px; overflow:hidden; }
.track > div { height:100%; background:var(--bar); border-radius:3px; }
.grid2 { display:grid; grid-template-columns:repeat(auto-fit,minmax(min(300px,100%),1fr)); gap:20px; margin-top:8px; }
section.box { border-top:1px solid var(--grid); padding-top:14px; }
.kapitel { margin-bottom:10px; } .kapitel .n { font-size:13px; color:var(--ink2); margin-bottom:4px; }
.zellen { display:flex; flex-wrap:wrap; gap:4px; }
.zelle { min-width:28px; height:28px; border-radius:4px; display:flex; align-items:center; justify-content:center;
  font-size:12px; padding:0 6px; color:#fff; cursor:default; }
.zelle.z0 { background:var(--s0); color:var(--ink2); } .zelle.z1 { background:var(--s1); color:var(--t1); }
.zelle.z2 { background:var(--s2); } .zelle.z3 { background:var(--s3); } .zelle.z4 { background:var(--s4); color:var(--t4); }
.legende { display:flex; flex-wrap:wrap; gap:12px; font-size:12px; color:var(--ink2); margin-top:8px; }
.legende span::before { content:""; display:inline-block; width:12px; height:12px; border-radius:3px; margin-right:5px; vertical-align:-2px; background:var(--c); }
.hbar { display:grid; grid-template-columns:100px 1fr 32px; gap:8px; align-items:center; font-size:13px; margin-bottom:6px; }
.hbar .b { height:10px; background:var(--grid); border-radius:0 4px 4px 0; } .hbar .b > div { height:100%; background:var(--bar); border-radius:0 4px 4px 0; }
.hbar .v { color:var(--ink2); text-align:right; font-variant-numeric:tabular-nums; }
ul.liste { margin:0; padding-left:18px; } ul.liste li { margin-bottom:4px; }
.fid { font-weight:600; color:var(--crit); } .leer { color:var(--muted); font-size:13px; }
details { margin-top:16px; } summary { cursor:pointer; color:var(--ink2); }
table { border-collapse:collapse; width:100%; font-size:13px; margin-top:8px; }
th, td { text-align:left; padding:4px 8px; border-bottom:1px solid var(--grid); } th { color:var(--ink2); font-weight:600; }
td.n { font-variant-numeric:tabular-nums; }
.theme { position:fixed; top:12px; right:12px; background:var(--surface); color:var(--ink2); border:1px solid var(--ring);
  border-radius:8px; padding:4px 10px; cursor:pointer; font:inherit; font-size:13px; }
svg text { fill:var(--muted); font-size:10px; }
"""

_JS = """
const b=document.querySelector('.theme');b.onclick=()=>{const r=document.documentElement;
const dunkel=r.dataset.theme? r.dataset.theme==='dark' : matchMedia('(prefers-color-scheme: dark)').matches;
r.dataset.theme=dunkel?'light':'dark';try{localStorage.setItem('lernecke-theme',r.dataset.theme)}catch(e){}};
try{const t=localStorage.getItem('lernecke-theme');if(t)document.documentElement.dataset.theme=t}catch(e){}
"""


def _pz(x: float) -> str:
    return f"{round(x * 100)} %"


def _tile(wert: str, label: str, anteil: float | None = None) -> str:
    track = f'<div class="track"><div style="width:{max(0, min(1, anteil)) * 100:.1f}%"></div></div>' if anteil is not None else ""
    return f'<div class="tile"><div class="w">{escape(wert)}</div><div class="l">{escape(label)}</div>{track}</div>'


def _themenkarte(kurs: Kurs, heute: date) -> str:
    staende = themen_stand(kurs, heute)
    if not staende:
        return '<p class="leer">Noch keine Themenlandkarte (themen.yaml).</p>'
    kapitel: dict[str, list] = {}
    for s in staende.values():
        kapitel.setdefault(s.kapitel or "(ohne Kapitel)", []).append(s)
    teile = []
    for name, liste in kapitel.items():
        zellen = "".join(
            f'<div class="zelle z{s.stufe}" title="{escape(s.titel)} – Stufe {s.stufe}: {STUFEN[s.stufe]}'
            f'{" · auffrischen" if s.auffrischen else ""}{" · " + escape("; ".join(s.gruende)) if s.gruende else ""}">'
            f'{s.stufe}{"↻" if s.auffrischen else ""}</div>' for s in liste)
        teile.append(f'<div class="kapitel"><div class="n">{escape(name)}</div><div class="zellen">{zellen}</div></div>')
    legende = "".join(f'<span style="--c:var(--s{i})">{i} {STUFEN[i]}</span>' for i in range(5))
    zeilen = "".join(f"<tr><td>{escape(s.kapitel)}</td><td>{escape(s.titel)}</td><td class='n'>{s.stufe} {STUFEN[s.stufe]}</td>"
                     f"<td class='n'>{s.relevanz}</td><td>{s.letzte_aktivitaet or '–'}</td></tr>" for s in staende.values())
    tabelle = (f"<details><summary>Als Tabelle</summary><table><tr><th>Kapitel</th><th>Thema</th><th>Stufe</th>"
               f"<th>Klausurrel.</th><th>Zuletzt</th></tr>{zeilen}</table></details>")
    return "".join(teile) + f'<div class="legende">{legende}<span style="--c:transparent">↻ auffrischen</span></div>' + tabelle


def _fehlertypen(f) -> str:
    if not f.fehlertypen:
        return '<p class="leer">Noch keine Fehler protokolliert.</p>'
    maxi = max(f.fehlertypen.values())
    return "".join(f'<div class="hbar" title="{escape(t)}: {n}"><span>{escape(t)}</span>'
                   f'<div class="b"><div style="width:{n / maxi * 100:.1f}%"></div></div><span class="v">{n}</span></div>'
                   for t, n in sorted(f.fehlertypen.items(), key=lambda kv: -kv[1]))


def _kalender(kurs: Kurs, heute: date, wochen: int = 16) -> str:
    zaehler = Counter(als_datum(e["ts"]) for e in kurs.ereignisse())
    start = heute - timedelta(days=heute.weekday()) - timedelta(weeks=wochen - 1)
    zelle, gap = 12, 3
    rects = []
    for w in range(wochen):
        for d in range(7):
            tag = start + timedelta(weeks=w, days=d)
            if tag > heute:
                continue
            n = zaehler.get(tag, 0)
            stufe = 0 if n == 0 else 1 if n <= 2 else 2 if n <= 5 else 3 if n <= 10 else 4
            rects.append(f'<rect x="{30 + w * (zelle + gap)}" y="{d * (zelle + gap)}" width="{zelle}" height="{zelle}" rx="2" '
                         f'style="fill:var(--h{stufe})"><title>{tag:%a %d.%m.}: {n} Einträge</title></rect>')
    labels = "".join(f'<text x="0" y="{d * (zelle + gap) + 10}">{t}</text>' for d, t in ((0, "Mo"), (2, "Mi"), (4, "Fr")))
    breite = 30 + wochen * (zelle + gap)
    legende = "".join(f'<span style="--c:var(--h{i})">{t}</span>' for i, t in enumerate(["0", "1–2", "3–5", "6–10", ">10"]))
    return (f'<svg viewBox="0 0 {breite} {7 * (zelle + gap)}" width="100%" style="max-width:{breite * 1.4:.0f}px" '
            f'role="img" aria-label="Lernaktivität der letzten {wochen} Wochen">{labels}{"".join(rects)}</svg>'
            f'<div class="legende">Einträge pro Tag: {legende}</div>')


def _kurs_html(kurs: Kurs, heute: date) -> str:
    f = fortschritt(kurs, heute)
    aufgaben = aufgaben_stand(kurs, heute)
    countdown = (f"Klausur am {f.klausur_datum:%d.%m.%Y} · noch {f.tage_bis_klausur} Tage" if f.klausur_datum
                 else "Klausurdatum fehlt in kurs.yaml")
    tiles = "".join([
        _tile(_pz(f.abdeckung), "Abdeckung (gewichtet)", f.abdeckung),
        _tile(_pz(f.beherrschung), "Beherrschung (Ø Stufe/4)", f.beherrschung),
        _tile(f"{f.aufgaben_selbst}/{f.aufgaben_gesamt}", "Aufgaben selbst gelöst",
              f.aufgaben_selbst / f.aufgaben_gesamt if f.aufgaben_gesamt else 0),
        _tile(str(f.fehler_offen), f"offene Fehler · {f.fehler_behoben} behoben"),
        _tile(str(len(f.lerntage)), f"Lerntage · {f.sitzungen} Sitzungen · {f.fragen} Fragen"),
    ])
    if f.kalibrierung["sicher_gesamt"]:
        k = f.kalibrierung
        tiles += _tile(f"{k['sicher_falsch']}/{k['sicher_gesamt']}", "„Sicher“, aber falsch (Kalibrierung)")

    emp = empfehlungen(kurs, heute)
    emp_html = ("<ol class='liste'>" + "".join(f"<li>{escape(e.text)}</li>" for e in emp) + "</ol>") if emp \
        else '<p class="leer">Nichts fällig.</p>'
    offen = offene_fehler(kurs.ereignisse())
    fehler_html = ("<ul class='liste'>" + "".join(
        f"<li><span class='fid'>{escape(fid)}</span> [{escape(e.get('fehlertyp', ''))}] "
        f"{escape(', '.join(e.get('themen', [])))}: {escape(e.get('kurz', ''))}</li>" for fid, e in offen.items()) + "</ul>") \
        if offen else '<p class="leer">Keine offenen Fehler.</p>'
    faellig = [a for a in aufgaben.values() if a.faellig]
    redo_html = ("<ul class='liste'>" + "".join(
        f"<li>{escape(a.id)} – {escape(a.titel)}: {a.faellig:%d.%m.}{' (fällig)' if a.faellig <= heute else ''}</li>"
        for a in sorted(faellig, key=lambda a: a.faellig)) + "</ul>") if faellig else '<p class="leer">Keine geplant.</p>'
    prognose = f"<p class='countdown'>{escape(f.prognose)}</p>" if f.prognose else ""

    return f"""<section class="kurs">
<div class="kopf"><h2>{escape(kurs.name)}</h2><span class="countdown">{escape(countdown)}</span></div>
{prognose}<div class="tiles">{tiles}</div>
<section class="box"><h3>Themenlandkarte (Mastery-Stufe je Thema)</h3>{_themenkarte(kurs, heute)}</section>
<div class="grid2">
<section class="box"><h3>Empfohlen als Nächstes</h3>{emp_html}</section>
<section class="box"><h3>Nachrechnen ohne Hilfe – Termine</h3>{redo_html}</section>
<section class="box"><h3>Offene Fehler</h3>{fehler_html}</section>
<section class="box"><h3>Fehlertypen (alle)</h3>{_fehlertypen(f)}</section>
</div>
<section class="box" style="margin-top:20px"><h3>Lernkalender</h3>{_kalender(kurs, heute)}</section>
</section>"""


def erzeuge(repo: Repo, heute: date | None = None, ziel: Path | None = None) -> Path:
    heute = heute or date.today()
    aktiv = repo.config.get("aktiver_kurs")
    ids = sorted(repo.kurs_ids(), key=lambda i: (i != aktiv, i))
    inhalt = "".join(_kurs_html(repo.kurs(i), heute) for i in ids) or '<p class="leer">Noch keine Kurse.</p>'
    seite = f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Lernecke Dashboard</title><style>{_CSS}</style></head>
<body><button class="theme" type="button">Hell/Dunkel</button><main>
<h1>Lernecke</h1><p class="sub">Stand {heute:%d.%m.%Y} · erzeugt mit <code>lern dashboard</code></p>
{inhalt}</main><script>{_JS}</script></body></html>"""
    ziel = ziel or repo.wurzel / "ausgabe" / "dashboard.html"
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(seite, encoding="utf-8", newline="\n")
    return ziel
