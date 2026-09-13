import json
import sys
from pathlib import Path

from jsonpatch import JsonPatch

ALLOWED_ROOT = Path(__file__).resolve().parent.parent


def safe_path(path: Path) -> Path:
    resolved = path.resolve()
    if resolved != ALLOWED_ROOT and ALLOWED_ROOT not in resolved.parents:
        raise ValueError(f"path {path!r} is outside {ALLOWED_ROOT}")
    return resolved


if len(sys.argv) < 3:
    sys.exit("Usage: apply_json_patches.py <input.json> <patch1.json> [<patch2.json>]")

input_path = safe_path(Path(sys.argv[1]))
patch_files = [safe_path(Path(p)) for p in sys.argv[2:]]

raw = json.loads(input_path.read_text())

for patch_file in patch_files:
    patch = JsonPatch(json.loads(patch_file.read_text()))
    raw = patch.apply(raw, in_place=False)

output_path = input_path.parent / "openapi.patched.json"
output_path.write_text(json.dumps(raw, indent=2, ensure_ascii=False))
