"""Pfade, Dateiformate und Ereignislog."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import yaml

ERGEBNISSE = ("selbst", "hinweise", "erklaert", "falsch")
ARTEN = ("aufgabe", "abruf", "karte", "klausur")
FEHLERTYPEN = ("konzept", "ansatz", "formel", "einheit", "rechnung", "lesefehler", "sonstiges")
MATERIALTYPEN = ("folien", "skript", "uebungen", "loesungen", "altklausuren", "studydrive", "sonstiges")


class LernFehler(Exception):
    """Fehler mit verständlicher Meldung für die CLI."""


def finde_wurzel(start: Path | None = None) -> Path:
    if os.environ.get("LERN_ROOT"):
        return Path(os.environ["LERN_ROOT"]).resolve()
    p = (start or Path.cwd()).resolve()
    for kandidat in (p, *p.parents):
        if (kandidat / "lern.yaml").is_file():
            return kandidat
    raise LernFehler("Keine LERNECKE gefunden (lern.yaml fehlt). Im Repo-Ordner ausführen oder LERN_ROOT setzen.")


def lade_yaml(pfad: Path, standard=None):
    if not pfad.is_file():
        return standard
    with pfad.open(encoding="utf-8") as f:
        daten = yaml.safe_load(f)
    return standard if daten is None else daten


def speichere_yaml(pfad: Path, daten) -> None:
    pfad.parent.mkdir(parents=True, exist_ok=True)
    with pfad.open("w", encoding="utf-8", newline="\n") as f:
        yaml.safe_dump(daten, f, allow_unicode=True, sort_keys=False, width=120)


def als_datum(wert) -> date | None:
    if wert is None or wert == "":
        return None
    if isinstance(wert, datetime):
        return wert.date()
    if isinstance(wert, date):
        return wert
    return date.fromisoformat(str(wert)[:10])


def jetzt() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


@dataclass
class Repo:
    wurzel: Path

    @classmethod
    def finde(cls, start: Path | None = None) -> "Repo":
        return cls(finde_wurzel(start))

    @property
    def config(self) -> dict:
        return lade_yaml(self.wurzel / "lern.yaml", {}) or {}

    def setze_config(self, schluessel: str, wert) -> None:
        cfg = self.config
        cfg[schluessel] = wert
        speichere_yaml(self.wurzel / "lern.yaml", cfg)

    @property
    def kurse_dir(self) -> Path:
        return self.wurzel / "kurse"

    def kurs_ids(self) -> list[str]:
        if not self.kurse_dir.is_dir():
            return []
        return sorted(p.name for p in self.kurse_dir.iterdir() if (p / "kurs.yaml").is_file())

    def kurs(self, kurs_id: str | None = None) -> "Kurs":
        kurs_id = kurs_id or self.config.get("aktiver_kurs")
        if not kurs_id:
            ids = self.kurs_ids()
            if len(ids) == 1:
                kurs_id = ids[0]
            else:
                raise LernFehler("Kein aktiver Kurs. `lern kurs aktiv <id>` oder --kurs angeben.")
        pfad = self.kurse_dir / kurs_id
        if not (pfad / "kurs.yaml").is_file():
            raise LernFehler(f"Kurs '{kurs_id}' nicht gefunden. Vorhanden: {', '.join(self.kurs_ids()) or '–'}")
        return Kurs(self, pfad)


@dataclass
class Kurs:
    repo: Repo
    pfad: Path

    @property
    def id(self) -> str:
        return self.pfad.name

    @property
    def meta(self) -> dict:
        return lade_yaml(self.pfad / "kurs.yaml", {}) or {}

    @property
    def name(self) -> str:
        return self.meta.get("name") or self.id

    @property
    def kuerzel(self) -> str:
        return self.meta.get("kuerzel") or self.id[:3]

    @property
    def themen(self) -> list[dict]:
        daten = lade_yaml(self.pfad / "themen.yaml", {}) or {}
        return daten.get("themen") or []

    @property
    def aufgaben(self) -> list[dict]:
        daten = lade_yaml(self.pfad / "aufgaben.yaml", {}) or {}
        return daten.get("aufgaben") or []

    @property
    def lernstand(self) -> Path:
        return self.pfad / "lernstand"

    @property
    def ereignis_datei(self) -> Path:
        return self.lernstand / "ereignisse.jsonl"

    def ereignisse(self) -> list[dict]:
        datei = self.ereignis_datei
        if not datei.is_file():
            return []
        liste = []
        for nr, zeile in enumerate(datei.read_text(encoding="utf-8").splitlines(), 1):
            zeile = zeile.strip()
            if not zeile:
                continue
            try:
                liste.append(json.loads(zeile))
            except json.JSONDecodeError as e:
                raise LernFehler(f"{datei}:{nr}: ungültiges JSON ({e})") from e
        return liste

    def schreibe_ereignis(self, ereignis: dict) -> dict:
        ereignis = {"ts": jetzt(), **ereignis}
        ereignis = {k: v for k, v in ereignis.items() if v not in (None, "", [])}
        self.lernstand.mkdir(parents=True, exist_ok=True)
        with self.ereignis_datei.open("a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(ereignis, ensure_ascii=False) + "\n")
        return ereignis

    def anki_stats(self) -> dict:
        datei = self.lernstand / "anki-stats.json"
        if not datei.is_file():
            return {}
        return json.loads(datei.read_text(encoding="utf-8")).get("karten", {})

    def themen_index(self) -> dict[str, dict]:
        return {t["id"]: t for t in self.themen if "id" in t}
