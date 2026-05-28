#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
. "${SCRIPT_DIR}/lib.sh"

ce_load_config
ce_create_runtime_dirs

matrix_path="${CE_ROOT}/config/motion_certification_matrix.json"
only_target=""

usage() {
  cat <<'EOF'
Usage: bin/ce smoke-motion [--only episode_id|family/preset]

Runs the matrix-driven motion certification harness for staged still-to-video proofs.
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --only)
      only_target="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      ce_die "Unknown option for smoke-motion: $1"
      ;;
  esac
done

ce_require_file "${matrix_path}"

validate_matrix() {
  python3 - "${matrix_path}" "${only_target}" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
only = sys.argv[2].strip()
data = json.loads(path.read_text(encoding="utf-8"))
entries = data.get("entries")
if not isinstance(entries, list) or not entries:
    raise SystemExit(f"{path}: entries must be a non-empty list")

required = {
    "episode_id",
    "motion_item_id",
    "preset_id",
    "still_path",
    "prompt",
    "frames",
    "width",
    "height",
    "pipeline",
    "typography_intent_path",
    "expected_typography_metadata",
    "min_duration_seconds",
}
seen = set()
selected = 0
for entry in entries:
    missing = sorted(required - set(entry))
    if missing:
        raise SystemExit(f"{path}: entry missing fields: {', '.join(missing)}")
    key = (entry["episode_id"], entry["motion_item_id"])
    if key in seen:
        raise SystemExit(f"{path}: duplicate entry for {entry['episode_id']} / {entry['motion_item_id']}")
    seen.add(key)
    if not isinstance(entry["frames"], int) or entry["frames"] <= 0:
        raise SystemExit(f"{path}: frames must be positive for {entry['episode_id']}")
    for name in ("width", "height"):
        if not isinstance(entry[name], int) or entry[name] <= 0:
            raise SystemExit(f"{path}: {name} must be positive for {entry['episode_id']}")
    if not isinstance(entry["expected_typography_metadata"], bool):
        raise SystemExit(f"{path}: expected_typography_metadata must be boolean for {entry['episode_id']}")
    if float(entry["min_duration_seconds"]) < 0:
        raise SystemExit(f"{path}: min_duration_seconds must be non-negative for {entry['episode_id']}")
    if entry["expected_typography_metadata"] and not str(entry["typography_intent_path"]).strip():
        raise SystemExit(f"{path}: entries that expect typography metadata must provide typography_intent_path ({entry['episode_id']})")
    if only:
        if only == entry["episode_id"] or only == entry["preset_id"]:
            selected += 1
    else:
        selected += 1

if only and selected == 0:
    raise SystemExit(f"{path}: no matrix entry matched --only {only!r}")

print(selected)
PY
}

matrix_rows() {
  python3 - "${matrix_path}" "${only_target}" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
only = sys.argv[2].strip()
separator = "\x1f"
for entry in json.loads(path.read_text(encoding="utf-8"))["entries"]:
    if only and only not in {entry["episode_id"], entry["preset_id"]}:
        continue
    print(
        separator.join(
            [
                entry["episode_id"],
                entry["motion_item_id"],
                entry["preset_id"],
                entry["still_path"],
                entry["prompt"],
                str(entry["frames"]),
                str(entry["width"]),
                str(entry["height"]),
                entry["pipeline"],
                str(entry["typography_intent_path"]),
                "true" if entry["expected_typography_metadata"] else "false",
                str(entry["min_duration_seconds"]),
            ]
        )
    )
PY
}

manifest_field() {
  python3 - "$1" "$2" <<'PY'
import json
import sys
from pathlib import Path

value = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
for part in sys.argv[2].split("."):
    if isinstance(value, dict):
        value = value.get(part)
    else:
        value = None
        break
print("" if value is None else value)
PY
}

repo_relative_path() {
  local rel="$1"
  if [ -z "${rel}" ]; then
    printf '\n'
  else
    ce_abs_path "${CE_ROOT}/${rel}"
  fi
}

handoff_video_manifest() {
  local staged="$1"
  shift
  local output
  if ! output="$("${CE_ROOT}/scripts/handoff-i2v.sh" "${staged}" "$@" 2>&1)"; then
    printf '%s\n' "${output}" >&2
    return 1
  fi
  printf '%s\n' "${output}" >&2
  local manifest
  manifest="$(printf '%s\n' "${output}" | awk -F': ' '/^INFO  Handoff video manifest: /{print $2}' | tail -1)"
  [ -n "${manifest}" ] || ce_die "Could not parse handoff video manifest for ${staged}"
  ce_require_file "${manifest}"
  printf '%s\n' "${manifest}"
}

append_summary_entry() {
  python3 - "${entries_jsonl}" "$1" "$2" "$3" "$4" "$5" "$6" <<'PY'
import json
import sys
from pathlib import Path

entry = {
    "episode_id": sys.argv[2],
    "motion_item_id": sys.argv[3],
    "preset_id": sys.argv[4],
    "staged_asset_path": sys.argv[5],
    "video_manifest_path": sys.argv[6],
    "final_status": sys.argv[7],
}
with Path(sys.argv[1]).open("a", encoding="utf-8") as handle:
    handle.write(json.dumps(entry) + "\n")
PY
}

write_summary_json() {
  local exit_code="${1:-0}"
  python3 - "${entries_jsonl}" "${summary_path}" "${matrix_path}" "${run_root}" "${exit_code}" "${only_target}" <<'PY'
import json
import sys
from pathlib import Path

entries = []
entries_path = Path(sys.argv[1])
if entries_path.exists():
    for line in entries_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            entries.append(json.loads(line))

summary = {
    "status": "success" if int(sys.argv[5]) == 0 else "failed",
    "matrix_path": sys.argv[3],
    "log_root": sys.argv[4],
    "selected_filter": sys.argv[6],
    "entries": entries,
}
Path(sys.argv[2]).write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
PY
}

