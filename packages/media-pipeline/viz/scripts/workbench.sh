#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
. "${SCRIPT_DIR}/lib.sh"

ce_load_config
ce_create_runtime_dirs
ce_require_file "${CE_MLX_VIDEO_PYTHON}"

exec "${CE_MLX_VIDEO_PYTHON}" "${CE_ROOT}/scripts/workbench_tool.py" \
  --repo-root "${CE_ROOT}" \
  "$@"
