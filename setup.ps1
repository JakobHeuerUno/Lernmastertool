# LERNECKE einrichten (idempotent): Python-Umgebung, Paket "lern", Skill-Junction für Claude Code.
# Aufruf im Repo-Ordner:  powershell -ExecutionPolicy Bypass -File .\setup.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Erzeuge .venv ..."
    python -m venv .venv
}
& .venv\Scripts\python.exe -m pip install --disable-pip-version-check -q -e ".[test]"

# Claude Code liest Skills aus .claude\skills, Codex aus .agents\skills -> Junction (braucht keine Admin-Rechte)
$link = ".claude\skills"
if (-not (Test-Path $link)) {
    New-Item -ItemType Directory -Force ".claude" | Out-Null
    cmd /c mklink /J "$link" ".agents\skills" | Out-Null
    Write-Host "Junction $link -> .agents\skills angelegt"
}

& .venv\Scripts\python.exe -m lern kurs liste
Write-Host "Fertig. Test: .\lern.cmd brief"