selected_count="$(validate_matrix)"
run_root="${CE_OUTPUTS_LOGS_DIR}/smoke-motion-$(ce_compact_timestamp_utc)"
mkdir -p "${run_root}"
entries_jsonl="${run_root}/entries.jsonl"
summary_path="${run_root}/summary.json"

trap 'exit_code=$?; write_summary_json "${exit_code}"' EXIT

ce_info "Smoke motion: selected ${selected_count} matrix entr$( [ "${selected_count}" = "1" ] && printf 'y' || printf 'ies' )"

while IFS=$'\x1f' read -r episode_id motion_item_id preset_id still_path prompt frames width height pipeline typography_intent_rel expected_typography_metadata min_duration_seconds; do
  [ -n "${episode_id}" ] || continue
  still_path="$(ce_abs_path "${still_path}")"
  ce_require_file "${still_path}"
  typography_intent_path="$(repo_relative_path "${typography_intent_rel}")"

  ce_info "Smoke motion: ${episode_id}/${motion_item_id} (${preset_id})"

  stage_args=(
    "${CE_ROOT}/scripts/handoff-stage.sh"
    "${still_path}"
    --from comfy
    --prompt "${prompt}"
    --width "${width}"
    --height "${height}"
    --next-step review
  )
  if [ -n "${typography_intent_path}" ]; then
    stage_args+=(--typography-intent "${typography_intent_path}")
  fi
  stage_output="$("${stage_args[@]}" 2>&1)" || {
    printf '%s\n' "${stage_output}" >&2
    ce_die "handoff-stage failed for ${episode_id}/${motion_item_id}"
  }
  printf '%s\n' "${stage_output}" >&2
  staged_path="$(printf '%s\n' "${stage_output}" | awk -F': ' '/^INFO  Staged asset: /{print $2}' | tail -1)"
  [ -n "${staged_path}" ] || ce_die "Could not parse staged asset for ${episode_id}/${motion_item_id}"
  ce_require_file "${staged_path}"

  video_manifest="$(
    handoff_video_manifest \
      "${staged_path}" \
      --frames "${frames}" \
      --width "${width}" \
      --height "${height}" \
      --pipeline "${pipeline}" \
      --typography auto
  )"

  output_path="$(manifest_field "${video_manifest}" output_path)"
  source_staged_path="$(manifest_field "${video_manifest}" source_staged_path)"
  typography_run_manifest="$(manifest_field "${video_manifest}" typography_run_manifest)"
  typography_intent_written="$(manifest_field "${video_manifest}" typography_intent_path)"

  ce_require_file "${output_path}"
  [ "${source_staged_path}" = "${staged_path}" ] || ce_die "Video manifest source_staged_path mismatch for ${episode_id}/${motion_item_id}"
  [ "$(manifest_field "${video_manifest}" prompt)" = "${prompt}" ] || ce_die "Video manifest prompt mismatch for ${episode_id}/${motion_item_id}"
  [ "$(manifest_field "${video_manifest}" pipeline)" = "${pipeline}" ] || ce_die "Video manifest pipeline mismatch for ${episode_id}/${motion_item_id}"
  [ "$(manifest_field "${video_manifest}" frames)" = "${frames}" ] || ce_die "Video manifest frames mismatch for ${episode_id}/${motion_item_id}"
  [ "$(manifest_field "${video_manifest}" width)" = "${width}" ] || ce_die "Video manifest width mismatch for ${episode_id}/${motion_item_id}"
  [ "$(manifest_field "${video_manifest}" height)" = "${height}" ] || ce_die "Video manifest height mismatch for ${episode_id}/${motion_item_id}"
  python3 - "${video_manifest}" "${episode_id}" "${motion_item_id}" "${min_duration_seconds}" <<'PY'
import json
import sys
from pathlib import Path

manifest = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
episode_id = sys.argv[2]
motion_item_id = sys.argv[3]
minimum = float(sys.argv[4] or "0")
duration = float(manifest.get("duration_seconds", 0.0) or 0.0)
if duration <= 0.0:
    raise SystemExit(f"Video manifest duration_seconds missing for {episode_id}/{motion_item_id}")
if minimum > 0.0 and duration + 1e-6 < minimum:
    raise SystemExit(
        f"Video manifest duration_seconds too short for {episode_id}/{motion_item_id}: "
        f"{duration:.3f}s < {minimum:.3f}s"
    )
PY

  if [ "${expected_typography_metadata}" = "true" ]; then
    [ -n "${typography_run_manifest}" ] || ce_die "Expected typography metadata for ${episode_id}/${motion_item_id}"
    ce_require_file "${typography_run_manifest}"
    [ -n "${typography_intent_written}" ] || ce_die "Expected typography intent path in video manifest for ${episode_id}/${motion_item_id}"
  else
    [ -z "${typography_run_manifest}" ] || ce_die "Did not expect typography metadata for ${episode_id}/${motion_item_id}"
    [ -z "${typography_intent_written}" ] || ce_die "Did not expect typography intent path for ${episode_id}/${motion_item_id}"
  fi

  append_summary_entry "${episode_id}" "${motion_item_id}" "${preset_id}" "${staged_path}" "${video_manifest}" "success"
done < <(matrix_rows)

ce_info "Smoke motion complete. Summary: ${summary_path}"
