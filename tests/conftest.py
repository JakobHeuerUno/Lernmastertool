import json
import shutil
from pathlib import Path

import pytest

from lern.daten import Repo, speichere_yaml
from lern.kurs import neuer_kurs

WURZEL = Path(__file__).resolve().parents[1]


@pytest.fixture
def repo(tmp_path, monkeypatch):
    shutil.copytree(WURZEL / "vorlagen", tmp_path / "vorlagen")
    (tmp_path / "lern.yaml").write_text("aktiver_kurs: null\n", encoding="utf-8")
    (tmp_path / "profil").mkdir()
    (tmp_path / "profil" / "lernprofil.md").write_text(
        "# Lernprofil\n\n## Kurzprofil\n- versteht Analogien gut\n\n## Details\nx\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LERN_ROOT", raising=False)
    return Repo(tmp_path)


@pytest.fixture
def kurs(repo):
    k = neuer_kurs(repo, "demo", "Demo-Kurs", "dem")
    speichere_yaml(k.pfad / "themen.yaml", {"themen": [
        {"id": "a", "titel": "Thema A", "kapitel": "K1", "klausurrelevanz": 3},
        {"id": "b", "titel": "Thema B", "kapitel": "K1", "voraussetzungen": ["a"], "klausurrelevanz": 2},
        {"id": "c", "titel": "Thema C", "kapitel": "K2", "klausurrelevanz": 1},
    ]})
    speichere_yaml(k.pfad / "aufgaben.yaml", {"aufgaben": [
        {"id": "ue1-a1", "titel": "Wand", "themen": ["a"]},
        {"id": "ue1-a2", "titel": "Rohr", "themen": ["b"]},
    ]})
    return k


def schreibe(kurs, *ereignisse):
    with kurs.ereignis_datei.open("a", encoding="utf-8") as f:
        for e in ereignisse:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
