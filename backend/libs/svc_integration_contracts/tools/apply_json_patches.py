import sys
import json
from pathlib import Path
from jsonpatch import JsonPatch

if len(sys.argv) < 3:
    sys.exit('Usage: apply_json_patches.py <input.json> <patch1.json> [<patch2.json>]')

input_path = Path(sys.argv[1])
patch_files = [Path(p) for p in sys.argv[2:]]

raw = json.load(open(input_path))

for patch_file in patch_files:
    patch = JsonPatch(json.loads(patch_file.read_text()))
    raw = patch.apply(raw, in_place=False)

output_path = input_path.parent / 'openapi.patched.json'
output_path.write_text(json.dumps(raw, indent=2, ensure_ascii=False))