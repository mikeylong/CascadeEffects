#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
. "${SCRIPT_DIR}/lib.sh"
ce_load_config

if [ $# -lt 1 ]; then
  ce_die "Usage: bin/ce handoff-i2v /path/to/staged-file [--prompt text] [--frames n] [--width n] [--height n] [--seed n] [--pipeline name] [--model-repo repo] [--text-encoder-repo repo] [--output path] [--typography auto|off|force] [--typography-intent /absolute/path/to/intent.json]"
fi

staged_path_input="$1"
shift

prompt_override=""
frames="33"
width=""
height=""
width_explicit="false"
height_explicit="false"
seed=""
pipeline="distilled"
model_repo="${CE_MLX_VIDEO_MODEL_REPO}"
model_repo_explicit="false"
text_encoder_repo="${CE_MLX_VIDEO_TEXT_ENCODER_REPO}"
output_path=""
text_encoder_repo_explicit="false"
typography_mode="auto"
typography_intent_override=""

while [ $# -gt 0 ]; do
  case "$1" in
    --prompt)
      prompt_override="$2"
      shift 2
      ;;
    --frames|-n|--num-frames)
      frames="$2"
      shift 2
      ;;
    --width)
      width="$2"
      width_explicit="true"
      shift 2
      ;;
    --height)
      height="$2"
      height_explicit="true"
      shift 2
      ;;
    --seed)
      seed="$2"
      shift 2
      ;;
    --pipeline)
      pipeline="$2"
      shift 2
      ;;
    --model-repo)
      model_repo="$2"
      model_repo_explicit="true"
      shift 2
      ;;
    --text-encoder-repo)
      text_encoder_repo="$2"
      text_encoder_repo_explicit="true"
      shift 2
      ;;
    --output)
      output_path="$2"
      shift 2
      ;;
    --typography)
      typography_mode="$2"
      shift 2
      ;;
    --typography-intent)
      typography_intent_override="$2"
      shift 2
      ;;
    *)
      ce_die "Unknown option for handoff-i2v: $1"
      ;;
  esac
done

case "${typography_mode}" in
  auto|off|force)
    ;;
  *)
    ce_die "--typography must be one of auto, off, force"
    ;;
esac

staged_path="$(ce_abs_path_preserve_links "${staged_path_input}")"
resolved_source_path="$(ce_abs_path "${staged_path}")"
ce_require_file "${staged_path}"
uv_bin="$(ce_uv_cmd)" || ce_die "uv is not installed. Run bin/ce bootstrap."
ce_create_runtime_dirs
ce_require_file "${CE_ROOT}/scripts/video.sh"

if [ "${pipeline}" = "apple-ltx23-q8-one-stage" ]; then
  ce_require_dir "${CE_LTX23_MLX_DIR}"
  ce_require_file "${CE_LTX23_MLX_DIR}/pyproject.toml"
else
  ce_require_file "${CE_MLX_VIDEO_DIR}/pyproject.toml"
fi

manifest_path="${staged_path}.json"
typography_intent_path=""
typography_intent_enabled="false"

if [ -n "${typography_intent_override}" ]; then
  typography_intent_path="$(ce_abs_path "${typography_intent_override}")"
elif [ -f "${manifest_path}" ]; then
  typography_intent_path="$(ce_load_manifest_value "${manifest_path}" typography_intent_path)"
  if [ -n "${typography_intent_path}" ]; then
    typography_intent_path="$(ce_abs_path "${typography_intent_path}")"
  fi
fi

if [ -n "${typography_intent_path}" ]; then
  ce_require_file "${typography_intent_path}"
  typography_intent_enabled="$(
    python3 - "${typography_intent_path}" <<'PY'
import json
import sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print("true" if bool(data.get("enabled", False)) else "false")
PY
  )"
fi

if [ -n "${prompt_override}" ]; then
  prompt="${prompt_override}"
elif [ -f "${manifest_path}" ]; then
  prompt="$(ce_load_manifest_value "${manifest_path}" prompt)"
else
  prompt="$(ce_read_prompt_file "${CE_ROOT}/config/prompts/smoke-video.txt")"
fi

