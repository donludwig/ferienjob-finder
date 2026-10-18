#!/bin/zsh
# Täglicher Lauf: holt aktuelle Anzeigen und baut die Seiten in ausgabe/. Er lädt NICHT hoch: Die Website wird nur aktualisiert,
# wenn die Person, die die Seite betreibt, es ausdrücklich freigibt (siehe README, Abschnitt Veröffentlichung). Kein Skript und kein Zeitplan lädt hoch.
# Protokoll: .cache/taeglich.log (nur Programmausgaben, keine Besucherdaten)
set -e
cd "${0:A:h}/.."
mkdir -p .cache
{
  echo "=== $(date '+%Y-%m-%d %H:%M') ==="
  .venv/bin/python -m finder bauen 2>&1 | tr '\r' '\n' | grep -v '^  Volltext [0-9]*/'
} >> .cache/taeglich.log 2>&1
