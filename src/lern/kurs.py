"""Kurse anlegen und auflisten."""

from __future__ import annotations

import re
import shutil

from lern.daten import Kurs, LernFehler, Repo, lade_yaml, speichere_yaml


def neuer_kurs(repo: Repo, kurs_id: str, name: str, kuerzel: str | None = None) -> Kurs:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", kurs_id):
        raise LernFehler("Kurs-ID nur aus a–z, 0–9 und '-' (z. B. 'waerme-stoffuebertragung')")
    ziel = repo.kurse_dir / kurs_id
    if ziel.exists() and any(ziel.iterdir()):
        raise LernFehler(f"Kurs-Ordner existiert bereits: {ziel}")
    vorlage = repo.wurzel / "vorlagen" / "kurs"
    if not vorlage.is_dir():
        raise LernFehler(f"Vorlage fehlt: {vorlage}")
    shutil.copytree(vorlage, ziel, dirs_exist_ok=True)
    meta = lade_yaml(ziel / "kurs.yaml", {}) or {}
    meta["id"] = kurs_id
    meta["name"] = name
    meta["kuerzel"] = kuerzel or "".join(w[0] for w in kurs_id.split("-"))[:4]
    speichere_yaml(ziel / "kurs.yaml", meta)
    if not repo.config.get("aktiver_kurs"):
        repo.setze_config("aktiver_kurs", kurs_id)
    return Kurs(repo, ziel)


def setze_aktiv(repo: Repo, kurs_id: str) -> Kurs:
    kurs = repo.kurs(kurs_id)
    repo.setze_config("aktiver_kurs", kurs_id)
    return kurs