if [ -z "${prompt}" ]; then
  prompt="$(ce_read_prompt_file "${CE_ROOT}/config/prompts/smoke-video.txt")"
fi

if [ -z "${seed}" ] && [ -f "${manifest_path}" ]; then
  seed="$(ce_load_manifest_value "${manifest_path}" seed)"
fi

if [ -z "${seed}" ]; then
  seed="42"
fi

if [ "${pipeline}" = "apple-ltx23-q8-one-stage" ] && [ "${model_repo_explicit}" != "true" ]; then
  model_repo="${CE_LTX23_MLX_MODEL_REPO}"
fi

if [ "${pipeline}" = "apple-ltx23-q8-one-stage" ] && [ "${text_encoder_repo_explicit}" != "true" ]; then
  text_encoder_repo="${CE_LTX23_MLX_GEMMA_REPO}"
fi

if [ -z "${width}" ] && [ -f "${manifest_path}" ]; then
  width="$(ce_load_manifest_value "${manifest_path}" width)"
fi

if [ -z "${height}" ] && [ -f "${manifest_path}" ]; then
  height="$(ce_load_manifest_value "${manifest_path}" height)"
fi

dimensions="$(
python3 - "${width}" "${height}" "${width_explicit}" "${height_explicit}" "${pipeline}" <<'PY'
import sys

raw_width = sys.argv[1].strip()
raw_height = sys.argv[2].strip()
width_explicit = sys.argv[3].strip().lower() == "true"
height_explicit = sys.argv[4].strip().lower() == "true"
pipeline = sys.argv[5].strip().lower()

def parse_int(raw: str) -> int | None:
    if not raw:
        return None
    try:
        value = int(raw)
    except ValueError:
        return None
    return value if value > 0 else None

def round_to_multiple(value: int, step: int = 32, minimum: int = 256) -> int:
    value = max(minimum, value)
    rounded = ((value + step - 1) // step) * step
    return max(minimum, rounded)

width_value = parse_int(raw_width)
height_value = parse_int(raw_height)

default_width = 640
default_height = 352
step = 64 if pipeline in {"distilled", "dev-two-stage", "dev-two-stage-hq"} else 32

if width_explicit and height_explicit and width_value is not None and height_value is not None:
    width = width_value
    height = height_value
elif width_explicit and width_value is not None:
    width = width_value
    height = int(round(width * default_height / default_width))
elif height_explicit and height_value is not None:
    height = height_value
    width = int(round(height * default_width / default_height))
elif width_value is None and height_value is None:
    width = default_width
    height = default_height
elif width_value is not None and height_value is not None:
    width = width_value
    height = height_value
elif width_value is not None:
    width = width_value
    height = int(round(width * default_height / default_width))
else:
    height = height_value
    width = int(round(height * default_width / default_height))

if not (width_explicit and height_explicit):
    longest_side = max(width, height)
    if longest_side > 640:
        scale = 640 / longest_side
        width = int(round(width * scale))
        height = int(round(height * scale))

width = round_to_multiple(width, step=step)
height = round_to_multiple(height, step=step)

print(f"{width} {height}")
PY
)"
width="${dimensions%% *}"
height="${dimensions##* }"
input_base_image_path="${resolved_source_path}"
input_image_path="${resolved_source_path}"
typography_run_manifest=""
typography_validation_summary="{}"
typography_applied="false"
repair_policy_path=""
repair_manifest_path=""
post_final_cleanup_enabled="false"

repair_context_lines="$(
  python3 - "${manifest_path}" "${resolved_source_path}" "${CE_ROOT}" "${CE_COMFY_OUTPUT_DIR}" "${typography_intent_path}" <<'PY'
import json
import sys
from pathlib import Path

manifest_path = Path(sys.argv[1])
resolved_source_path = Path(sys.argv[2]).resolve()
repo_root = Path(sys.argv[3]).resolve()
comfy_output_dir = Path(sys.argv[4]).resolve()
typography_intent_path = Path(sys.argv[5]).expanduser().resolve() if sys.argv[5].strip() else None

source_path = resolved_source_path
if manifest_path.exists():
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_source = str(data.get("source_path", "")).strip()
    if manifest_source:
        source_path = Path(manifest_source).expanduser().resolve()

