"""Originalmaterial teilen ohne Git: packen (Zips für die Cloud) und holen (Download → lern abgleich).

Das Material bleibt aus urheberrechtlichen Gründen und wegen der Größe außerhalb des Repos. Der Link steht lokal in
`lern.lokal.yaml` (git-ignoriert) oder wird beim Aufruf übergeben – nie in versionierten Dateien.
Unterstützt: Sciebo/Nextcloud-Freigaben (auch mit Passwort, Ordner oder Datei), OneDrive, Google Drive (Datei
oder Ordner, Freigabe „Jeder mit dem Link“), direkte URLs.
"""

from __future__ import annotations

import base64
import html
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from lern.daten import Kurs, LernFehler, Repo, lade_yaml

LOKAL = "lern.lokal.yaml"
BLOCK = 1 << 20


# ------------------------------------------------------------------ packen

def packen(kurs: Kurs, mit_medien: bool = True) -> list[Path]:
    """ausgabe/<kurs>-material.zip (+ -medien.zip). Ohne Kompression: PDFs/Videos sind schon komprimiert."""
    ziel_dir = kurs.repo.wurzel / "ausgabe"
    ziel_dir.mkdir(exist_ok=True)
    teile = [("material", kurs.pfad / "material")]
    if mit_medien:
        teile.append(("medien", kurs.pfad / "medien"))
    erzeugt = []
    for name, ordner in teile:
        dateien = [p for p in sorted(ordner.rglob("*")) if p.is_file() and not p.name.startswith(".")
                   and "archiv" not in p.relative_to(ordner).parts[:1]] if ordner.is_dir() else []
        if not dateien:
            continue
        ziel = ziel_dir / f"{kurs.id}-{name}.zip"
        with zipfile.ZipFile(ziel, "w", zipfile.ZIP_STORED, allowZip64=True) as z:
            for p in dateien:
                z.write(p, p.relative_to(kurs.pfad).as_posix())
        erzeugt.append(ziel)
    return erzeugt


# ------------------------------------------------------------------ Links → Downloads

def lokale_links(repo: Repo, kurs: Kurs) -> tuple[list[str], str | None]:
    cfg = lade_yaml(repo.wurzel / LOKAL, {}) or {}
    eintrag = (cfg.get("material") or {}).get(kurs.id) or {}
    links = eintrag.get("links") or []
    return [links] if isinstance(links, str) else list(links), eintrag.get("passwort")


def _nextcloud(url: str) -> tuple[str, str] | None:
    """https://<host>/s/<token>[/download] → (Basis, Token) für Sciebo/Nextcloud-Freigaben."""
    m = re.match(r"(https?://[^/]+(?:/index\.php)?)/s/([A-Za-z0-9]+)", url)
    return (m.group(1).replace("/index.php", ""), m.group(2)) if m else None


def direkte_url(url: str) -> str:
    """Freigabe-Link → direkt ladbare URL (ohne Passwort)."""
    if nc := _nextcloud(url):
        return f"{nc[0]}/s/{nc[1]}/download"
    if m := re.search(r"drive\.google\.com/(?:file/d/|open\?id=|uc\?(?:.*&)?id=)([\w-]+)", url):
        return f"https://drive.usercontent.google.com/download?id={m.group(1)}&export=download&confirm=t"
    if re.search(r"(1drv\.ms|onedrive\.live\.com|sharepoint\.com)", url):
        if "sharepoint.com" in url:
            return url + ("&" if "?" in url else "?") + "download=1"
        kodiert = base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")
        return f"https://api.onedrive.com/v1.0/shares/u!{kodiert}/root/content"
    return url


def _oeffnen(url: str, auth: tuple[str, str] | None = None, methode: str = "GET", daten: bytes | None = None,
             kopf: dict | None = None):
    req = urllib.request.Request(url, data=daten, method=methode, headers={"User-Agent": "lern", **(kopf or {})})
    if auth:
        token = base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
        req.add_header("Authorization", f"Basic {token}")
    return urllib.request.urlopen(req, timeout=60)


def _dateiname(r, url: str, ersatz: str) -> str:
    cd = r.headers.get("Content-Disposition") or ""
    m = re.search(r"filename\*?=(?:UTF-8'')?\"?([^\";]+)", cd)
    return urllib.parse.unquote(m.group(1)) if m else (Path(urllib.parse.urlparse(url).path).name or ersatz)


