#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
. "${SCRIPT_DIR}/lib.sh"

failures=0

pass() {
  printf 'PASS  %s\n' "$1"
}

fail() {
  printf 'FAIL  %s\n' "$1"
  failures=$((failures + 1))
}

note() {
  printf 'INFO  %s\n' "$1"
}

if ce_is_macos; then
  pass "macOS detected: $(sw_vers -productVersion)"
else
  fail "macOS required"
fi

if ce_is_apple_silicon; then
  pass "Apple Silicon detected: $(uname -m)"
else
  fail "Apple Silicon required"
fi

if command -v brew >/dev/null 2>&1; then
  pass "Homebrew available: $(command -v brew)"
else
  fail "Homebrew missing"
fi

if command -v git >/dev/null 2>&1; then
  pass "Git available: $(command -v git)"
else
  fail "Git missing"
fi

if uv_path="$(ce_uv_cmd 2>/dev/null)"; then
  pass "uv available: ${uv_path}"
else
  fail "uv not installed; run bin/ce bootstrap"
fi

if ce_comfy_installed; then
  pass "ComfyUI Desktop installed"
else
  fail "ComfyUI Desktop not installed; run bin/ce bootstrap"
fi

if [ -d "${CE_HOME}" ]; then
  pass "Runtime root exists: ${CE_HOME}"
else
  fail "Runtime root missing: ${CE_HOME}"
fi

if [ -d "${CE_COMFY_OUTPUT_DIR}" ]; then
  pass "Comfy output directory exists: ${CE_COMFY_OUTPUT_DIR}"
else
  fail "Comfy output directory missing: ${CE_COMFY_OUTPUT_DIR}"
fi

missing_dirs=()
for path in "${CE_REQUIRED_DIRS[@]}"; do
  if [ ! -d "${path}" ]; then
    missing_dirs+=("${path}")
  fi
done

if [ "${#missing_dirs[@]}" -eq 0 ]; then
  pass "Expected runtime directories are present"
else
  fail "Missing runtime directories: ${missing_dirs[*]}"
fi

if [ -d "${CE_COMFY_SUPPORT_DIR}" ]; then
  pass "ComfyUI support directory exists: ${CE_COMFY_SUPPORT_DIR}"
else
  fail "ComfyUI support directory missing; launch ComfyUI Desktop once"
fi

if [ -f "${CE_COMFY_EXTRA_MODELS_CONFIG}" ]; then
  pass "ComfyUI external model config present: ${CE_COMFY_EXTRA_MODELS_CONFIG}"
else
  fail "ComfyUI external model config missing; run bin/ce configure-comfy after first launch"
fi

if [ -d "${CE_REFERENCES_ROOT}" ]; then
  pass "Reference root exists: ${CE_REFERENCES_ROOT}"
else
  fail "Reference root missing: ${CE_REFERENCES_ROOT}"
fi

if mflux_path="$(ce_mflux_cmd 2>/dev/null)"; then
  pass "MFLUX image command available: ${mflux_path}"
else
  fail "MFLUX CLI missing; run bin/ce bootstrap"
fi

if [ -f "${CE_MLX_LAB_DIR}/pyproject.toml" ]; then
  pass "MLX lab project initialized"
else
  fail "MLX lab project missing: ${CE_MLX_LAB_DIR}/pyproject.toml"
fi

if [ -f "${CE_MLX_VIDEO_DIR}/pyproject.toml" ]; then
  pass "mlx-video project initialized"
else
  fail "mlx-video project missing: ${CE_MLX_VIDEO_DIR}/pyproject.toml"
fi

if uv_path="$(ce_uv_cmd 2>/dev/null)"; then
  if [ -f "${CE_MLX_LAB_DIR}/pyproject.toml" ]; then
    if (cd "${CE_MLX_LAB_DIR}" && "${uv_path}" run python -c "import mlx.core as mx; print(mx.arange(4).shape)") >/dev/null 2>&1; then
      pass "MLX lab runtime import check passed"
    else
      fail "MLX lab runtime import check failed"
    fi
  else
    note "Skipping MLX lab runtime import check until project exists"
  fi

  if [ -f "${CE_MLX_VIDEO_DIR}/pyproject.toml" ]; then
    if (cd "${CE_MLX_VIDEO_DIR}" && "${uv_path}" run python -c "import mlx_video; print(mlx_video.__file__)") >/dev/null 2>&1; then
      pass "mlx-video import check passed"
    else
      fail "mlx-video import check failed"
    fi
  else
    note "Skipping mlx-video import check until project exists"
  fi
fi

if [ -f "${CE_MODELS_ROOT}/upscale_models/RealESRGAN_x4plus.pth" ]; then
  pass "Shared upscale model installed: RealESRGAN_x4plus.pth"
else
  note "Optional quality asset missing: ${CE_MODELS_ROOT}/upscale_models/RealESRGAN_x4plus.pth"
fi

full_flux_missing=()
for path in \
  "${CE_MODELS_ROOT}/diffusion_models/flux2-dev.safetensors" \
  "${CE_MODELS_ROOT}/text_encoders/mistral_3_small_flux2_bf16.safetensors" \
  "${CE_MODELS_ROOT}/text_encoders/clip_l.safetensors" \
  "${CE_MODELS_ROOT}/vae/flux2-vae.safetensors"
do
  if [ ! -f "${path}" ]; then
    full_flux_missing+=("${path}")
  fi
done

if [ "${#full_flux_missing[@]}" -eq 0 ]; then
  pass "Full FLUX2 still-generation assets present"
else
  note "Optional quality assets missing: ${full_flux_missing[*]}"
fi

enabled_repair_specs=()
if [ -d "${CE_ROOT}/workflows/source_text_repair" ]; then
  while IFS= read -r line; do
    [ -n "${line}" ] && enabled_repair_specs+=("${line}")
  done < <(CE_ROOT="${CE_ROOT}" python3 - <<'PY'
import json
import os
from pathlib import Path

root = Path(os.environ["CE_ROOT"]) / "workflows" / "source_text_repair"
if root.exists():
    for path in sorted(root.rglob("*.json")):
        try:
            data = json.loads(path.read_text())
        except Exception:
            continue
        if bool(data.get("enabled")) and str(data.get("llm_backend", "")).strip() == "ollama":
            print(f"{path}|{str(data.get('llm_model', '')).strip()}")
PY
)
fi

if [ "${#enabled_repair_specs[@]}" -gt 0 ]; then
  if command -v ollama >/dev/null 2>&1; then
    pass "Ollama available for enabled source-text repair policies: $(command -v ollama)"
    checked_models=()
    for item in "${enabled_repair_specs[@]}"; do
      policy_path="${item%%|*}"
      model_name="${item#*|}"
      checked_joined="${checked_models[*]-}"
      if [[ " ${checked_joined} " == *" ${model_name} "* ]]; then
        continue
      fi
      checked_models+=("${model_name}")
      if ollama show "${model_name}" >/dev/null 2>&1; then
        pass "Ollama model available for ${policy_path}: ${model_name}"
      else
        fail "Enabled source-text repair policy requires missing Ollama model ${model_name}: ${policy_path}"
      fi
    done
  else
    fail "Enabled source-text repair policy requires ollama, but it is not installed"
  fi
else
  note "No enabled source-text repair policies configured"
fi

if [ "${failures}" -gt 0 ]; then
  printf 'FAIL  doctor completed with %d failing check(s)\n' "${failures}"
  exit 1
fi

printf 'PASS  doctor completed with no failing checks\n'
