@echo off
rem Launcher fuer das Lerntool unter Windows (cmd/PowerShell):  .\lern.cmd <befehl>
rem Fehlt die .venv oder passt sie nicht zu diesem Rechner, wird sie zuerst automatisch eingerichtet.
setlocal
if not defined LERN_ROOT set "LERN_ROOT=%~dp0."
set "PY=%~dp0.venv\Scripts\python.exe"
"%PY%" -c "import lern, yaml" >nul 2>&1
if not errorlevel 1 goto los

echo LERNECKE: Python-Umgebung fehlt oder passt nicht zu diesem Rechner - richte sie ein (einmalig, ca. 1 Minute) ... 1>&2
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1" -Auto 1>&2
"%PY%" -c "import lern, yaml" >nul 2>&1
if not errorlevel 1 goto los

set "MELDUNG=LERNECKE ist auf diesem Rechner noch nicht eingerichtet und die automatische Einrichtung ist fehlgeschlagen, meist fehlt Python 3.11+. Bitte im Repo-Ordner ausfuehren: powershell -ExecutionPolicy Bypass -File setup.ps1 - danach Session neu starten. Bis dahin STAND.md lesen."
if /i "%~1 %~2"=="brief --hook" (
  echo {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "%MELDUNG%"}}
  exit /b 0
)
echo %MELDUNG% 1>&2
exit /b 1

:los
"%PY%" -m lern %*
