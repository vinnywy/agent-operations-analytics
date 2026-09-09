#!/bin/sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
python3 -c 'import sys; assert sys.version_info >= (3,11)'
if [ ! -x .venv/bin/python ]; then python3 -m venv .venv; fi
.venv/bin/python -m pip install .
.venv/bin/agentops --version
printf '%s\n' 'Instalado. Siga README.md e execute onboard --source .'
