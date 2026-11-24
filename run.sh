#!/bin/sh
# Finds Python and starts the actiontrack menu.
cd "$(dirname "$0")" || exit 1
if command -v python3 >/dev/null 2>&1; then exec python3 run.py "$@"; fi
if command -v python >/dev/null 2>&1; then exec python run.py "$@"; fi
echo "Python 3.10 or newer was not found. Install it from https://www.python.org/downloads/ and run this file again."
exit 1
