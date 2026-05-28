#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
. "${SCRIPT_DIR}/lib.sh"

prompt_file="${CE_ROOT}/config/prompts/smoke-image.txt"
prompt_override=""
seed="42"
width="1280"
height="720"
steps="9"
quantize="8"
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
    --steps)
      steps="$2"
      shift 2
      ;;
    --quantize|-q)
      quantize="$2"
      shift 2
      ;;
    --output)
      output_path="$2"
      shift 2
      ;;
    *)
      ce_die "Unknown option for smoke-image: $1"
      ;;
  esac
done

ce_create_runtime_dirs
mflux_bin="$(ce_mflux_cmd)" || ce_die "MFLUX is not installed. Run bin/ce bootstrap."

if [ -n "${prompt_override}" ]; then
  prompt="${prompt_override}"
else
  prompt="$(ce_read_prompt_file "${prompt_file}")"
fi

if [ -z "${output_path}" ]; then
  output_path="${CE_OUTPUTS_MLX_IMAGES_DIR}/smoke-image-$(ce_compact_timestamp_utc).png"
fi

mkdir -p "$(dirname "${output_path}")"

ce_info "Generating smoke-test image to ${output_path}"
"${mflux_bin}" \
  --prompt "${prompt}" \
  --width "${width}" \
  --height "${height}" \
  --seed "${seed}" \
  --steps "${steps}" \
  -q "${quantize}" \
  --output "${output_path}" \
  --metadata

ce_require_file "${output_path}"
ce_info "Smoke image complete: ${output_path}"

