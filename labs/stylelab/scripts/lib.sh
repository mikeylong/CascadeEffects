#!/usr/bin/env bash
set -euo pipefail

SL_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SL_ROOT="$(cd "${SL_LIB_DIR}/.." && pwd)"

sl_load_config() {
  local config_file="${SL_ROOT}/config/paths.env"

  if [ -f "${config_file}" ]; then
    set -a
    # shellcheck disable=SC1090
    . "${config_file}"
    set +a
  fi

  : "${CE_HOME:=/Users/mike/AI}"
  : "${CE_MODELS_ROOT:=${CE_HOME}/models}"
  : "${CE_OUTPUTS_ROOT:=${CE_HOME}/outputs}"
  : "${CE_STYLELAB_PYTHON:=/Users/mike/AI/mlx-video/.venv/bin/python}"
  : "${CE_REFERENCES_RUNTIME_ROOT:=${SL_ROOT}/references}"

  SL_REQUIRED_DIRS=(
    "${SL_ROOT}/profiles"
    "${SL_ROOT}/scenes"
    "${SL_ROOT}/references"
    "${SL_ROOT}/renders"
    "${SL_ROOT}/exports"
    "${SL_ROOT}/boards"
    "${SL_ROOT}/evaluations"
    "${SL_ROOT}/tests"
  )
}

sl_create_runtime_dirs() {
  mkdir -p "${SL_REQUIRED_DIRS[@]}"
}

sl_require_file() {
  [ -f "$1" ] || {
    printf 'ERROR Required file not found: %s\n' "$1" >&2
    exit 1
  }
}
