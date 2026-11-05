#!/usr/bin/env bash
# Builds a standalone app on Mac/Linux:  dist/Escapism/   (run from the app/ folder)
set -e
python3 -m pip install --upgrade pyinstaller pywebview
python3 tools/fetch_three.py
python3 -m PyInstaller --noconfirm --clean --windowed --name Escapism \
  --add-data "escapism_app/ui:escapism_app/ui" \
  --add-data "rooms:rooms" \
  run_escapism.py
echo "Done! Your game is in dist/Escapism/"
