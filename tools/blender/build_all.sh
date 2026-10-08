#!/usr/bin/env bash
# Rebuild the rigged, animated characters from the original 500k-triangle GLBs.
# Usage: tools/blender/build_all.sh <dir with original <Name>.glb files> <output dir> [jobs] [Name ...]
set -euo pipefail
SRC=$1; OUT=$2; JOBS=${3:-3}; shift 3 || shift $#
ONLY=" $* "
HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$OUT/renders"
while read -r name opts ratio; do
  if [ "$ONLY" != "  " ] && [[ "$ONLY" != *" $name "* ]]; then continue; fi
  ( blender -b --factory-startup --python "$HERE/rig_character.py" -- \
      "$SRC/$name.glb" "$name" "$OUT/$name.glb" "$OUT/renders" "$ratio" "$opts" 2>&1 </dev/null \
      | grep -E 'MESH|SKIN|WALK|EXPORTED|Error|Traceback' | sed "s/^/$name: /" ) &
  while [ "$(jobs -r | wc -l)" -ge "$JOBS" ]; do sleep 2; done
done < <(python3 -I - "$HERE/characters.json" <<'PY'
import json, sys
c = json.load(open(sys.argv[1]))
for n, o in c["characters"].items():
    print(n, json.dumps(dict(o, animate=1), separators=(",", ":")), c["ratio"])
PY
)
wait
