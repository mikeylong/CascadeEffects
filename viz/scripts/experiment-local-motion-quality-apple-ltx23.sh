#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
. "${SCRIPT_DIR}/lib.sh"

ce_load_config
ce_create_runtime_dirs

repo_python="$(ce_repo_python)"

exec "${repo_python}" "${CE_ROOT}/scripts/local_motion_quality_apple_ltx23_tool.py" \
  --repo-root "${CE_ROOT}" \
  "$@"
