#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
. "${SCRIPT_DIR}/lib.sh"

ce_load_config
ce_create_runtime_dirs
ce_require_file "${CE_MLX_VIDEO_PYTHON}"

exec "${CE_MLX_VIDEO_PYTHON}" "${CE_ROOT}/scripts/video_backend_tool.py" \
  --repo-root "${CE_ROOT}" \
  --mlx-video-dir "${CE_MLX_VIDEO_DIR}" \
  --prepared-root "${CE_MLX_VIDEO_PREPARED_ROOT}" \
  --hf-home "${CE_HF_HOME}" \
  --hf-hub-cache "${CE_HF_HUB_CACHE}" \
  "$@"
