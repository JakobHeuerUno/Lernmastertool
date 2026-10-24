# LERNECKE einrichten auf Windows (idempotent).
# Aufruf im Repo-Ordner:  powershell -ExecutionPolicy Bypass -File .\setup.ps1   [-Neu] [-Tests]
# -Auto: vom Launcher beim Sessionstart aufgerufen -> still, installiert kein System-Python.
param([switch]$Auto, [switch]$Neu, [switch]$Tests)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Finde-Python {
    # py-Launcher zuerst; "python"/"python3" koennen der Microsoft-Store-Platzhalter sein -> Version testen
    foreach ($k in @("py -3.13", "py -3.12", "py -3.11", "py -3", "python", "python3")) {
        $teile = $k -split " "
        $exe = $teile[0]; $rest = @($teile | Select-Object -Skip 1)
        if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) { continue }
        try {
            & $exe @rest -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" 2>$null | Out-Null
            if ($LASTEXITCODE -eq 0) { return $k }
        } catch {}
    }
    return $null
}

$py = Finde-Python
if (-not $py -and -not $Auto -and (Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Host "Kein Python >= 3.11 gefunden - installiere Python 3.12 ueber winget ..."
    winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
    # PATH der laufenden Sitzung auffrischen
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "User") + ";" + [Environment]::GetEnvironmentVariable("Path", "Machine")
    $py = Finde-Python
}
if (-not $py) {
    [Console]::Error.WriteLine("FEHLER: Kein Python >= 3.11 gefunden. 'winget install Python.Python.3.12' oder https://www.python.org/downloads/ (Haken bei 'Add python.exe to PATH'), danach erneut .\setup.ps1")
    exit 2
}

$argsPy = @()
if ($Auto) { $argsPy += "--still" }
if ($Neu) { $argsPy += "--neu" }
if ($Tests) { $argsPy += "--tests" }
$teile = $py -split " "
$exe = $teile[0]; $rest = @($teile | Select-Object -Skip 1)
& $exe @rest einrichten.py @argsPy
exit $LASTEXITCODE