family = ""
preset = ""
repair_policy_path = ""
repair_manifest_path = ""
post_final_cleanup_enabled = False


def load_repair_policy(candidate: Path) -> tuple[str, bool]:
    data = json.loads(candidate.read_text(encoding="utf-8"))
    cleanup_enabled = bool((data.get("post_final_cleanup") or {}).get("enabled"))
    return str(candidate), cleanup_enabled


def infer_preset_from_intent(path: Path | None) -> tuple[str, str]:
    if path is None:
        return "", ""
    name = path.name
    suffixes = ("_handoff_asset.intent.json", "_still.intent.json")
    for suffix in suffixes:
        if name.endswith(suffix):
            preset_name = name[: -len(suffix)]
            break
    else:
        return "", ""

    matches = sorted((repo_root / "workflows" / "source_text_repair").glob(f"*/{preset_name}.json"))
    if len(matches) != 1:
        return "", preset_name
    family_name = matches[0].parent.name
    return family_name, preset_name

try:
    rel = source_path.relative_to(comfy_output_dir / "cascadeeffects")
    parts = rel.parts
    if len(parts) >= 3:
        family = parts[0]
        preset = parts[1]
except ValueError:
    parts = ()

if family and preset:
    candidate = repo_root / "workflows" / "source_text_repair" / family / f"{preset}.json"
    if candidate.exists():
        repair_policy_path, post_final_cleanup_enabled = load_repair_policy(candidate)
    runs_dir = repo_root / "workflows" / "generated" / "runs" / family / preset
    if runs_dir.exists():
        for candidate in sorted(runs_dir.glob("*__pipeline.run.json"), reverse=True):
            try:
                data = json.loads(candidate.read_text(encoding="utf-8"))
            except Exception:
                continue
            final_outputs = [Path(item).resolve() for item in data.get("final_outputs", []) if item]
            base_outputs = [Path(item).resolve() for item in data.get("base_final_outputs", []) if item]
            if source_path in final_outputs or source_path in base_outputs:
                repair_value = str(data.get("repair_run_manifest", "")).strip()
                if repair_value:
                    repair_candidate = Path(repair_value).expanduser().resolve()
                    if repair_candidate.exists():
                        repair_manifest_path = str(repair_candidate)
                break

if not family or not preset:
    family, preset = infer_preset_from_intent(typography_intent_path)
    if family and preset:
        candidate = repo_root / "workflows" / "source_text_repair" / family / f"{preset}.json"
        if candidate.exists():
            repair_policy_path, post_final_cleanup_enabled = load_repair_policy(candidate)

print(family)
print(preset)
print(str(repair_policy_path))
print("true" if post_final_cleanup_enabled else "false")
print(str(repair_manifest_path))
PY
)"
source_family="$(printf '%s\n' "${repair_context_lines}" | sed -n '1p')"
source_preset="$(printf '%s\n' "${repair_context_lines}" | sed -n '2p')"
repair_policy_path="$(printf '%s\n' "${repair_context_lines}" | sed -n '3p')"
post_final_cleanup_enabled="$(printf '%s\n' "${repair_context_lines}" | sed -n '4p')"
repair_manifest_path="$(printf '%s\n' "${repair_context_lines}" | sed -n '5p')"

build_typography_output_path() {
  python3 - "${staged_path}" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
print(path.with_name(f"{path.stem}__typography{path.suffix}"))
PY
}

video_has_audio_stream() {
  local video_path="$1"
  ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 "${video_path}" 2>/dev/null | grep -q .
}

strip_video_audio_in_place() {
  local video_path="$1"
  local temp_path
  temp_path="$(dirname "${video_path}")/.$(basename "${video_path}").silent.mp4"
  rm -f "${temp_path}"
  ffmpeg -y -i "${video_path}" -map 0:v:0 -c copy -map_metadata -1 -movflags +faststart "${temp_path}" >/dev/null 2>&1 || ce_die "Failed to strip audio from ${video_path}"
  mv "${temp_path}" "${video_path}"
}