def _laden(url: str, ziel_dir: Path, name: str | None = None, auth: tuple[str, str] | None = None) -> Path:
    """Streamt url nach ziel_dir/<name>; überspringt, wenn die Datei schon vollständig da ist."""
    with _oeffnen(url, auth) as r:
        if "drive.usercontent.google.com" in url and "text/html" in (r.headers.get("Content-Type") or ""):
            # große Drive-Dateien: Hinweisseite „Virenscan nicht möglich“ – Formular enthält die echte Download-URL
            seite = r.read().decode("utf-8", "replace")
            if m := re.search(r'<form[^>]*action="([^"]+)"', seite):
                felder = dict(re.findall(r'<input[^>]*name="([^"]+)"[^>]*value="([^"]*)"', seite))
                return _laden(html.unescape(m.group(1)) + "?" + urllib.parse.urlencode(felder), ziel_dir, name)
            raise LernFehler("Google Drive liefert keine Datei – Freigabe auf „Jeder, der über den Link verfügt“ stellen.")
        ziel = ziel_dir / (name or _dateiname(r, url, "download.zip"))
        gesamt = int(r.headers.get("Content-Length") or 0)
        if ziel.is_file() and gesamt and ziel.stat().st_size == gesamt:
            return ziel
        ziel.parent.mkdir(parents=True, exist_ok=True)
        teil = ziel.with_name(ziel.name + ".teil")
        print(f"Lade {ziel.name} …", file=sys.stderr)
        geladen, gemeldet = 0, 0
        with teil.open("wb") as f:
            for block in iter(lambda: r.read(BLOCK), b""):
                f.write(block)
                geladen += len(block)
                if geladen - gemeldet >= 100 * BLOCK:
                    gemeldet = geladen
                    von = f" / {gesamt / BLOCK:.0f}" if gesamt else ""
                    print(f"  … {geladen / BLOCK:.0f}{von} MB", file=sys.stderr)
    teil.replace(ziel)
    return ziel


def _nextcloud_dateien(basis: str, token: str, passwort: str) -> list[str]:
    """Pfade aller Dateien einer passwortgeschützten Freigabe (WebDAV PROPFIND, rekursiv)."""
    dav = f"{basis}/public.php/webdav"
    gefunden, offen = [], [""]
    while offen:
        pfad = offen.pop()
        with _oeffnen(f"{dav}/{urllib.parse.quote(pfad)}", (token, passwort), "PROPFIND", kopf={"Depth": "1"}) as r:
            baum = ET.fromstring(r.read())
        for resp in baum.findall("{DAV:}response"):
            href = urllib.parse.unquote(resp.findtext("{DAV:}href") or "")
            rel = href.split("/public.php/webdav", 1)[-1].strip("/")
            if rel == pfad.strip("/"):
                continue
            ist_ordner = resp.find(".//{DAV:}collection") is not None
            (offen if ist_ordner else gefunden).append(rel)
    return gefunden or [""]  # Datei-Freigabe: die Freigabe selbst ist die Datei


def _drive_ordner(ordner_id: str, pfad: str = "") -> list[tuple[str, str]]:
    """(Datei-ID, relativer Pfad) aller Dateien eines öffentlich geteilten Drive-Ordners, rekursiv."""
    try:
        with _oeffnen(f"https://drive.google.com/embeddedfolderview?id={ordner_id}") as r:
            seite = r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        raise LernFehler(f"Drive-Ordner nicht lesbar (HTTP {e.code}) – Freigabe auf „Jeder, der über den Link "
                         "verfügt“ stellen.") from e
    dateien = []
    for href, titel in re.findall(r'<a href="([^"]+)"[^>]*>.*?flip-entry-title">([^<]+)<', seite, flags=re.S):
        rel = f"{pfad}{html.unescape(titel).strip()}"
        if m := re.search(r"/folders/([\w-]+)", href):
            dateien += _drive_ordner(m.group(1), rel + "/")
        elif m := re.search(r"/file/d/([\w-]+)", href):
            dateien.append((m.group(1), rel))
    return dateien


def holen(repo: Repo, kurs: Kurs, links: list[str], passwort: str | None = None) -> list[Path]:
    """Lädt alle Links nach .cache/material/<kurs>/ und gibt die lokalen Dateien zurück (für lern abgleich)."""
    if not links:
        raise LernFehler(f"Kein Link angegeben und keiner in {LOKAL} (material: {{{kurs.id}: {{links: [...]}}}}).")
    cache = repo.wurzel / ".cache" / "material" / kurs.id
    dateien = []
    for nr, link in enumerate(links, 1):
        if Path(link).exists():  # lokale Datei/Ordner (z. B. USB-Stick, gemeinsamer Netzordner)
            dateien.append(Path(link))
            continue
        if m := re.search(r"drive\.google\.com/drive/(?:u/\d+/)?folders/([\w-]+)", link):
            for datei_id, rel in _drive_ordner(m.group(1)):
                url = f"https://drive.usercontent.google.com/download?id={datei_id}&export=download&confirm=t"
                dateien.append(_laden(url, cache / str(nr) / Path(rel).parent, Path(rel).name))
            continue
        nc = _nextcloud(link)
        if nc and passwort:
            for rel in _nextcloud_dateien(nc[0], nc[1], passwort):
                url = f"{nc[0]}/public.php/webdav/{urllib.parse.quote(rel)}"
                ziel = cache / str(nr) / Path(rel).parent if rel else cache / str(nr)
                dateien.append(_laden(url, ziel, Path(rel).name or None, (nc[1], passwort)))
            continue
        dateien.append(_laden(direkte_url(link), cache / str(nr)))
    return dateien
