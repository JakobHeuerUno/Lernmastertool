"""LERNECKE einrichten – plattformübergreifend (Windows, macOS, Linux), idempotent, nur Standardbibliothek.

Normalerweise nicht direkt aufrufen, sondern über
    Windows:        powershell -ExecutionPolicy Bypass -File .\\setup.ps1
    macOS / Linux:  sh setup.sh
Die Wrapper suchen ein passendes Python (>= 3.11) und starten dann dieses Skript damit.
Der Launcher (`lern` / `lern.cmd`) ruft es beim Sessionstart automatisch auf, wenn die .venv fehlt
oder kaputt ist (z. B. Ordner von einem anderen Rechner/Betriebssystem kopiert).

Was passiert:
  1. Betriebssystem erkennen, Python-Version prüfen
  2. .venv prüfen; fehlt sie, gehört sie zu einem anderen OS/Rechner oder ist kaputt -> neu anlegen
  3. Paket `lern` editierbar installieren (nur wenn sich pyproject.toml geändert hat)
  4. .claude/skills -> .agents/skills verlinken (Windows: Junction, sonst Symlink)
  5. Schnelltest: `lern pruefen`
"""

import argparse
import hashlib
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

MIN_PY = (3, 11)
WURZEL = Path(__file__).resolve().parent
VENV = WURZEL / ".venv"
STEMPEL = VENV / ".lernecke-installiert"
STILL = False


def log(text: str) -> None:
    # Fortschritt immer auf stderr: im Hook-Modus gehört stdout dem JSON des Hooks.
    if not STILL:
        print(text, file=sys.stderr, flush=True)


def fehler(text: str) -> "None":
    print(f"FEHLER: {text}", file=sys.stderr, flush=True)
    sys.exit(1)


def os_name() -> str:
    s = platform.system()
    return {"Darwin": "macos", "Windows": "windows"}.get(s, "linux")


def venv_python(os_id: str) -> Path:
    return VENV / ("Scripts/python.exe" if os_id == "windows" else "bin/python")


def python_hinweis(os_id: str) -> str:
    if os_id == "windows":
        return ("Python >= 3.11 installieren: `winget install Python.Python.3.12` "
                "oder https://www.python.org/downloads/ (Haken bei 'Add python.exe to PATH').")
    if os_id == "macos":
        return ("Python >= 3.11 installieren: `brew install python@3.12` (Homebrew: https://brew.sh) "
                "oder Installer von https://www.python.org/downloads/macos/. "
                "Das vorinstallierte /usr/bin/python3 (3.9) ist zu alt.")
    return "Python >= 3.11 + venv installieren, z. B. `sudo apt install python3 python3-venv` (Debian/Ubuntu)."


