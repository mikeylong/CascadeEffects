#!/usr/bin/env bash
set -euo pipefail

CE_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CE_ROOT="$(cd "${CE_LIB_DIR}/.." && pwd)"
CE_REPO_VENV_PYTHON="${CE_ROOT}/.venv/bin/python"

ce_load_config() {
  local config_file="${CE_ROOT}/config/paths.env"

  if [ -f "${config_file}" ]; then
    set -a
    # shellcheck disable=SC1090
    . "${config_file}"
    set +a
  fi

  : "${CE_HOME:=/Users/mike/AI}"
  : "${CE_MODELS_ROOT:=${CE_HOME}/models}"
  : "${CE_COMFY_INSTALL_ROOT:=${CE_HOME}/comfy}"
  : "${CE_COMFY_USER_DIR:=${CE_COMFY_INSTALL_ROOT}/user}"
  : "${CE_COMFY_INPUT_DIR:=${CE_COMFY_INSTALL_ROOT}/input}"
  : "${CE_COMFY_OUTPUT_DIR:=${CE_COMFY_INSTALL_ROOT}/output}"
  : "${CE_COMFY_TEMP_DIR:=${CE_COMFY_INSTALL_ROOT}/temp}"
  : "${CE_MLX_LAB_DIR:=${CE_HOME}/mlx-lab}"
  : "${CE_MLX_VIDEO_DIR:=${CE_HOME}/mlx-video}"
  : "${CE_MLX_VIDEO_PYTHON:=${CE_MLX_VIDEO_DIR}/.venv/bin/python}"
  : "${CE_MLX_VIDEO_PREPARED_ROOT:=${CE_MODELS_ROOT}/mlx-video/prepared}"
  : "${CE_OUTPUTS_DIR:=${CE_HOME}/outputs}"
  : "${CE_OUTPUTS_COMFY_DIR:=${CE_OUTPUTS_DIR}/comfy}"
  : "${CE_OUTPUTS_MLX_IMAGES_DIR:=${CE_OUTPUTS_DIR}/mlx-images}"
  : "${CE_OUTPUTS_MLX_VIDEO_DIR:=${CE_OUTPUTS_DIR}/mlx-video}"
  : "${CE_OUTPUTS_HANDOFF_DIR:=${CE_OUTPUTS_DIR}/handoff}"
  : "${CE_OUTPUTS_LOGS_DIR:=${CE_OUTPUTS_DIR}/logs}"
  : "${CE_HF_HOME:=${CE_HOME}/cache/huggingface}"
  : "${CE_HF_HUB_CACHE:=${CE_HF_HOME}/hub}"
  : "${CE_LTX23_MLX_DIR:=${CE_HOME}/ltx-2-mlx}"
  : "${CE_LTX23_MLX_MODEL_REPO:=dgrauet/ltx-2.3-mlx-q8}"
  : "${CE_LTX23_MLX_GEMMA_REPO:=mlx-community/gemma-3-12b-it-4bit}"
  : "${CE_LTX23_MLX_HF_HOME:=${HOME}/.cache/huggingface}"
  : "${CE_LTX23_MLX_HF_HUB_CACHE:=${CE_LTX23_MLX_HF_HOME}/hub}"
  : "${CE_COMFY_WORKFLOWS_DIR:=${CE_COMFY_INSTALL_ROOT}/user/default/workflows}"
  : "${CE_COMFY_SUPPORT_DIR:=${HOME}/Library/Application Support/ComfyUI}"
  : "${CE_COMFY_EXTRA_MODELS_CONFIG:=${CE_COMFY_SUPPORT_DIR}/extra_models_config.yaml}"
  : "${CE_COMFY_HEADLESS_HOST:=127.0.0.1}"
  : "${CE_COMFY_HEADLESS_PORT:=8188}"
  : "${CE_COMFY_HEADLESS_URL:=http://${CE_COMFY_HEADLESS_HOST}:${CE_COMFY_HEADLESS_PORT}}"
  : "${CE_COMFY_HEADLESS_PID_FILE:=${CE_OUTPUTS_LOGS_DIR}/ce-comfy-headless.pid}"
  : "${CE_COMFY_HEADLESS_LOG_FILE:=${CE_OUTPUTS_LOGS_DIR}/ce-comfy-headless.log}"
  : "${CE_COMFY_SOURCE_ROOT:=${CE_COMFY_APP_ROOT:-${CE_COMFY_INSTALL_ROOT}/ComfyUI}}"
  : "${CE_COMFY_MAIN_PY:=${CE_COMFY_SOURCE_ROOT}/main.py}"
  : "${CE_COMFY_PYTHON:=${CE_COMFY_INSTALL_ROOT}/.venv/bin/python}"
  : "${CE_COMFY_CLIP_VISION_MODEL:=}"
  : "${CE_REFERENCES_ROOT:=${CE_ROOT}/references}"
  : "${CE_MLX_VIDEO_MODEL_REPO:=mlx-community/LTX-2-distilled-bf16}"
  : "${CE_MLX_VIDEO_TEXT_ENCODER_REPO:=}"

  CE_REQUIRED_DIRS=(
    "${CE_MODELS_ROOT}"
    "${CE_MODELS_ROOT}/checkpoints"
    "${CE_MODELS_ROOT}/loras"
    "${CE_MODELS_ROOT}/vae"
    "${CE_MODELS_ROOT}/text_encoders"
    "${CE_MODELS_ROOT}/diffusion_models"
    "${CE_MODELS_ROOT}/clip_vision"
    "${CE_MODELS_ROOT}/style_models"
    "${CE_MODELS_ROOT}/controlnet"
    "${CE_MODELS_ROOT}/upscale_models"
    "${CE_MODELS_ROOT}/latent_upscale_models"
    "${CE_COMFY_INSTALL_ROOT}"
    "${CE_COMFY_USER_DIR}"
    "${CE_COMFY_INPUT_DIR}"
    "${CE_COMFY_OUTPUT_DIR}"
    "${CE_COMFY_TEMP_DIR}"
    "${CE_MLX_LAB_DIR}"
    "${CE_MLX_VIDEO_DIR}"
    "${CE_MLX_VIDEO_PREPARED_ROOT}"
    "${CE_OUTPUTS_COMFY_DIR}"
    "${CE_OUTPUTS_MLX_IMAGES_DIR}"
    "${CE_OUTPUTS_MLX_VIDEO_DIR}"
    "${CE_OUTPUTS_HANDOFF_DIR}"
    "${CE_OUTPUTS_LOGS_DIR}"
    "${CE_HF_HOME}"
    "${CE_HF_HUB_CACHE}"
    "${CE_COMFY_WORKFLOWS_DIR}"
    "${CE_REFERENCES_ROOT}"
  )
}

