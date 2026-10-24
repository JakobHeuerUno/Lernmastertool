#!/bin/sh
# LERNECKE einrichten auf macOS / Linux (funktioniert auch in Git Bash unter Windows).
# Aufruf im Repo-Ordner:  sh setup.sh            (Optionen: --neu, --tests)
# --auto: vom Launcher beim Sessionstart aufgerufen -> still, installiert kein System-Python.
set -e
cd "$(dirname "$0")"

AUTO=0
for a in "$@"; do
    case "$a" in --auto) AUTO=1 ;; esac
done

# Erstes Python >= 3.11 finden (Homebrew-Pfade explizit, weil PATH in GUI-Apps oft unvollständig ist)
finde_python() {
    for c in python3.13 python3.12 python3.11 python3 python \
             /opt/homebrew/bin/python3 /usr/local/bin/python3 \
             /Library/Frameworks/Python.framework/Versions/Current/bin/python3 \
             "$HOME/.local/bin/python3" "py -3"; do
        # shellcheck disable=SC2086
        if $c -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1; then
            echo "$c"; return 0
        fi
    done
    return 1
}

PY=$(finde_python || true)

if [ -z "$PY" ] && [ "$AUTO" = 0 ]; then
    case "$(uname -s)" in
        Darwin)
            if command -v brew >/dev/null 2>&1 || [ -x /opt/homebrew/bin/brew ] || [ -x /usr/local/bin/brew ]; then
                BREW=$(command -v brew || ls /opt/homebrew/bin/brew /usr/local/bin/brew 2>/dev/null | head -n1)
                echo "Kein Python >= 3.11 gefunden – installiere python@3.12 über Homebrew ..."
                "$BREW" install python@3.12
                PY=$(finde_python || true)
            fi ;;
    esac
fi

if [ -z "$PY" ]; then
    {
        echo "FEHLER: Kein Python >= 3.11 gefunden."
        case "$(uname -s)" in
            Darwin) echo "macOS: 'brew install python@3.12' (Homebrew: https://brew.sh) oder Installer von"
                    echo "       https://www.python.org/downloads/macos/ – danach erneut: sh setup.sh"
                    echo "       (/usr/bin/python3 von Apple ist 3.9 und zu alt.)" ;;
            Linux)  echo "Linux: z. B. 'sudo apt install python3 python3-venv' – danach erneut: sh setup.sh" ;;
            *)      echo "Windows: 'winget install Python.Python.3.12', dann in PowerShell: .\\setup.ps1" ;;
        esac
    } >&2
    exit 2
fi

ARGS=""
for a in "$@"; do
    case "$a" in
        --auto) ARGS="$ARGS --still" ;;
        *) ARGS="$ARGS $a" ;;
    esac
done
# shellcheck disable=SC2086
exec $PY einrichten.py $ARGS
