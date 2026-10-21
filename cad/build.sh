#!/usr/bin/env bash
# Regenerate every STL in ../stl from cad/print/*.scad.
# Usage: cad/build.sh            (uses `openscad` from PATH, or set OPENSCAD=/path/to/openscad)
set -euo pipefail
cd "$(dirname "$0")"
OPENSCAD="${OPENSCAD:-openscad}"
mkdir -p ../stl
for f in print/*.scad; do
    name="$(basename "$f" .scad)"
    echo "==> $name"
    "$OPENSCAD" -q --export-format binstl -o "../stl/$name.stl" "$f"
done
echo "done: $(ls ../stl/*.stl | wc -l) STL files in stl/"
