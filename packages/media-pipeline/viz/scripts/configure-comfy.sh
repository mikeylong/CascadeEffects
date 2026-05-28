#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
. "${SCRIPT_DIR}/lib.sh"

ce_require_macos_apple_silicon
ce_comfy_installed || ce_die "ComfyUI Desktop is not installed. Run bin/ce bootstrap."
ce_require_dir "${CE_COMFY_SUPPORT_DIR}"
ce_require_dir "${CE_COMFY_INSTALL_ROOT}"
ce_require_file "${CE_ROOT}/config/comfy/extra_models_config.yaml.tmpl"

ce_info "Writing ComfyUI external model config to ${CE_COMFY_EXTRA_MODELS_CONFIG}"
ce_render_template \
  "${CE_ROOT}/config/comfy/extra_models_config.yaml.tmpl" \
  "${CE_COMFY_EXTRA_MODELS_CONFIG}"

ce_info "ComfyUI model-path configuration updated"
ce_info "Restart ComfyUI Desktop to pick up the shared model directories"

