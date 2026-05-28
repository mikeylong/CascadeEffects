#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
. "${SCRIPT_DIR}/lib.sh"
ce_load_config

if [ $# -lt 1 ]; then
  ce_die "Usage: bin/ce handoff-stage /absolute/path/to/file --from comfy|mflux [--prompt text] [--seed n] [--width n] [--height n] [--next-step label] [--typography-intent /absolute/path/to/intent.json]"
fi

source_path="$1"
shift

source_tool=""
prompt=""
seed=""
width=""
height=""
next_step="review"
typography_intent=""

while [ $# -gt 0 ]; do
  case "$1" in
    --from)
      source_tool="$2"
      shift 2
      ;;
    --prompt)
      prompt="$2"
      shift 2
      ;;
    --seed)
      seed="$2"
      shift 2
      ;;
    --width)
      width="$2"
      shift 2
      ;;
    --height)
      height="$2"
      shift 2
      ;;
    --next-step)
      next_step="$2"
      shift 2
      ;;
    --typography-intent)
      typography_intent="$2"
      shift 2
      ;;
    *)
      ce_die "Unknown option for handoff-stage: $1"
      ;;
  esac
done

case "${source_tool}" in
  comfy|mflux)
    ;;
  *)
    ce_die "You must pass --from comfy or --from mflux"
    ;;
esac

source_path="$(ce_abs_path "${source_path}")"
ce_require_file "${source_path}"
if [ -n "${typography_intent}" ]; then
  typography_intent="$(ce_abs_path "${typography_intent}")"
  ce_require_file "${typography_intent}"
fi
ce_create_runtime_dirs

uuid="$(ce_uuid)"
timestamp="$(ce_compact_timestamp_utc)"
basename_safe="$(ce_slug_component "${source_path}")"
staged_path="${CE_OUTPUTS_HANDOFF_DIR}/${timestamp}-${uuid%%-*}-${source_tool}-${basename_safe}"
manifest_path="${staged_path}.json"
created_at="$(ce_timestamp_utc)"

ln -s "${source_path}" "${staged_path}"

SOURCE_TOOL="${source_tool}" \
SOURCE_PATH="${source_path}" \
STAGED_PATH="${staged_path}" \
PROMPT_VALUE="${prompt}" \
SEED_VALUE="${seed}" \
WIDTH_VALUE="${width}" \
HEIGHT_VALUE="${height}" \
NEXT_STEP_VALUE="${next_step}" \
TYPOGRAPHY_INTENT_VALUE="${typography_intent}" \
CREATED_AT="${created_at}" \
HANDOFF_ID="${uuid}" \
python3 - "${manifest_path}" <<'PY'
import json
import os
import sys
from pathlib import Path

manifest_path = Path(sys.argv[1])
data = {
    "id": os.environ["HANDOFF_ID"],
    "created_at": os.environ["CREATED_AT"],
    "source_tool": os.environ["SOURCE_TOOL"],
    "source_path": os.environ["SOURCE_PATH"],
    "staged_path": os.environ["STAGED_PATH"],
    "prompt": os.environ["PROMPT_VALUE"],
    "seed": os.environ["SEED_VALUE"],
    "width": os.environ["WIDTH_VALUE"],
    "height": os.environ["HEIGHT_VALUE"],
    "next_step": os.environ["NEXT_STEP_VALUE"],
    "typography_intent_path": os.environ["TYPOGRAPHY_INTENT_VALUE"],
}
manifest_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
PY

ce_info "Staged asset: ${staged_path}"
ce_info "Manifest: ${manifest_path}"
