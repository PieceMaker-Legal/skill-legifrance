#!/bin/sh
# Prépare le venv local de la skill. Aucun code distant n'est téléchargé.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
exec python3 "$ROOT/scripts/legifrance.py" --bootstrap-only