ce_log() {
  printf '%s\n' "$*"
}

ce_info() {
  printf 'INFO  %s\n' "$*"
}

ce_warn() {
  printf 'WARN  %s\n' "$*" >&2
}

ce_die() {
  printf 'ERROR %s\n' "$*" >&2
  exit 1
}

ce_is_macos() {
  [ "$(uname -s)" = "Darwin" ]
}

ce_is_apple_silicon() {
  [ "$(uname -m)" = "arm64" ]
}

ce_require_macos_apple_silicon() {
  ce_is_macos || ce_die "This workspace is intended for macOS."
  ce_is_apple_silicon || ce_die "This workspace requires Apple Silicon."
}

ce_require_command() {
  local cmd="$1"
  command -v "${cmd}" >/dev/null 2>&1 || ce_die "Missing required command: ${cmd}"
}

ce_find_cmd() {
  local name="$1"

  if command -v "${name}" >/dev/null 2>&1; then
    command -v "${name}"
    return 0
  fi

  if [ -x "${HOME}/.local/bin/${name}" ]; then
    printf '%s\n' "${HOME}/.local/bin/${name}"
    return 0
  fi

  return 1
}

ce_repo_python() {
  if [ -x "${CE_REPO_VENV_PYTHON}" ]; then
    printf '%s\n' "${CE_REPO_VENV_PYTHON}"
    return 0
  fi

  ce_require_command python3
  command -v python3
}

ce_refresh_hash() {
  hash -r 2>/dev/null || true
}

ce_abs_path() {
  python3 - "$1" <<'PY'
from pathlib import Path
import sys

print(Path(sys.argv[1]).expanduser().resolve())
PY
}

ce_abs_path_preserve_links() {
  python3 - "$1" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1]).expanduser()
if not path.is_absolute():
    path = Path.cwd() / path
print(path)
PY
}

ce_timestamp_utc() {
  date -u '+%Y-%m-%dT%H:%M:%SZ'
}

ce_compact_timestamp_utc() {
  date -u '+%Y%m%dT%H%M%SZ'
}

ce_uuid() {
  python3 - <<'PY'
import uuid

print(uuid.uuid4())
PY
}