apply_handoff_typography() {
  local typography_output_path typography_summary_json typography_stderr typography_status
  local stderr_file cleanup_summary_json validated_summary_json cleanup_output_path cleanup_debug_dir
  typography_output_path="$(build_typography_output_path)"
  stderr_file="$(mktemp)"
  typography_status=0
  local -a typography_cmd=(
    "${CE_ROOT}/scripts/typography.sh" apply
    --target handoff_asset
    --artifact "${resolved_source_path}"
    --intent "${typography_intent_path}"
    --output "${typography_output_path}"
  )
  if [ -n "${repair_manifest_path}" ]; then
    typography_cmd+=(--repair-manifest "${repair_manifest_path}")
  fi
  typography_summary_json="$("${typography_cmd[@]}" 2>"${stderr_file}")" || typography_status=$?
  typography_stderr="$(cat "${stderr_file}")"
  rm -f "${stderr_file}"

  if [ "${typography_status}" -eq 0 ] && [ -z "${typography_summary_json}" ]; then
    ce_die "Controlled typography returned an empty summary for ${resolved_source_path}"
  fi

  if [ "${typography_status}" -ne 0 ]; then
    if [ "${post_final_cleanup_enabled}" != "true" ] || [ -z "${repair_policy_path}" ]; then
      ce_die "${typography_stderr:-Controlled typography failed for ${resolved_source_path}}"
    fi
    [ -f "${typography_output_path}" ] || ce_die "${typography_stderr:-Controlled typography failed for ${resolved_source_path}}"
    cleanup_debug_dir="${CE_ROOT}/workflows/generated/runs/handoff_asset/$(basename "${staged_path}")/debug/typography_overlay__post_cleanup"
    cleanup_output_path="$(
      python3 - "${typography_output_path}" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
print(path.with_name(f"{path.stem}__cleanup{path.suffix}"))
PY
    )"
    local -a cleanup_cmd=(
      "${CE_ROOT}/scripts/typography.sh" cleanup-final-text
      --artifact "${typography_output_path}"
      --intent "${typography_intent_path}"
      --policy "${repair_policy_path}"
      --output "${cleanup_output_path}"
      --debug-dir "${cleanup_debug_dir}"
    )
    if [ -n "${repair_manifest_path}" ]; then
      cleanup_cmd+=(--repair-manifest "${repair_manifest_path}")
    fi
    cleanup_summary_json="$("${cleanup_cmd[@]}")" || ce_die "Post-typography cleanup failed for ${typography_output_path}"

    local validate_status=0
    local validate_stderr_file validate_stderr
    validate_stderr_file="$(mktemp)"
    local -a validate_cmd=(
      "${CE_ROOT}/scripts/typography.sh" validate
      --target handoff_asset
      --artifact "${cleanup_output_path}"
      --intent "${typography_intent_path}"
      --debug-dir "${cleanup_debug_dir}/post_cleanup_validate"
    )
    if [ -n "${repair_manifest_path}" ]; then
      validate_cmd+=(--repair-manifest "${repair_manifest_path}")
    fi
    validated_summary_json="$("${validate_cmd[@]}" 2>"${validate_stderr_file}")" || validate_status=$?
    validate_stderr="$(cat "${validate_stderr_file}")"
    rm -f "${validate_stderr_file}"
    if [ "${validate_status}" -ne 0 ]; then
      ce_die "${validate_stderr:-Post-typography validation failed for ${cleanup_output_path}}"
    fi
    if [ -z "${validated_summary_json}" ]; then
      ce_die "Post-typography validation returned an empty summary for ${cleanup_output_path}"
    fi

    typography_summary_json="$(
      APPLY_SUMMARY_JSON="${typography_summary_json}" TYPOGRAPHY_SUMMARY_JSON="${validated_summary_json}" CLEANUP_SUMMARY_JSON="${cleanup_summary_json}" python3 - <<'PY'
import json
import os

