#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
. "${SCRIPT_DIR}/lib.sh"

ce_require_macos_apple_silicon
ce_require_command brew
ce_require_command git

ce_info "Creating runtime directory tree under ${CE_HOME}"
ce_create_runtime_dirs

ce_brew_install_formula_if_missing uv
ce_brew_install_cask_if_missing comfyui
ce_refresh_hash

uv_bin="$(ce_uv_cmd)" || ce_die "uv is still unavailable after installation"

ce_info "Installing or upgrading MFLUX"
"${uv_bin}" tool install --upgrade mflux
ce_refresh_hash

ce_info "Initializing MLX lab project at ${CE_MLX_LAB_DIR}"
mkdir -p "${CE_MLX_LAB_DIR}"
if [ ! -f "${CE_MLX_LAB_DIR}/pyproject.toml" ]; then
  (
    cd "${CE_MLX_LAB_DIR}"
    "${uv_bin}" init
  )
else
  ce_info "MLX lab project already initialized"
fi
ce_set_project_name "${CE_MLX_LAB_DIR}/pyproject.toml" "cascadeeffects-mlx-lab-runtime"
(
  cd "${CE_MLX_LAB_DIR}"
  "${uv_bin}" add mlx
)

ce_info "Preparing mlx-video project at ${CE_MLX_VIDEO_DIR}"
mkdir -p "${CE_MLX_VIDEO_DIR}"
if [ ! -f "${CE_MLX_VIDEO_DIR}/pyproject.toml" ]; then
  (
    cd "${CE_MLX_VIDEO_DIR}"
    "${uv_bin}" init
  )
else
  ce_info "mlx-video project already initialized"
fi
ce_set_project_name "${CE_MLX_VIDEO_DIR}/pyproject.toml" "cascadeeffects-mlx-video-runtime"

printf '3.11\n' > "${CE_MLX_VIDEO_DIR}/.python-version"
"${uv_bin}" python install 3.11

(
  cd "${CE_MLX_VIDEO_DIR}"
  "${uv_bin}" add "mlx>=0.22"
  "${uv_bin}" add git+https://github.com/Blaizzy/mlx-video.git
)

ce_info "Bootstrap complete"
ce_info "Next manual step: launch ComfyUI Desktop once with MPS and install root ${CE_COMFY_INSTALL_ROOT}"
ce_info "Then run: bin/ce configure-comfy"
