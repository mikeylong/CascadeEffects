#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
. "${SCRIPT_DIR}/lib.sh"

ce_load_config
ce_create_runtime_dirs

exec "$(ce_repo_python)" "${CE_ROOT}/scripts/render_tool.py" \
  --repo-root "${CE_ROOT}" \
  --models-root "${CE_MODELS_ROOT}" \
  --comfy-workflows-dir "${CE_COMFY_WORKFLOWS_DIR}" \
  --comfy-output-dir "${CE_COMFY_OUTPUT_DIR}" \
  --references-root "${CE_REFERENCES_ROOT}" \
  --comfy-input-dir "${CE_COMFY_INPUT_DIR}" \
  --comfy-temp-dir "${CE_COMFY_TEMP_DIR}" \
  --comfy-user-dir "${CE_COMFY_USER_DIR}" \
  --comfy-extra-models-config "${CE_COMFY_EXTRA_MODELS_CONFIG}" \
  --comfy-python "${CE_COMFY_PYTHON}" \
  --comfy-main-py "${CE_COMFY_MAIN_PY}" \
  --comfy-clip-vision-model "${CE_COMFY_CLIP_VISION_MODEL}" \
  --host "${CE_COMFY_HEADLESS_HOST}" \
  --port "${CE_COMFY_HEADLESS_PORT}" \
  --pid-file "${CE_COMFY_HEADLESS_PID_FILE}" \
  --log-file "${CE_COMFY_HEADLESS_LOG_FILE}" \
  "$@"