apply_summary_raw = os.environ.get("APPLY_SUMMARY_JSON", "").strip()
summary = json.loads(apply_summary_raw) if apply_summary_raw else json.loads(os.environ["TYPOGRAPHY_SUMMARY_JSON"])
validated = json.loads(os.environ["TYPOGRAPHY_SUMMARY_JSON"])
cleanup = json.loads(os.environ["CLEANUP_SUMMARY_JSON"])
summary["output_artifact"] = cleanup["output_artifact"]
summary["validation"] = validated["validation"]
summary["debug_artifacts"] = validated.get("debug_artifacts", summary.get("debug_artifacts", []))
summary["post_typography_cleanup_output_image"] = cleanup["output_artifact"]
summary["post_typography_cleanup_validation"] = validated["validation"]
summary["post_typography_cleanup_manifest_path"] = cleanup["cleanup_manifest_path"]
print(json.dumps(summary))
PY
    )"
  fi

  printf '%s' "${typography_summary_json}"
}

write_handoff_typography_run_manifest() {
  TYPOGRAPHY_SUMMARY_JSON="$1" STAGED_PATH="${staged_path}" CE_ROOT="${CE_ROOT}" python3 - <<'PY'
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

summary = json.loads(os.environ["TYPOGRAPHY_SUMMARY_JSON"])
staged_path = Path(os.environ["STAGED_PATH"])
run_timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
run_dir = Path(os.environ["CE_ROOT"]) / "workflows" / "generated" / "runs" / "handoff_asset" / staged_path.stem
run_dir.mkdir(parents=True, exist_ok=True)
run_manifest_path = run_dir / f"{run_timestamp.replace(':', '').replace('-', '')}__typography_overlay.run.json"
manifest = {
    "run_id": str(uuid.uuid4()),
    "created_at": run_timestamp,
    "invocation": "handoff-i2v",
    "pipeline_id": None,
    "target": summary["target"],
    "artifact_type": summary["artifact_type"],
    "application_phase": summary["application_phase"],
    "staged_path": str(staged_path),
    "base_artifact": summary["artifact_path"],
    "typography_intent": summary["intent_path"],
    "typography_output_artifact": summary["output_artifact"],
    "typography_mode": summary["mode"],
    "zone_count": summary["zone_count"],
    "zones": summary["zones"],
    "validation": summary["validation"],
    "debug_artifacts": summary.get("debug_artifacts", []),
}
if summary.get("post_typography_cleanup_output_image"):
    manifest["post_typography_cleanup_output_image"] = summary["post_typography_cleanup_output_image"]
if summary.get("post_typography_cleanup_validation"):
    manifest["post_typography_cleanup_validation"] = summary["post_typography_cleanup_validation"]
if summary.get("post_typography_cleanup_manifest_path"):
    manifest["post_typography_cleanup_manifest_path"] = summary["post_typography_cleanup_manifest_path"]
run_manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print(run_manifest_path)
PY
}

case "${typography_mode}" in
  off)
    ;;
  auto)
    if [ -n "${typography_intent_path}" ] && [ "${typography_intent_enabled}" = "true" ]; then
      typography_summary_json="$(apply_handoff_typography)"
      input_image_path="$(
        TYPOGRAPHY_SUMMARY_JSON="${typography_summary_json}" python3 - <<'PY'
import json
import os

summary = json.loads(os.environ["TYPOGRAPHY_SUMMARY_JSON"])
print(summary["output_artifact"])
PY
      )"
      typography_run_manifest="$(write_handoff_typography_run_manifest "${typography_summary_json}")"
      typography_validation_summary="$(
        TYPOGRAPHY_SUMMARY_JSON="${typography_summary_json}" python3 - <<'PY'
import json
import os

summary = json.loads(os.environ["TYPOGRAPHY_SUMMARY_JSON"])
print(json.dumps(summary["validation"]))
PY
      )"
      typography_applied="true"
    fi
    ;;
  force)
    [ -n "${typography_intent_path}" ] || ce_die "Controlled typography was forced, but no typography intent was available."
    typography_summary_json="$(apply_handoff_typography)"
    input_image_path="$(
      TYPOGRAPHY_SUMMARY_JSON="${typography_summary_json}" python3 - <<'PY'
import json
import os

summary = json.loads(os.environ["TYPOGRAPHY_SUMMARY_JSON"])
print(summary["output_artifact"])
PY
    )"
    typography_run_manifest="$(write_handoff_typography_run_manifest "${typography_summary_json}")"
    typography_validation_summary="$(
      TYPOGRAPHY_SUMMARY_JSON="${typography_summary_json}" python3 - <<'PY'