def venv_ok(os_id: str) -> bool:
    """Läuft das venv-Python auf diesem Rechner und hat es die nötige Version?"""
    py = venv_python(os_id)
    fremd = VENV / ("bin/python" if os_id == "windows" else "Scripts/python.exe")
    if not py.exists():
        if fremd.exists():
            log(".venv stammt von einem anderen Betriebssystem -> wird neu angelegt")
        return False
    try:
        r = subprocess.run([str(py), "-c", "import sys; print(sys.version_info[:2] >= %r)" % (MIN_PY,)],
                           capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        log(".venv ist auf diesem Rechner nicht lauffähig -> wird neu angelegt")
        return False
    if r.returncode != 0 or r.stdout.strip() != "True":
        log(".venv ist kaputt oder zu alt -> wird neu angelegt")
        return False
    return True


def lege_venv_an(os_id: str) -> None:
    if VENV.exists() or VENV.is_symlink():
        shutil.rmtree(VENV, ignore_errors=True)
        if VENV.exists():
            fehler(f"Konnte die alte .venv nicht löschen ({VENV}). Ist noch ein Programm daraus offen? "
                   "Bitte schließen und erneut versuchen.")
    log(f"Erzeuge .venv mit Python {platform.python_version()} ({sys.executable}) ...")
    try:
        import venv  # noqa: F401
        import ensurepip  # noqa: F401
    except ImportError:
        fehler("Diesem Python fehlt das Modul venv/ensurepip. " + python_hinweis(os_id))
    r = subprocess.run([sys.executable, "-m", "venv", str(VENV)], stdout=sys.stderr)
    if r.returncode != 0 or not venv_python(os_id).exists():
        fehler(".venv konnte nicht erzeugt werden. " + python_hinweis(os_id))


def installiere(os_id: str, erzwingen: bool) -> None:
    soll = hashlib.sha1((WURZEL / "pyproject.toml").read_bytes()).hexdigest()
    py = str(venv_python(os_id))
    if not erzwingen and STEMPEL.is_file() and STEMPEL.read_text().strip() == soll:
        r = subprocess.run([py, "-c", "import lern, yaml, pymupdf, genanki, pytest"], capture_output=True)
        if r.returncode == 0:
            log("Pakete sind aktuell.")
            return
    log("Installiere Paket `lern` + Abhängigkeiten (PyYAML, PyMuPDF, genanki, pytest) ...")
    pip = [py, "-m", "pip", "--disable-pip-version-check"]
    subprocess.run(pip + ["install", "-q", "--upgrade", "pip"], cwd=WURZEL, stdout=sys.stderr)  # Fehlschlag egal
    r = subprocess.run(pip + ["install", "-q", "-e", ".[test]"], cwd=WURZEL, stdout=sys.stderr)
    if r.returncode != 0:
        fehler("pip install ist fehlgeschlagen (Internetverbindung? Proxy?). Ausgabe oben prüfen, "
               "dann Setup erneut starten.")
    STEMPEL.write_text(soll + "\n")


def ist_link(p: Path) -> bool:
    if p.is_symlink():
        return True
    isjunction = getattr(os.path, "isjunction", None)  # Python >= 3.12
    return bool(isjunction and isjunction(p))


def verlinke_skills(os_id: str) -> None:
    """Claude Code liest Skills aus .claude/skills, Codex aus .agents/skills."""
    link = WURZEL / ".claude" / "skills"
    ziel = WURZEL / ".agents" / "skills"
    if (link / "aufgabe" / "SKILL.md").is_file():
        return
    if ist_link(link):
        log(".claude/skills zeigt ins Leere (z. B. von anderem Rechner kopiert) -> neu verlinken")
        if os_id == "windows":
            os.rmdir(link)  # entfernt nur die Junction, nicht das Ziel
        else:
            link.unlink()
    elif link.exists():
        if link.is_dir() and not any(link.iterdir()):
            link.rmdir()
        else:
            log("WARNUNG: .claude/skills existiert als echter Ordner/Datei – nicht angefasst. "
                "Bitte löschen und Setup erneut starten, damit es auf .agents/skills zeigt.")
            return
    link.parent.mkdir(exist_ok=True)
    if os_id == "windows":
        # Junction braucht (anders als Symlinks) keine Admin-Rechte/Entwicklermodus
        r = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(ziel)], capture_output=True)
        if r.returncode != 0:
            meldung = r.stderr.decode("oem", errors="replace").strip()
            log(f"WARNUNG: Junction .claude/skills konnte nicht angelegt werden: {meldung}")
            return
    else:
        link.symlink_to(Path("..") / ".agents" / "skills", target_is_directory=True)
    log(".claude/skills -> .agents/skills verlinkt")


def ausfuehrbar_machen(os_id: str) -> None:
    """Falls das Repo ohne Dateirechte kopiert wurde (ZIP, USB-Stick, Cloud)."""
    if os_id == "windows":
        return
    for name in ("lern", "setup.sh"):
        p = WURZEL / name
        if p.is_file():
            p.chmod(p.stat().st_mode | 0o111)


def main() -> int:
    global STILL
    ap = argparse.ArgumentParser(description="LERNECKE einrichten (Windows/macOS/Linux)")
    ap.add_argument("--still", action="store_true", help="nur Fehler ausgeben (Hook-Modus)")
    ap.add_argument("--neu", action="store_true", help=".venv komplett neu anlegen")
    ap.add_argument("--tests", action="store_true", help="zum Schluss die Testsuite laufen lassen")
    args = ap.parse_args()
    STILL = args.still

    os_id = os_name()
    log(f"LERNECKE-Setup · {platform.system()} {platform.release()} ({platform.machine()}) · "
        f"Python {platform.python_version()}")
    if sys.version_info[:2] < MIN_PY:
        fehler(f"Python {platform.python_version()} ist zu alt. " + python_hinweis(os_id))

    neu = args.neu or not venv_ok(os_id)
    if neu:
        lege_venv_an(os_id)
    installiere(os_id, erzwingen=neu)
    verlinke_skills(os_id)
    ausfuehrbar_machen(os_id)

    py = str(venv_python(os_id))
    r = subprocess.run([py, "-m", "lern", "pruefen"], cwd=WURZEL, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        log("Hinweis: `lern pruefen` meldet Probleme in den Kursdaten:\n" + (r.stdout + r.stderr).strip())
    if args.tests:
        t = subprocess.run([py, "-m", "pytest", "-q"], cwd=WURZEL, stdout=sys.stderr)
        if t.returncode != 0:
            fehler("Tests fehlgeschlagen.")

    aufruf = r".\lern.cmd" if os_id == "windows" else "./lern"
    log(f"\nFertig. Lerntool aufrufen mit:  {aufruf} brief"
        + ("   (in Git Bash: ./lern brief)" if os_id == "windows" else ""))
    log("Claude Code / Codex im Repo-Ordner starten. Falls die Skills (/lernen, /aufgabe, ...) "
        "noch fehlen: Session einmal neu starten.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
