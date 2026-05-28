#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
. "${SCRIPT_DIR}/lib.sh"

ce_load_config
ce_create_runtime_dirs

source_image="$(ce_abs_path "${CE_ROOT}/renders/controlled_typography/challenger_typography_smoke_input.png")"
shared_still_intent="$(ce_abs_path "${CE_ROOT}/workflows/typography/shared/challenger_mission_control_still.intent.json")"
shared_handoff_intent="$(ce_abs_path "${CE_ROOT}/workflows/typography/shared/challenger_mission_control_handoff_asset.intent.json")"

ce_require_file "${source_image}"
ce_require_file "${shared_still_intent}"
ce_require_file "${shared_handoff_intent}"

run_root="${CE_OUTPUTS_LOGS_DIR}/smoke-typography-$(ce_compact_timestamp_utc)"
mkdir -p "${run_root}"

shared_output="${run_root}/shared-still.png"
handoff_output="${run_root}/handoff-asset.png"

ce_info "Smoke: shared still intent -> apply/validate"
"${CE_ROOT}/scripts/typography.sh" apply \
  --target still \
  --artifact "${source_image}" \
  --intent "${shared_still_intent}" \
  --output "${shared_output}" \
  --debug-dir "${run_root}/shared-debug" >/dev/null
"${CE_ROOT}/scripts/typography.sh" validate \
  --target still \
  --artifact "${shared_output}" \
  --intent "${shared_still_intent}" >/dev/null

ce_info "Smoke: shared handoff intent -> apply and staged manifest propagation"
"${CE_ROOT}/scripts/typography.sh" apply \
  --target handoff_asset \
  --artifact "${source_image}" \
  --intent "${shared_handoff_intent}" \
  --output "${handoff_output}" >/dev/null
staged_asset="$(
  "${CE_ROOT}/scripts/handoff-stage.sh" "${source_image}" --from comfy --typography-intent "${shared_handoff_intent}" \
    | awk -F': ' '/^INFO  Staged asset: /{print $2}'
)"
[ -n "${staged_asset}" ] || ce_die "Smoke handoff-stage did not return a staged asset path."
staged_manifest="${staged_asset}.json"
ce_require_file "${staged_manifest}"
recorded_intent="$(ce_load_manifest_value "${staged_manifest}" typography_intent_path)"
[ "${recorded_intent}" = "${shared_handoff_intent}" ] || ce_die "Handoff staged manifest did not record typography_intent_path."

ce_info "Smoke: unimplemented sequence/video targets fail fast"
if "${CE_ROOT}/scripts/typography.sh" validate \
  --target video \
  --artifact "${source_image}" \
  --intent "${shared_handoff_intent}" >/dev/null 2>&1; then
  ce_die "Expected video typography validation to fail fast."
fi
if "${CE_ROOT}/scripts/typography.sh" validate \
  --target image_sequence \
  --artifact "${source_image}" \
  --intent "${shared_handoff_intent}" >/dev/null 2>&1; then
  ce_die "Expected image_sequence typography validation to fail fast."
fi

ce_info "Smoke typography complete: ${run_root}"