import json
import os

summary = json.loads(os.environ["TYPOGRAPHY_SUMMARY_JSON"])
print(json.dumps(summary["validation"]))
PY
    )"
    typography_applied="true"
    ;;
esac

if [ -z "${output_path}" ]; then
  stem="$(python3 - "${staged_path}" <<'PY'
from pathlib import Path
import re
import sys

stem = Path(sys.argv[1]).stem
stem = re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip("-")
print(stem or "handoff")
PY
)"
  output_path="${CE_OUTPUTS_MLX_VIDEO_DIR}/${stem}-i2v-$(ce_compact_timestamp_utc).mp4"
fi

output_path="$(ce_abs_path_preserve_links "${output_path}")"
mkdir -p "$(dirname "${output_path}")"

source_model_repo="${model_repo}"
resolved_model_path=""

if [ "${pipeline}" = "apple-ltx23-q8-one-stage" ]; then
  resolved_model_path="${source_model_repo}"
  cmd=(
    ltx-2-mlx
    generate
    --prompt "${prompt}"
    --output "${output_path}"
    --model "${source_model_repo}"
    --height "${height}"
    --width "${width}"
    --frames "${frames}"
    --seed "${seed}"
    --image "${input_image_path}"
  )
  if [ -n "${text_encoder_repo}" ]; then
    cmd+=(--gemma "${text_encoder_repo}")
  fi
  ce_info "Running image-to-video handoff from ${staged_path}"
  ce_info "Using Apple-native LTX 2.3 defaults: frames=${frames} width=${width} height=${height} pipeline=${pipeline} runtime_root=${CE_LTX23_MLX_DIR} source_model_repo=${source_model_repo} resolved_model_path=${resolved_model_path}${text_encoder_repo:+ text_encoder_repo=${text_encoder_repo}} typography_mode=${typography_mode} typography_applied=${typography_applied}"
  (
    cd "${CE_LTX23_MLX_DIR}"
    HF_HOME="${CE_LTX23_MLX_HF_HOME}" \
    HF_HUB_CACHE="${CE_LTX23_MLX_HF_HUB_CACHE}" \
    "${uv_bin}" run "${cmd[@]}"
  )
else
  model_variant="distilled"
  case "${pipeline}" in
    dev|dev-two-stage|dev-two-stage-hq)
      model_variant="dev"
      ;;
  esac

  resolved_model_path="$(
    "${CE_ROOT}/scripts/video.sh" backend prepare \
      --model-repo "${source_model_repo}" \
      --variant "${model_variant}" \
      --print-path-only
  )"

  if [ "${text_encoder_repo_explicit}" != "true" ]; then
    text_encoder_repo=""
  fi

  cmd=(
    python -m mlx_video.models.ltx_2.generate
    --prompt "${prompt}"
    --pipeline "${pipeline}"
    --model-repo "${resolved_model_path}"
    --image "${input_image_path}"
    --num-frames "${frames}"
    --width "${width}"
    --height "${height}"
    --seed "${seed}"
    --output-path "${output_path}"
  )

  if [ -n "${text_encoder_repo}" ]; then
    cmd+=(--text-encoder-repo "${text_encoder_repo}")
  fi

  ce_info "Running image-to-video handoff from ${staged_path}"
  ce_info "Using cheap i2v defaults: frames=${frames} width=${width} height=${height} pipeline=${pipeline} source_model_repo=${source_model_repo} resolved_model_path=${resolved_model_path}${text_encoder_repo:+ text_encoder_repo=${text_encoder_repo}} typography_mode=${typography_mode} typography_applied=${typography_applied}"
  (
    cd "${CE_MLX_VIDEO_DIR}"
    HF_HOME="${CE_HF_HOME}" \
    HF_HUB_CACHE="${CE_HF_HUB_CACHE}" \
    "${uv_bin}" run "${cmd[@]}"
  )
fi

ce_require_file "${output_path}"
if video_has_audio_stream "${output_path}"; then
  ce_info "Removing unexpected audio stream from ${output_path}"
  strip_video_audio_in_place "${output_path}"
