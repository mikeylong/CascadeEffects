#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
. "${SCRIPT_DIR}/lib.sh"

ce_load_config
ce_create_runtime_dirs

exec "${CE_COMFY_PYTHON}" "${CE_ROOT}/scripts/typography_tool.py" \
  --repo-root "${CE_ROOT}" \
  --models-root "${CE_MODELS_ROOT}" \
  --comfy-workflows-dir "${CE_COMFY_WORKFLOWS_DIR}" \
  --comfy-output-dir "${CE_COMFY_OUTPUT_DIR}" \
  --references-root "${CE_REFERENCES_ROOT}" \
  "$@"
