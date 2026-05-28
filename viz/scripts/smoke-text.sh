#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
. "${SCRIPT_DIR}/lib.sh"

ce_load_config
ce_create_runtime_dirs

matrix_path="${CE_ROOT}/config/text_governance_matrix.json"
only_preset=""
skip_handoff="false"

usage() {
  cat <<'EOF'
Usage: bin/ce smoke-text [--only family/preset] [--skip-handoff]

Runs the matrix-driven text-governance certification harness for still and staged handoff/video probes.
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --only)
      only_preset="$2"
      shift 2
      ;;
    --skip-handoff)
      skip_handoff="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      ce_die "Unknown option for smoke-text: $1"
      ;;
  esac
done

ce_require_file "${matrix_path}"

if [ -n "${only_preset}" ] && [[ "${only_preset}" != */* ]]; then
  ce_die "--only must be in family/preset form."
fi

validate_matrix() {
  python3 - "${matrix_path}" "${only_preset}" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
only = sys.argv[2].strip()
data = json.loads(path.read_text(encoding="utf-8"))
if not isinstance(data, dict):
    raise SystemExit(f"{path}: matrix must be an object")
entries = data.get("entries")
if not isinstance(entries, list) or not entries:
    raise SystemExit(f"{path}: entries must be a non-empty list")

required = {
    "family",
    "preset",
    "canonical_seed",
    "governance_class",
    "source_text_repair_mode",
    "typography_mode",
    "handoff_probe",
    "handoff_frames",
    "width",
    "height",
    "expected_typography_metadata",
}
allowed_governance = {"strict_zero_letter", "controlled_text", "negative_control"}
allowed_modes = {"auto", "off", "force"}
allowed_handoff = {"none", "without_typography", "with_typography"}

seen = set()
selected = 0

for entry in entries:
    if not isinstance(entry, dict):
        raise SystemExit(f"{path}: matrix entries must be objects")
    missing = sorted(required - set(entry))
    if missing:
        raise SystemExit(f"{path}: entry missing fields: {', '.join(missing)}")
    preset_id = f"{entry['family']}/{entry['preset']}"
    if preset_id in seen:
        raise SystemExit(f"{path}: duplicate matrix entry for {preset_id}")
    seen.add(preset_id)
    if entry["governance_class"] not in allowed_governance:
        raise SystemExit(f"{path}: invalid governance_class for {preset_id}: {entry['governance_class']!r}")
    if entry["source_text_repair_mode"] not in allowed_modes:
        raise SystemExit(f"{path}: invalid source_text_repair_mode for {preset_id}: {entry['source_text_repair_mode']!r}")
    if entry["typography_mode"] not in allowed_modes:
        raise SystemExit(f"{path}: invalid typography_mode for {preset_id}: {entry['typography_mode']!r}")
    if entry["handoff_probe"] not in allowed_handoff:
        raise SystemExit(f"{path}: invalid handoff_probe for {preset_id}: {entry['handoff_probe']!r}")
    if not isinstance(entry["canonical_seed"], int):
        raise SystemExit(f"{path}: canonical_seed must be an integer for {preset_id}")
    for key in ("handoff_frames", "width", "height"):
        if not isinstance(entry[key], int) or entry[key] <= 0:
            raise SystemExit(f"{path}: {key} must be a positive integer for {preset_id}")
    if not isinstance(entry["expected_typography_metadata"], bool):
        raise SystemExit(f"{path}: expected_typography_metadata must be boolean for {preset_id}")
    if entry["governance_class"] == "strict_zero_letter" and entry["typography_mode"] != "off":
        raise SystemExit(f"{path}: strict_zero_letter entries must use typography_mode=off ({preset_id})")
    if entry["governance_class"] == "controlled_text" and entry["typography_mode"] == "off":
        raise SystemExit(f"{path}: controlled_text entries must not use typography_mode=off ({preset_id})")
    if entry["governance_class"] == "negative_control":
        if entry["source_text_repair_mode"] != "off" or entry["typography_mode"] != "off":
            raise SystemExit(f"{path}: negative_control entries must use off/off modes ({preset_id})")
        if entry["handoff_probe"] != "none":
            raise SystemExit(f"{path}: negative_control entries must use handoff_probe=none ({preset_id})")
    if entry["handoff_probe"] == "with_typography":
        rel = str(entry.get("handoff_typography_intent_path", "")).strip()
        if not rel:
            raise SystemExit(f"{path}: with_typography entries require handoff_typography_intent_path ({preset_id})")
        if not entry["expected_typography_metadata"]:
            raise SystemExit(f"{path}: with_typography entries must expect typography metadata ({preset_id})")
    if entry["handoff_probe"] != "with_typography" and entry["expected_typography_metadata"]:
        raise SystemExit(f"{path}: only with_typography entries may expect typography metadata ({preset_id})")
    if only and preset_id == only:
        selected += 1
    elif not only:
        selected += 1

if only and selected == 0:
    raise SystemExit(f"{path}: no matrix entry matched --only {only!r}")

print(selected)
PY
}

matrix_rows() {
  python3 - "${matrix_path}" "${only_preset}" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
only = sys.argv[2].strip()
data = json.loads(path.read_text(encoding="utf-8"))
separator = "\x1f"
for entry in data["entries"]:
    preset_id = f"{entry['family']}/{entry['preset']}"
    if only and preset_id != only:
        continue
    fields = [
        entry["family"],
        entry["preset"],
        str(entry["canonical_seed"]),
        entry["governance_class"],
        entry["source_text_repair_mode"],
        entry["typography_mode"],
        entry["handoff_probe"],
        str(entry.get("handoff_typography_intent_path", "")),
        str(entry["handoff_frames"]),
        str(entry["width"]),
        str(entry["height"]),
        "true" if entry["expected_typography_metadata"] else "false",
    ]
    print(separator.join(fields))
PY
}

manifest_field() {
  python3 - "$1" "$2" <<'PY'
import json
import sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
value = data
for part in sys.argv[2].split("."):
    if isinstance(value, dict):
        value = value.get(part)
    else:
        value = None
        break
print("" if value is None else value)
PY
}

manifest_first_item() {
  python3 - "$1" "$2" <<'PY'
import json
import sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
value = data.get(sys.argv[2], [])
if isinstance(value, list) and value:
    print(value[0])
else:
    print("")
PY
}

render_pipeline_manifest() {
  local family="$1"
  local preset="$2"
  shift 2
  local output
  if ! output="$("${CE_ROOT}/scripts/render.sh" pipeline "${family}" "${preset}" "$@" 2>&1)"; then
    printf '%s\n' "${output}" >&2
    return 1
  fi
  printf '%s\n' "${output}" >&2
  local manifest
  manifest="$(printf '%s\n' "${output}" | awk -F'-> ' '/pipeline manifest -> /{print $2}' | tail -1)"
  [ -n "${manifest}" ] || ce_die "Could not parse pipeline manifest for ${family}/${preset}"
  ce_require_file "${manifest}"
  printf '%s\n' "${manifest}"
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
  python3 - "${entries_jsonl}" "$1" "$2" "$3" "$4" "$5" "$6" "$7" <<'PY'
import json
import sys
from pathlib import Path

entry = {
    "preset_id": sys.argv[2],
    "governance_class": sys.argv[3],
    "still_manifest_path": sys.argv[4],
    "cleanup_validation_path": sys.argv[5],
    "typography_run_path": sys.argv[6],
    "handoff_video_manifest_path": sys.argv[7],
    "final_status": sys.argv[8],
}
with Path(sys.argv[1]).open("a", encoding="utf-8") as handle:
    handle.write(json.dumps(entry) + "\n")
PY
}

write_summary_json() {
  local exit_code="${1:-0}"
  python3 - "${entries_jsonl}" "${summary_path}" "${matrix_path}" "${run_root}" "${exit_code}" "${only_preset}" "${skip_handoff}" <<'PY'
import json
import sys
from pathlib import Path

entries_path = Path(sys.argv[1])
summary_path = Path(sys.argv[2])
matrix_path = Path(sys.argv[3])
run_root = Path(sys.argv[4])
exit_code = int(sys.argv[5])
only_preset = sys.argv[6]
skip_handoff = sys.argv[7].lower() == "true"

entries = []
if entries_path.exists():
    for line in entries_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            entries.append(json.loads(line))

matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
summary = {
    "status": "success" if exit_code == 0 else "failed",
    "matrix_path": str(matrix_path),
    "schema_version": matrix.get("schema_version"),
    "log_root": str(run_root),
    "selected_filter": only_preset,
    "skip_handoff": skip_handoff,
    "entries": entries,
}
summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
PY
}

selected_count="$(validate_matrix)"
run_root="${CE_OUTPUTS_LOGS_DIR}/smoke-text-$(ce_compact_timestamp_utc)"
mkdir -p "${run_root}"
entries_jsonl="${run_root}/entries.jsonl"
summary_path="${run_root}/summary.json"

trap 'exit_code=$?; write_summary_json "${exit_code}"' EXIT

repo_relative_path() {
  local rel="$1"
  if [ -z "${rel}" ]; then
    printf '\n'
  else
    ce_abs_path "${CE_ROOT}/${rel}"
  fi
}

for_expected_typography_metadata() {
  if [ "$1" = "true" ]; then
    printf 'with typography metadata'
  else
    printf 'without typography metadata'
  fi
}

ce_info "Smoke text: selected ${selected_count} matrix entr$( [ "${selected_count}" = "1" ] && printf 'y' || printf 'ies' )"

while IFS=$'\x1f' read -r family preset canonical_seed governance_class source_text_repair_mode typography_mode handoff_probe handoff_typography_intent_rel handoff_frames width height expected_typography_metadata; do
  [ -n "${family}" ] || continue
  preset_id="${family}/${preset}"
  still_manifest=""
  cleanup_validation=""
  typography_run=""
  handoff_video=""
  typography_sidecar="${CE_ROOT}/workflows/typography/${family}/${preset}.json"
  repair_policy="${CE_ROOT}/workflows/source_text_repair/${family}/${preset}.json"

  case "${governance_class}" in
    controlled_text)
      ce_info "Smoke text: ${preset_id} controlled-text certification"
      [ -f "${typography_sidecar}" ] || ce_die "${preset_id} is controlled_text but has no typography sidecar."
      if [ "${handoff_probe}" = "with_typography" ]; then
        handoff_typography_intent_path="$(repo_relative_path "${handoff_typography_intent_rel}")"
        ce_require_file "${handoff_typography_intent_path}"
      fi
      ;;
    strict_zero_letter)
      ce_info "Smoke text: ${preset_id} strict zero-letter certification"
      if [ -f "${repair_policy}" ]; then
        prefinal_enabled="$(
          python3 - "${repair_policy}" <<'PY'
import json
import sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print("true" if bool(data.get("enabled", False)) else "false")
PY
        )"
        if [ "${prefinal_enabled}" = "false" ]; then
          :
        fi
      fi
      ;;
    negative_control)
      ce_info "Smoke text: ${preset_id} negative control"
      [ ! -f "${repair_policy}" ] || ce_die "${preset_id} negative control unexpectedly has a repair policy."
      [ ! -f "${typography_sidecar}" ] || ce_die "${preset_id} negative control unexpectedly has a typography sidecar."
      append_summary_entry "${preset_id}" "${governance_class}" "" "" "" "" "success"
      continue
      ;;
    *)
      ce_die "Unsupported governance class for ${preset_id}: ${governance_class}"
      ;;
  esac

  still_manifest="$(render_pipeline_manifest "${family}" "${preset}" --selected-seed "${canonical_seed}" --source-text-repair "${source_text_repair_mode}" --typography "${typography_mode}")"
  visual_qc_manifest="$(manifest_field "${still_manifest}" stage_validations.visual_qc.audit_manifest)"
  [ -n "${visual_qc_manifest}" ] || ce_die "${preset_id} did not record visual_qc validation."
  ce_require_file "${visual_qc_manifest}"
  visual_qc_status="$(manifest_field "${still_manifest}" stage_validations.visual_qc.status)"
  [ "${visual_qc_status}" = "ok" ] || ce_die "${preset_id} visual_qc failed with status=${visual_qc_status}."
  cleanup_validation="$(manifest_field "${still_manifest}" stage_validations.cleanup_final_text.post_cleanup_text_audit)"
  [ -n "${cleanup_validation}" ] || ce_die "${preset_id} did not record cleanup_final_text validation."
  ce_require_file "${cleanup_validation}"

  typography_run="$(manifest_first_item "${still_manifest}" typography_runs)"
  case "${governance_class}" in
    controlled_text)
      [ -n "${typography_run}" ] || ce_die "${preset_id} controlled_text entry did not record a typography run."
      ce_require_file "${typography_run}"
      ;;
    strict_zero_letter)
      [ -z "${typography_run}" ] || ce_die "${preset_id} strict_zero_letter entry unexpectedly recorded a typography run."
      ;;
  esac

  if [ "${skip_handoff}" = "false" ] && [ "${handoff_probe}" != "none" ]; then
    case "${handoff_probe}" in
      with_typography)
        stage_source="$(manifest_first_item "${still_manifest}" base_final_outputs)"
        ce_require_file "${stage_source}"
        handoff_typography_intent_path="$(repo_relative_path "${handoff_typography_intent_rel}")"
        ce_require_file "${handoff_typography_intent_path}"
        staged_path="$(
          "${CE_ROOT}/scripts/handoff-stage.sh" "${stage_source}" --from comfy --typography-intent "${handoff_typography_intent_path}" \
            | awk -F': ' '/^INFO  Staged asset: /{print $2}' | tail -1
        )"
        ;;
      without_typography)
        stage_source="$(manifest_first_item "${still_manifest}" final_outputs)"
        if [ -z "${stage_source}" ]; then
          stage_source="$(manifest_first_item "${still_manifest}" base_final_outputs)"
        fi
        ce_require_file "${stage_source}"
        staged_path="$(
          "${CE_ROOT}/scripts/handoff-stage.sh" "${stage_source}" --from comfy \
            | awk -F': ' '/^INFO  Staged asset: /{print $2}' | tail -1
        )"
        ;;
      *)
        ce_die "Unsupported handoff_probe for ${preset_id}: ${handoff_probe}"
        ;;
    esac
    [ -n "${staged_path}" ] || ce_die "Could not stage ${preset_id} for handoff."
    ce_require_file "${staged_path}"

    handoff_video="$(handoff_video_manifest "${staged_path}" --frames "${handoff_frames}" --width "${width}" --height "${height}" --typography auto)"
    if [ "${expected_typography_metadata}" = "true" ]; then
      typography_intent_value="$(ce_load_manifest_value "${handoff_video}" typography_intent_path)"
      typography_run_value="$(ce_load_manifest_value "${handoff_video}" typography_run_manifest)"
      [ -n "${typography_intent_value}" ] || ce_die "${preset_id} handoff expected typography metadata but typography_intent_path was empty."
      [ -n "${typography_run_value}" ] || ce_die "${preset_id} handoff expected typography metadata but typography_run_manifest was empty."
    else
      typography_intent_value="$(ce_load_manifest_value "${handoff_video}" typography_intent_path)"
      typography_run_value="$(ce_load_manifest_value "${handoff_video}" typography_run_manifest)"
      [ -z "${typography_intent_value}" ] || ce_die "${preset_id} handoff expected no typography metadata but typography_intent_path was present."
      [ -z "${typography_run_value}" ] || ce_die "${preset_id} handoff expected no typography metadata but typography_run_manifest was present."
    fi
  fi

  append_summary_entry "${preset_id}" "${governance_class}" "${still_manifest}" "${cleanup_validation}" "${typography_run}" "${handoff_video}" "success"
done < <(matrix_rows)

ce_info "Smoke text complete: ${run_root}"