fi
video_manifest_path="${output_path}.json"
video_duration_seconds="$(
  python3 - "${output_path}" <<'PY'
import subprocess
import sys
from pathlib import Path

video_path = Path(sys.argv[1]).resolve()
completed = subprocess.run(
    [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ],
    check=False,
    capture_output=True,
    text=True,
)
if completed.returncode != 0:
    raise SystemExit(completed.stderr.strip() or completed.stdout.strip() or f"ffprobe failed for {video_path}")
print(completed.stdout.strip())
PY
)"
VIDEO_CREATED_AT="$(ce_timestamp_utc)"
VIDEO_MANIFEST_ID="$(ce_uuid)"
SOURCE_STAGED_PATH="${staged_path}" \
SOURCE_IMAGE_BASE_PATH="${input_base_image_path}" \
SOURCE_IMAGE_PATH="${input_image_path}" \
VIDEO_PROMPT="${prompt}" \
VIDEO_SEED="${seed}" \
VIDEO_FRAMES="${frames}" \
VIDEO_WIDTH="${width}" \
VIDEO_HEIGHT="${height}" \
VIDEO_PIPELINE="${pipeline}" \
VIDEO_MODEL_REPO="${source_model_repo}" \
VIDEO_RESOLVED_MODEL_PATH="${resolved_model_path}" \
VIDEO_TEXT_ENCODER_REPO="${text_encoder_repo}" \
VIDEO_OUTPUT_PATH="${output_path}" \
VIDEO_DURATION_SECONDS="${video_duration_seconds}" \
VIDEO_TYPOGRAPHY_MODE="${typography_mode}" \
VIDEO_TYPOGRAPHY_INTENT_PATH="${typography_intent_path}" \
VIDEO_TYPOGRAPHY_RUN_MANIFEST="${typography_run_manifest}" \
VIDEO_TYPOGRAPHY_VALIDATION_SUMMARY="${typography_validation_summary}" \
VIDEO_CREATED_AT="${VIDEO_CREATED_AT}" \
VIDEO_MANIFEST_ID="${VIDEO_MANIFEST_ID}" \
python3 - "${video_manifest_path}" <<'PY'
import json
import os
import sys
from pathlib import Path

manifest_path = Path(sys.argv[1])
data = {
    "id": os.environ["VIDEO_MANIFEST_ID"],
    "created_at": os.environ["VIDEO_CREATED_AT"],
    "source_staged_path": os.environ["SOURCE_STAGED_PATH"],
    "input_base_image_path": os.environ["SOURCE_IMAGE_BASE_PATH"],
    "input_image_path": os.environ["SOURCE_IMAGE_PATH"],
    "prompt": os.environ["VIDEO_PROMPT"],
    "seed": os.environ["VIDEO_SEED"],
    "frames": int(os.environ["VIDEO_FRAMES"]),
    "width": int(os.environ["VIDEO_WIDTH"]),
    "height": int(os.environ["VIDEO_HEIGHT"]),
    "pipeline": os.environ["VIDEO_PIPELINE"],
    "model_repo": os.environ["VIDEO_MODEL_REPO"],
    "resolved_model_path": os.environ["VIDEO_RESOLVED_MODEL_PATH"],
    "text_encoder_repo": os.environ["VIDEO_TEXT_ENCODER_REPO"],
    "output_path": os.environ["VIDEO_OUTPUT_PATH"],
    "duration_seconds": float(os.environ["VIDEO_DURATION_SECONDS"] or "0"),
    "typography_mode": os.environ["VIDEO_TYPOGRAPHY_MODE"],
    "typography_intent_path": os.environ["VIDEO_TYPOGRAPHY_INTENT_PATH"],
    "typography_run_manifest": os.environ["VIDEO_TYPOGRAPHY_RUN_MANIFEST"],
    "typography_validation": json.loads(os.environ["VIDEO_TYPOGRAPHY_VALIDATION_SUMMARY"] or "{}"),
}
manifest_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
PY

ce_info "Handoff video complete: ${output_path}"
ce_info "Handoff video manifest: ${video_manifest_path}"
