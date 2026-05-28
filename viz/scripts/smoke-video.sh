#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
. "${SCRIPT_DIR}/lib.sh"

prompt_file="${CE_ROOT}/config/prompts/smoke-video.txt"
prompt_override=""
frames="97"
width="768"
height="512"
steps=""
seed="42"
pipeline="distilled"
output_path=""

while [ $# -gt 0 ]; do
  case "$1" in
    --prompt-file)
      prompt_file="$2"
      shift 2
      ;;
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
      shift 2
      ;;
    --height)
      height="$2"
      shift 2
      ;;
    --steps)
      steps="$2"
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
    --output)
      output_path="$2"
      shift 2
      ;;
    *)
      ce_die "Unknown option for smoke-video: $1"
      ;;
  esac
done

ce_create_runtime_dirs
uv_bin="$(ce_uv_cmd)" || ce_die "uv is not installed. Run bin/ce bootstrap."
ce_require_file "${CE_MLX_VIDEO_DIR}/pyproject.toml"

if [ -n "${prompt_override}" ]; then
  prompt="${prompt_override}"
else
  prompt="$(ce_read_prompt_file "${prompt_file}")"
fi

if [ -z "${output_path}" ]; then
  output_path="${CE_OUTPUTS_MLX_VIDEO_DIR}/smoke-video-$(ce_compact_timestamp_utc).mp4"
fi

mkdir -p "$(dirname "${output_path}")"

cmd=(
  python -m mlx_video.models.ltx_2.generate
  --prompt "${prompt}"
  --pipeline "${pipeline}"
  --num-frames "${frames}"
  --width "${width}"
  --height "${height}"
  --seed "${seed}"
  --output-path "${output_path}"
)

if [ -n "${steps}" ]; then
  cmd+=(--steps "${steps}")
fi

ce_info "Generating smoke-test video to ${output_path}"
(
  cd "${CE_MLX_VIDEO_DIR}"
  "${uv_bin}" run "${cmd[@]}"
)

ce_require_file "${output_path}"
ce_info "Smoke video complete: ${output_path}"