ce_slug_component() {
  python3 - "$1" <<'PY'
import re
import sys
from pathlib import Path

name = Path(sys.argv[1]).name
name = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-")
print(name or "asset")
PY
}

ce_read_prompt_file() {
  local prompt_file="$1"
  [ -f "${prompt_file}" ] || ce_die "Prompt file not found: ${prompt_file}"

  python3 - "${prompt_file}" <<'PY'
from pathlib import Path
import sys

text = Path(sys.argv[1]).read_text(encoding="utf-8").strip()
print(" ".join(text.split()))
PY
}

ce_brew_has_formula() {
  brew list --formula "$1" >/dev/null 2>&1
}

ce_brew_has_cask() {
  brew list --cask "$1" >/dev/null 2>&1
}

ce_brew_install_formula_if_missing() {
  local formula="$1"

  if ce_brew_has_formula "${formula}"; then
    ce_info "Homebrew formula already installed: ${formula}"
    return 0
  fi

  ce_info "Installing Homebrew formula: ${formula}"
  brew install "${formula}"
}

ce_brew_install_cask_if_missing() {
  local cask="$1"

  if ce_brew_has_cask "${cask}"; then
    ce_info "Homebrew cask already installed: ${cask}"
    return 0
  fi

  ce_info "Installing Homebrew cask: ${cask}"
  brew install --cask "${cask}"
}

ce_uv_cmd() {
  if ce_find_cmd uv >/dev/null 2>&1; then
    ce_find_cmd uv
    return 0
  fi

  return 1
}

ce_mflux_cmd() {
  if ce_find_cmd mflux-generate-z-image-turbo >/dev/null 2>&1; then
    ce_find_cmd mflux-generate-z-image-turbo
    return 0
  fi

  return 1
}

ce_comfy_installed() {
  [ -f "${CE_COMFY_MAIN_PY}" ]
}

ce_create_runtime_dirs() {
  mkdir -p "${CE_REQUIRED_DIRS[@]}"
}

ce_render_template() {
  local template_path="$1"
  local destination_path="$2"

  python3 - "${template_path}" "${destination_path}" <<'PY'
import os
import sys
from pathlib import Path

template_path = Path(sys.argv[1])
destination_path = Path(sys.argv[2])
content = template_path.read_text(encoding="utf-8")

for key, value in os.environ.items():
    content = content.replace(f"__{key}__", value)

destination_path.parent.mkdir(parents=True, exist_ok=True)
destination_path.write_text(content, encoding="utf-8")
PY
}

ce_set_project_name() {
  local pyproject_path="$1"
  local project_name="$2"

  python3 - "${pyproject_path}" "${project_name}" <<'PY'
import sys
from pathlib import Path

pyproject_path = Path(sys.argv[1])
project_name = sys.argv[2]
lines = pyproject_path.read_text(encoding="utf-8").splitlines(keepends=True)

inside_project = False
updated = False

for index, line in enumerate(lines):
    stripped = line.strip()
    if stripped == "[project]":
        inside_project = True
        continue
    if inside_project and stripped.startswith("[") and stripped != "[project]":
        break
    if inside_project and stripped.startswith("name = "):
        lines[index] = f'name = "{project_name}"\n'
        updated = True
        break

if not updated:
    raise SystemExit(f"Could not update [project].name in {pyproject_path}")

pyproject_path.write_text("".join(lines), encoding="utf-8")
PY
}

ce_require_file() {
  [ -f "$1" ] || ce_die "Required file not found: $1"
}

ce_require_dir() {
  [ -d "$1" ] || ce_die "Required directory not found: $1"
}

ce_run_uv_project() {
  local project_dir="$1"
  shift
  local uv_bin

  uv_bin="$(ce_uv_cmd)" || ce_die "uv is not installed. Run bin/ce bootstrap."
  ce_require_dir "${project_dir}"

  (
    cd "${project_dir}"
    "${uv_bin}" run "$@"
  )
}

ce_run_mlx_video_generate() {
  local project_dir="$1"
  shift
  ce_run_uv_project "${project_dir}" python -m mlx_video.models.ltx_2.generate "$@"
}

ce_load_manifest_value() {
  local manifest_path="$1"
  local field_name="$2"

  python3 - "${manifest_path}" "${field_name}" <<'PY'
import json
import sys
from pathlib import Path

manifest = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
value = manifest.get(sys.argv[2], "")
print("" if value is None else value)
PY
}

ce_load_config
