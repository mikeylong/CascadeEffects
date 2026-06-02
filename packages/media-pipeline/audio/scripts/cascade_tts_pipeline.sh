#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

PIPELINE_DIR="${PIPELINE_DIR:-$ROOT_DIR/tmp/speech_emotive}"
AUDITION_JOBS="${AUDITION_JOBS:-$PIPELINE_DIR/audition_jobs.jsonl}"
FINAL_JOBS="${FINAL_JOBS:-$PIPELINE_DIR/final_jobs.jsonl}"
AUDITION_OUT_DIR="${AUDITION_OUT_DIR:-$ROOT_DIR/output/speech/auditions}"
RENDER_OUT_DIR="${RENDER_OUT_DIR:-$PIPELINE_DIR/rendered}"
PROSODY_GUARD_DIR="${PROSODY_GUARD_DIR:-$PIPELINE_DIR/prosody_guard}"
MASTER_OUT="${MASTER_OUT:-$ROOT_DIR/output/speech/ep3_narration_emotive_v2.wav}"
TRANSCRIPT_OUT_DIR="${TRANSCRIPT_OUT_DIR:-$ROOT_DIR/tmp/transcripts_final}"
TTS_PROVIDER="${TTS_PROVIDER:-elevenlabs}"
VOICE="${VOICE:-cedar}"
OPENAI_DEFAULT_MODEL="${OPENAI_DEFAULT_MODEL:-gpt-4o-mini-tts-2025-12-15}"
ELEVENLABS_DEFAULT_MODEL="${ELEVENLABS_DEFAULT_MODEL:-}"
MODEL="${MODEL:-}"
RESPONSE_FORMAT="${RESPONSE_FORMAT:-wav}"
PREMASTER_OUT="${PREMASTER_OUT:-$PIPELINE_DIR/premaster.$RESPONSE_FORMAT}"
MASTERING_DIR="${MASTERING_DIR:-$PIPELINE_DIR/mastering}"
MASTERING_ENABLED="${MASTERING_ENABLED:-1}"
LOUDNESS_TARGET_I="${LOUDNESS_TARGET_I:--14}"
LOUDNESS_TARGET_TP="${LOUDNESS_TARGET_TP:--1.0}"
LOUDNESS_TARGET_LRA="${LOUDNESS_TARGET_LRA:-11}"
EPISODE_DIR="${EPISODE_DIR:-}"
EPISODE_SCRIPT="${EPISODE_SCRIPT:-}"
EPISODE_FINAL_OUT="${EPISODE_FINAL_OUT:-}"
AUDIO_PACKAGE_PATH="${AUDIO_PACKAGE_PATH:-}"
REQUIRE_CANONICAL_CUE_TAGS="${REQUIRE_CANONICAL_CUE_TAGS:-1}"
ELEVENLABS_STRICT_SOURCE_ALIGNMENT="${ELEVENLABS_STRICT_SOURCE_ALIGNMENT:-1}"
ENV_FILE="${ENV_FILE:-$ROOT_DIR/.env.local}"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
TTS_GEN="${TTS_GEN:-$CODEX_HOME/skills/speech/scripts/text_to_speech.py}"
ELEVENLABS_HELPER="${ELEVENLABS_HELPER:-$ROOT_DIR/scripts/elevenlabs_provider.py}"
ELEVENLABS_OUTPUT_FORMAT="${ELEVENLABS_OUTPUT_FORMAT:-wav_44100}"
PRONUNCIATION_PREFLIGHT_HELPER="${PRONUNCIATION_PREFLIGHT_HELPER:-$ROOT_DIR/scripts/pronunciation_preflight.py}"
ELEVENLABS_PRONUNCIATION_LEXICON="${ELEVENLABS_PRONUNCIATION_LEXICON:-$ROOT_DIR/references/pronunciation/known_risks_v1.json}"
SHORTS_VOICE_PROFILE_REGISTRY="${SHORTS_VOICE_PROFILE_REGISTRY:-$ROOT_DIR/references/voice_profiles/youtube_shorts_voice_profiles.json}"
SHORT_AUDIO_VOICE_PROFILE_ID="${SHORT_AUDIO_VOICE_PROFILE_ID:-}"
SIBILANCE_HELPER="${SIBILANCE_HELPER:-$ROOT_DIR/scripts/sibilance_workflow.py}"
SIBILANCE_MASTER="${SIBILANCE_MASTER:-}"
SIBILANCE_REPORT="${SIBILANCE_REPORT:-$PIPELINE_DIR/sibilance_hotspots.json}"
SIBILANCE_AUDITION_JOBS="${SIBILANCE_AUDITION_JOBS:-$PIPELINE_DIR/sibilance_audition_jobs.jsonl}"
SIBILANCE_AUDITION_OUT_DIR="${SIBILANCE_AUDITION_OUT_DIR:-$PIPELINE_DIR/sibilance_auditions}"
SIBILANCE_AUDITION_STAGE="${SIBILANCE_AUDITION_STAGE:-first-pass}"
SIBILANCE_TOP_N="${SIBILANCE_TOP_N:-8}"
SIBILANCE_SEED_TIMES="${SIBILANCE_SEED_TIMES:-}"
SIBILANCE_SEED_TOLERANCE="${SIBILANCE_SEED_TOLERANCE:-1.0}"
SIBILANCE_WINNER_VOICE="${SIBILANCE_WINNER_VOICE:-}"
OPENAI_PYTHON_SPEC="${OPENAI_PYTHON_SPEC:-git+https://github.com/openai/openai-python.git}"
ESTIMATED_USD_PER_MILLION_CHARS="${ESTIMATED_USD_PER_MILLION_CHARS:-15.0}"
ELEVENLABS_ESTIMATED_USD_PER_MILLION_CHARS="${ELEVENLABS_ESTIMATED_USD_PER_MILLION_CHARS:-198.4126984126984}"
ELEVENLABS_MAX_INPUT_CHARS="${ELEVENLABS_MAX_INPUT_CHARS:-3000}"
ELEVENLABS_CONTINUITY_CHARS="${ELEVENLABS_CONTINUITY_CHARS:-400}"
WARMUP_HELPER="${WARMUP_HELPER:-$ROOT_DIR/scripts/warmup_trim.py}"
WARMUP_TRIM_DIR="${WARMUP_TRIM_DIR:-$PIPELINE_DIR/warmup_trim}"
WARMUP_TRANSCRIBE_MODEL="${WARMUP_TRANSCRIBE_MODEL:-small}"
CANONICAL_CUE_TAGS=(
  calm
  deliberate
  matter-of-fact
  flatly
  sorrowful
  resigned
  frustrated
  nervous
  pauses
)

usage() {
  cat <<EOF
Usage: $(basename "$0") <command>

Commands:
  validate   Validate the standard full-render JSONL manifest.
  cost       Estimate standard full-render cost and optional audition extra.
  audition   Render the opening audition set when you explicitly want one.
  render     Render the full chunked episode.
  guard      Detect and auto-repair likely unintended prosody spikes.
  merge      Merge rendered chunks and package the canonical episode final.
  qa         Run local transcription QA on the packaged canonical final.
  sibilance-analyze  Rank likely sibilance hotspots in a packaged master.
  sibilance-audition Build and render hotspot comparison clips.
  all        Run validate -> cost -> render -> guard -> merge -> qa.
  help       Show this help text.

Key environment overrides:
  PIPELINE_DIR                  Default: $PIPELINE_DIR
  AUDITION_JOBS                 Default: $AUDITION_JOBS
  FINAL_JOBS                    Default: $FINAL_JOBS
  AUDITION_OUT_DIR              Default: $AUDITION_OUT_DIR
  RENDER_OUT_DIR                Default: $RENDER_OUT_DIR
  PROSODY_GUARD_DIR             Default: $PROSODY_GUARD_DIR
  MASTER_OUT                    Default: $MASTER_OUT
  PREMASTER_OUT                 Default: $PREMASTER_OUT
  MASTERING_DIR                 Default: $MASTERING_DIR
  TRANSCRIPT_OUT_DIR            Default: $TRANSCRIPT_OUT_DIR
  TTS_PROVIDER                  Default: $TTS_PROVIDER (elevenlabs|openai)
  VOICE                         Default: $VOICE
  MODEL                         Default: provider default (openai=$OPENAI_DEFAULT_MODEL, elevenlabs=ELEVENLABS_DEFAULT_MODEL from env)
  RESPONSE_FORMAT               Default: $RESPONSE_FORMAT
  ELEVENLABS_OUTPUT_FORMAT      Default: $ELEVENLABS_OUTPUT_FORMAT
  ELEVENLABS_PRONUNCIATION_LEXICON Default: $ELEVENLABS_PRONUNCIATION_LEXICON
  MASTERING_ENABLED             Default: $MASTERING_ENABLED
  LOUDNESS_TARGET_I             Default: $LOUDNESS_TARGET_I
  LOUDNESS_TARGET_TP            Default: $LOUDNESS_TARGET_TP
  LOUDNESS_TARGET_LRA           Default: $LOUDNESS_TARGET_LRA
  EPISODE_DIR                   Default: (unset; required for merge, qa, all)
  EPISODE_SCRIPT                Default: <EPISODE_DIR>/<basename(EPISODE_DIR)>.txt
  EPISODE_FINAL_OUT             Default: <EPISODE_DIR>/final/<basename(EPISODE_DIR)>.wav
  AUDIO_PACKAGE_PATH            Default: <PIPELINE_DIR>/audio_package.json
  REQUIRE_CANONICAL_CUE_TAGS    Default: $REQUIRE_CANONICAL_CUE_TAGS (1|0)
  ELEVENLABS_STRICT_SOURCE_ALIGNMENT Default: $ELEVENLABS_STRICT_SOURCE_ALIGNMENT (1|0)
  WARMUP_TRIM_DIR               Default: $WARMUP_TRIM_DIR
  WARMUP_TRANSCRIBE_MODEL       Default: $WARMUP_TRANSCRIBE_MODEL
  SIBILANCE_MASTER              Default: canonical packaged final, else MASTER_OUT
  SIBILANCE_REPORT              Default: $SIBILANCE_REPORT
  SIBILANCE_AUDITION_JOBS       Default: $SIBILANCE_AUDITION_JOBS
  SIBILANCE_AUDITION_OUT_DIR    Default: $SIBILANCE_AUDITION_OUT_DIR
  SIBILANCE_AUDITION_STAGE      Default: $SIBILANCE_AUDITION_STAGE
  SIBILANCE_TOP_N               Default: $SIBILANCE_TOP_N
  SIBILANCE_SEED_TIMES          Default: (unset; comma-separated HH:MM:SS.mmm list)
  SIBILANCE_SEED_TOLERANCE      Default: $SIBILANCE_SEED_TOLERANCE
  SIBILANCE_WINNER_VOICE        Default: (unset; required for second-pass)
  ENV_FILE                      Default: $ENV_FILE
  ESTIMATED_USD_PER_MILLION_CHARS Default: $ESTIMATED_USD_PER_MILLION_CHARS
  ELEVENLABS_ESTIMATED_USD_PER_MILLION_CHARS Default: $ELEVENLABS_ESTIMATED_USD_PER_MILLION_CHARS
EOF
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

require_supported_response_format() {
  case "$RESPONSE_FORMAT" in
    wav|flac)
      ;;
    *)
      echo "Unsupported RESPONSE_FORMAT: $RESPONSE_FORMAT (supported: wav, flac)" >&2
      exit 1
      ;;
  esac
}

require_supported_provider() {
  case "$TTS_PROVIDER" in
    openai|elevenlabs)
      ;;
    *)
      echo "Unsupported TTS_PROVIDER: $TTS_PROVIDER (supported: openai, elevenlabs)" >&2
      exit 1
      ;;
  esac
}

require_master_out_matches_format() {
  local master_ext
  master_ext="${MASTER_OUT##*.}"
  master_ext="$(printf '%s' "$master_ext" | tr '[:upper:]' '[:lower:]')"
  if [[ "$master_ext" != "$RESPONSE_FORMAT" ]]; then
    echo "MASTER_OUT extension .$master_ext does not match RESPONSE_FORMAT=$RESPONSE_FORMAT" >&2
    exit 1
  fi
}

require_premaster_out_matches_format() {
  local premaster_ext
  premaster_ext="${PREMASTER_OUT##*.}"
  premaster_ext="$(printf '%s' "$premaster_ext" | tr '[:upper:]' '[:lower:]')"
  if [[ "$premaster_ext" != "$RESPONSE_FORMAT" ]]; then
    echo "PREMASTER_OUT extension .$premaster_ext does not match RESPONSE_FORMAT=$RESPONSE_FORMAT" >&2
    exit 1
  fi
}

require_distinct_premaster_if_mastering() {
  if [[ "$MASTERING_ENABLED" == "1" && "$PREMASTER_OUT" == "$MASTER_OUT" ]]; then
    echo "PREMASTER_OUT must be different from MASTER_OUT when MASTERING_ENABLED=1" >&2
    exit 1
  fi
}

require_episode_dir() {
  if [[ -z "$EPISODE_DIR" ]]; then
    echo "EPISODE_DIR is required for release commands (merge, qa, all)." >&2
    exit 1
  fi
  if [[ ! -d "$EPISODE_DIR" ]]; then
    echo "EPISODE_DIR does not exist or is not a directory: $EPISODE_DIR" >&2
    exit 1
  fi
}

episode_dir_name() {
  local trimmed
  trimmed="${EPISODE_DIR%/}"
  basename "$trimmed"
}

canonical_episode_script_path() {
  local episode_name
  episode_name="$(episode_dir_name)"
  if [[ -n "$EPISODE_SCRIPT" ]]; then
    printf '%s\n' "$EPISODE_SCRIPT"
  else
    printf '%s/%s.txt\n' "${EPISODE_DIR%/}" "$episode_name"
  fi
}

canonical_episode_final_dir() {
  if [[ -n "$EPISODE_FINAL_OUT" ]]; then
    dirname "$EPISODE_FINAL_OUT"
    return
  fi
  printf '%s/final\n' "${EPISODE_DIR%/}"
}

canonical_episode_final_out() {
  local episode_name
  if [[ -n "$EPISODE_FINAL_OUT" ]]; then
    printf '%s\n' "$EPISODE_FINAL_OUT"
    return
  fi
  episode_name="$(episode_dir_name)"
  printf '%s/final/%s.wav\n' "${EPISODE_DIR%/}" "$episode_name"
}

audio_package_metadata_path() {
  if [[ -n "$AUDIO_PACKAGE_PATH" ]]; then
    printf '%s\n' "$AUDIO_PACKAGE_PATH"
    return
  fi
  printf '%s/audio_package.json\n' "${PIPELINE_DIR%/}"
}

source_env_file_if_present() {
  if [[ -f "$ENV_FILE" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a
  fi
}

file_sha256() {
  python3 - "$1" <<'PY'
import hashlib
import sys
from pathlib import Path

path = Path(sys.argv[1])
digest = hashlib.sha256()
with path.open("rb") as handle:
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
        digest.update(chunk)
print(digest.hexdigest())
PY
}

audio_package_effective_manifest_path() {
  if [[ "$TTS_PROVIDER" == "elevenlabs" ]]; then
    local candidate="$PIPELINE_DIR/effective_final_jobs.elevenlabs.jsonl"
    if [[ -f "$candidate" ]]; then
      printf '%s\n' "$candidate"
      return
    fi
    printf '\n'
    return
  fi
  printf '%s\n' "$FINAL_JOBS"
}

run_pronunciation_preflight_scan() {
  local manifest="$1"
  if [[ "$TTS_PROVIDER" != "elevenlabs" ]]; then
    return
  fi
  python3 "$PRONUNCIATION_PREFLIGHT_HELPER" scan \
    --manifest "$manifest" \
    --text-key input \
    --lexicon "$ELEVENLABS_PRONUNCIATION_LEXICON" >&2
}

run_pronunciation_preflight_verify_compiled() {
  local manifest="$1"
  if [[ "$TTS_PROVIDER" != "elevenlabs" ]]; then
    return
  fi
  python3 "$PRONUNCIATION_PREFLIGHT_HELPER" verify-compiled \
    --manifest "$manifest" \
    --lexicon "$ELEVENLABS_PRONUNCIATION_LEXICON" >&2
}

resolve_audio_package_voice() {
  source_env_file_if_present
  if [[ "$TTS_PROVIDER" == "elevenlabs" && -n "${ELEVEN_LABS_VOICE_ID:-}" ]]; then
    printf '%s\n' "$ELEVEN_LABS_VOICE_ID"
    return
  fi
  printf '%s\n' "$VOICE"
}

write_audio_package_sidecar() {
  local packaged_path="$1"
  local metadata_path
  local provider_voice
  local provider_model_id
  local effective_manifest
  local packaged_sha256
  local packaged_at
  local voice_profile_registry

  metadata_path="$(audio_package_metadata_path)"
  provider_voice="$(resolve_audio_package_voice)"
  provider_model_id="$(provider_model)"
  effective_manifest="$(audio_package_effective_manifest_path)"
  packaged_sha256="$(file_sha256 "$packaged_path")"
  packaged_at="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  voice_profile_registry="$SHORTS_VOICE_PROFILE_REGISTRY"

  python3 - "$metadata_path" "$TTS_PROVIDER" "$provider_voice" "$provider_model_id" "$effective_manifest" "$packaged_path" "$packaged_sha256" "$packaged_at" "$voice_profile_registry" "$RESPONSE_FORMAT" "$ELEVENLABS_OUTPUT_FORMAT" "$SHORT_AUDIO_VOICE_PROFILE_ID" <<'PY'
import json
import os
import sys
from pathlib import Path

metadata_path = Path(sys.argv[1])
metadata_path.parent.mkdir(parents=True, exist_ok=True)
provider = sys.argv[2]
voice = sys.argv[3]
model = sys.argv[4]
effective_manifest_path = sys.argv[5]
voice_profile_registry_path = Path(sys.argv[9]).expanduser()
response_format = sys.argv[10]
elevenlabs_output_format = sys.argv[11]
explicit_voice_profile_id = sys.argv[12].strip()

def load_first_effective_job(path_text):
    path = Path(path_text).expanduser()
    if not path.exists():
        return {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            loaded = json.loads(line)
        except json.JSONDecodeError:
            return {}
        return loaded if isinstance(loaded, dict) else {}
    return {}

def load_voice_profiles(path):
    if not path.exists():
        return {}
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    profiles = loaded.get("profiles", {})
    return profiles if isinstance(profiles, dict) else {}

def infer_voice_profile(profiles):
    if explicit_voice_profile_id:
        profile = profiles.get(explicit_voice_profile_id)
        return explicit_voice_profile_id, profile if isinstance(profile, dict) else {}
    matches = []
    for profile_id, profile in profiles.items():
        if not isinstance(profile, dict):
            continue
        if (
            str(profile.get("provider", "")).strip() == provider
            and str(profile.get("voice", "")).strip() == voice
            and str(profile.get("model", "")).strip() == model
        ):
            matches.append((str(profile_id), profile))
    if not matches:
        return "", {}
    matches.sort(key=lambda item: (not bool(item[1].get("final_export_eligible", False)), item[0]))
    return matches[0]

effective_job = load_first_effective_job(effective_manifest_path)
profiles = load_voice_profiles(voice_profile_registry_path)
voice_profile_id, voice_profile = infer_voice_profile(profiles)
voice_settings = effective_job.get("elevenlabs_voice_settings")
if not isinstance(voice_settings, dict):
    voice_settings = effective_job.get("voice_settings") if isinstance(effective_job.get("voice_settings"), dict) else {}
speed = effective_job.get("speed")
if speed is None and isinstance(voice_settings, dict):
    speed = voice_settings.get("speed")
render_settings = {
    "provider": provider,
    "voice": voice,
    "model": model,
    "response_format": response_format,
    "effective_manifest_path": effective_manifest_path,
}
if provider == "elevenlabs":
    applied_rules = effective_job.get("elevenlabs_pronunciation_applied_rules")
    if not isinstance(applied_rules, list):
        applied_rules = []
    render_settings.update(
        {
            "elevenlabs_output_format": elevenlabs_output_format,
            "elevenlabs_model_id": effective_job.get("elevenlabs_model_id", model),
            "elevenlabs_seed": effective_job.get("elevenlabs_seed"),
            "elevenlabs_apply_text_normalization": effective_job.get("elevenlabs_apply_text_normalization"),
            "elevenlabs_voice_settings": voice_settings,
            "speed": speed,
            "pronunciation_lexicon_path": effective_job.get("elevenlabs_pronunciation_lexicon_path", ""),
            "pronunciation_lexicon_sha256": effective_job.get("elevenlabs_pronunciation_lexicon_sha256", ""),
            "pronunciation_applied_rule_ids": sorted({str(item.get("rule_id")) for item in applied_rules if isinstance(item, dict) and item.get("rule_id")}),
            "pronunciation_dictionary_locators": effective_job.get("elevenlabs_pronunciation_dictionary_locators", []),
        }
    )

payload = {}
if metadata_path.exists():
    loaded = json.loads(metadata_path.read_text(encoding="utf-8"))
    if isinstance(loaded, dict):
        payload = loaded
payload.update(
    {
        "provider": provider,
        "voice": voice,
        "model": model,
        "voice_profile_id": voice_profile_id,
        "voice_profile_registry_path": str(voice_profile_registry_path) if voice_profile_registry_path.exists() else "",
        "voice_profile_settings": voice_profile.get("render_settings", {}) if isinstance(voice_profile, dict) else {},
        "voice_profile_final_export_eligible": bool(voice_profile.get("final_export_eligible", False)) if isinstance(voice_profile, dict) else False,
        "render_settings": render_settings,
        "effective_manifest_path": effective_manifest_path,
        "source_script_path": effective_job.get("source_script_path", ""),
        "source_script_sha256": effective_job.get("source_script_sha256", ""),
        "preflight_path": effective_job.get("preflight_path", ""),
        "preflight_sha256": effective_job.get("preflight_sha256", ""),
        "approval_receipt_path": effective_job.get("approval_receipt_path", ""),
        "approval_receipt_sha256": effective_job.get("approval_receipt_sha256", ""),
        "episode_id": effective_job.get("episode_id", ""),
        "chunk_count": effective_job.get("chunk_count", ""),
        "packaged_path": sys.argv[6],
        "master_audio_path": sys.argv[6],
        "packaged_sha256": sys.argv[7],
        "master_audio_sha256": sys.argv[7],
        "packaged_at": sys.argv[8],
    }
)
metadata_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
PY
}

append_audio_package_qa_sidecar() {
  local transcript_path="$1"
  local metadata_path
  local transcript_sha256
  local qa_completed_at

  metadata_path="$(audio_package_metadata_path)"
  transcript_sha256="$(file_sha256 "$transcript_path")"
  qa_completed_at="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

  python3 - "$metadata_path" "$transcript_path" "$transcript_sha256" "$qa_completed_at" <<'PY'
import json
import sys
from pathlib import Path

metadata_path = Path(sys.argv[1])
metadata_path.parent.mkdir(parents=True, exist_ok=True)
payload = {}
if metadata_path.exists():
    loaded = json.loads(metadata_path.read_text(encoding="utf-8"))
    if isinstance(loaded, dict):
        payload = loaded
payload.update(
    {
        "transcript_path": sys.argv[2],
        "transcript_sha256": sys.argv[3],
        "qa_completed_at": sys.argv[4],
    }
)
metadata_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
PY
}

find_generated_transcript_path() {
  local out_dir="$1"
  local qa_target="$2"
  local started_at_epoch="$3"
  python3 - "$out_dir" "$qa_target" "$started_at_epoch" <<'PY'
import sys
from pathlib import Path

out_dir = Path(sys.argv[1])
qa_target = Path(sys.argv[2])
started_at = float(sys.argv[3])
stem = qa_target.stem

if not out_dir.exists():
    raise SystemExit("Transcript output directory does not exist.")

candidates = [
    path
    for path in out_dir.rglob("*.txt")
    if path.is_file() and "logs" not in path.parts
]

def sort_key(path: Path) -> tuple[int, int, float, str]:
    name = path.name
    return (
        0 if name.startswith(stem) else 1,
        0 if name.endswith(".diarized.txt") else 1,
        -path.stat().st_mtime,
        str(path),
    )

recent = [path for path in candidates if path.stat().st_mtime >= started_at - 1]
search_space = recent or candidates
if not search_space:
    raise SystemExit("Could not find a QA transcript output.")

winner = sorted(search_space, key=sort_key)[0]
print(winner)
PY
}

canonical_cue_tags_display() {
  local tag
  local rendered=""
  for tag in "${CANONICAL_CUE_TAGS[@]}"; do
    if [[ -n "$rendered" ]]; then
      rendered+=", "
    fi
    rendered+="[$tag]"
  done
  printf '%s\n' "$rendered"
}

require_canonical_episode_script_cue_tags() {
  local script_path="$1"
  local allowed_tags
  local validation_output
  local validation_status

  allowed_tags="${CANONICAL_CUE_TAGS[*]}"
  if validation_output="$(
    awk -v allowed_tags="$allowed_tags" '
      BEGIN {
        tag_count = split(allowed_tags, tags, " ")
        for (i = 1; i <= tag_count; i++) {
          allowed[tags[i]] = 1
        }
        saw_tag = 0
        invalid = 0
      }
      /^\[[^]]+\]/ {
        saw_tag = 1
        tag = $0
        sub(/^\[/, "", tag)
        sub(/\].*$/, "", tag)
        if (!(tag in allowed)) {
          invalid = 1
          printf("%d:%s\n", NR, $0)
        }
      }
      END {
        if (!saw_tag) {
          exit 2
        }
        if (invalid) {
          exit 1
        }
      }
    ' "$script_path"
  )"; then
    return
  else
    validation_status=$?
  fi

  case "$validation_status" in
    1)
      echo "Canonical episode script contains non-canonical cue tags: $script_path" >&2
      printf '%s\n' "$validation_output" >&2
      echo "Allowed cue tags: $(canonical_cue_tags_display)" >&2
      ;;
    2)
      echo "Canonical episode script does not contain any cue-tagged lines: $script_path" >&2
      echo "Allowed cue tags: $(canonical_cue_tags_display)" >&2
      ;;
    *)
      echo "Failed to validate canonical cue tags: $script_path" >&2
      ;;
  esac
  exit 1
}

require_episode_package_contract() {
  local script_path
  require_episode_dir
  require_cmd awk
  require_supported_response_format

  if [[ "$RESPONSE_FORMAT" != "wav" ]]; then
    echo "Release packaging requires RESPONSE_FORMAT=wav (got $RESPONSE_FORMAT)." >&2
    exit 1
  fi

  script_path="$(canonical_episode_script_path)"
  if [[ ! -f "$script_path" ]]; then
    echo "Canonical episode script not found: $script_path" >&2
    exit 1
  fi
  if [[ ! -s "$script_path" ]]; then
    echo "Canonical episode script is empty: $script_path" >&2
    exit 1
  fi
  if [[ "$REQUIRE_CANONICAL_CUE_TAGS" != "0" ]]; then
    require_canonical_episode_script_cue_tags "$script_path"
  fi
}

package_master_into_episode_final() {
  local packaged_dir
  local packaged_out
  require_cmd cmp
  require_episode_package_contract

  packaged_dir="$(canonical_episode_final_dir)"
  packaged_out="$(canonical_episode_final_out)"

  mkdir -p "$packaged_dir"
  if [[ "$MASTER_OUT" != "$packaged_out" ]]; then
    cp "$MASTER_OUT" "$packaged_out"
  fi

  if [[ ! -f "$packaged_out" ]]; then
    echo "Packaged final audio was not written: $packaged_out" >&2
    exit 1
  fi
  if ! cmp -s "$MASTER_OUT" "$packaged_out"; then
    echo "Packaged final audio does not match staging master: $packaged_out" >&2
    exit 1
  fi

  echo "Packaged final audio to $packaged_out" >&2
  printf '%s\n' "$packaged_out"
}

release_qa_target() {
  local packaged_out
  require_episode_package_contract
  packaged_out="$(canonical_episode_final_out)"
  if [[ ! -f "$packaged_out" ]]; then
    echo "Packaged canonical final not found: $packaged_out" >&2
    exit 1
  fi
  printf '%s\n' "$packaged_out"
}

load_env() {
  source_env_file_if_present
  require_supported_provider
  case "$TTS_PROVIDER" in
    openai)
      if [[ -z "${OPENAI_API_KEY:-}" ]]; then
        echo "OPENAI_API_KEY is not set. Add it to $ENV_FILE or export it in the shell." >&2
        exit 1
      fi
      ;;
    elevenlabs)
      if [[ -z "${ELEVEN_LABS_API_KEY:-}" ]]; then
        echo "ELEVEN_LABS_API_KEY is not set. Add it to $ENV_FILE or export it in the shell." >&2
        exit 1
      fi
      if [[ -z "${ELEVEN_LABS_VOICE_ID:-}" ]]; then
        echo "ELEVEN_LABS_VOICE_ID is not set. Add it to $ENV_FILE or export it in the shell." >&2
        exit 1
      fi
      if [[ "$ELEVENLABS_OUTPUT_FORMAT" != wav_* ]]; then
        echo "ELEVENLABS_OUTPUT_FORMAT must be WAV-based (got $ELEVENLABS_OUTPUT_FORMAT)." >&2
        exit 1
      fi
      ;;
  esac
}

run_tts_cli() {
  uv run --with "$OPENAI_PYTHON_SPEC" python "$TTS_GEN" "$@"
}

run_elevenlabs_helper() {
  ELEVENLABS_PRONUNCIATION_LEXICON="$ELEVENLABS_PRONUNCIATION_LEXICON" \
    ELEVENLABS_PRONUNCIATION_DICTIONARY_LOCATORS="${ELEVENLABS_PRONUNCIATION_DICTIONARY_LOCATORS:-}" \
    python3 "$ELEVENLABS_HELPER" "$@"
}

run_sibilance_helper() {
  python3 "$SIBILANCE_HELPER" "$@"
}

provider_max_input_chars() {
  if [[ "$TTS_PROVIDER" == "elevenlabs" ]]; then
    printf '%s\n' "$ELEVENLABS_MAX_INPUT_CHARS"
  else
    printf '4096\n'
  fi
}

provider_estimated_usd_per_million_chars() {
  if [[ "$TTS_PROVIDER" == "elevenlabs" ]]; then
    printf '%s\n' "$ELEVENLABS_ESTIMATED_USD_PER_MILLION_CHARS"
  else
    printf '%s\n' "$ESTIMATED_USD_PER_MILLION_CHARS"
  fi
}

provider_model() {
  if [[ -n "$MODEL" ]]; then
    printf '%s\n' "$MODEL"
    return
  fi
  if [[ "$TTS_PROVIDER" == "elevenlabs" ]]; then
    source_env_file_if_present
    if [[ -z "${ELEVENLABS_DEFAULT_MODEL:-}" ]]; then
      echo "ELEVENLABS_DEFAULT_MODEL is not set. Add it to $ENV_FILE, export it in the shell, or pass MODEL for this run." >&2
      exit 1
    fi
    printf '%s\n' "$ELEVENLABS_DEFAULT_MODEL"
  else
    printf '%s\n' "$OPENAI_DEFAULT_MODEL"
  fi
}

validate_manifest() {
  local manifest="$1"
  local char_limit
  require_supported_response_format
  require_supported_provider
  char_limit="$(provider_max_input_chars)"
  python3 - "$manifest" "$RESPONSE_FORMAT" "$char_limit" "$TTS_PROVIDER" <<'PY'
import json
import re
import sys
from pathlib import Path

manifest = Path(sys.argv[1])
expected_format = sys.argv[2]
char_limit = int(sys.argv[3])
provider = sys.argv[4]
if not manifest.exists():
    raise SystemExit(f"Missing manifest: {manifest}")

errors = []
count = 0
for line_no, raw in enumerate(manifest.read_text().splitlines(), start=1):
    raw = raw.strip()
    if not raw:
        continue
    count += 1
    try:
        job = json.loads(raw)
    except json.JSONDecodeError as exc:
        errors.append(f"{manifest}:{line_no}: invalid JSON ({exc})")
        continue

    text = job.get("input")
    out = job.get("out")
    if not isinstance(text, str) or not text.strip():
        errors.append(f"{manifest}:{line_no}: missing non-empty input")
        text = ""
    elif len(text) > char_limit:
        errors.append(
            f"{manifest}:{line_no}: input exceeds {char_limit} chars ({len(text)})"
        )

    if not isinstance(out, str) or not out.strip():
        errors.append(f"{manifest}:{line_no}: missing out filename")
    else:
        out_path = Path(out.strip())
        if out_path.suffix.lower() != f".{expected_format}":
            errors.append(
                f"{manifest}:{line_no}: out filename extension {out_path.suffix or '<none>'} "
                f"does not match RESPONSE_FORMAT={expected_format}"
            )

    seen_format_fields = []
    for key in ("response_format", "format"):
        if key in job:
            seen_format_fields.append((key, job.get(key)))

    normalized_formats = []
    for key, raw_value in seen_format_fields:
        if not isinstance(raw_value, str) or not raw_value.strip():
            errors.append(f"{manifest}:{line_no}: {key} must be a non-empty string when present")
            continue
        normalized_formats.append((key, raw_value.strip().lower()))

    if len({value for _, value in normalized_formats}) > 1:
        pairs = ", ".join(f"{key}={value}" for key, value in normalized_formats)
        errors.append(f"{manifest}:{line_no}: conflicting per-job formats ({pairs})")

    for key, value in normalized_formats:
        if value != expected_format:
            errors.append(
                f"{manifest}:{line_no}: {key}={value} does not match RESPONSE_FORMAT={expected_format}"
            )

    warmup_prefix = job.get("warmup_prefix")
    if warmup_prefix is not None:
        if not isinstance(warmup_prefix, str) or not warmup_prefix.strip():
            errors.append(f"{manifest}:{line_no}: warmup_prefix must be a non-empty string")
        elif text:
            effective_len = len(f"{warmup_prefix.strip()}\n\n{text}")
            if effective_len > char_limit:
                errors.append(
                    f"{manifest}:{line_no}: warmup-prefixed input exceeds {char_limit} chars ({effective_len})"
                )

    warmup_preroll_ms = job.get("warmup_preroll_ms")
    if warmup_preroll_ms is not None:
        if not isinstance(warmup_preroll_ms, int) or warmup_preroll_ms < 0:
            errors.append(f"{manifest}:{line_no}: warmup_preroll_ms must be a non-negative integer")

    warmup_anchor_text = job.get("warmup_anchor_text")
    if warmup_anchor_text is not None:
        if not isinstance(warmup_anchor_text, str) or not warmup_anchor_text.strip():
            errors.append(f"{manifest}:{line_no}: warmup_anchor_text must be a non-empty string")
        elif text:
            normalize = lambda value: re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
            anchor_norm = normalize(warmup_anchor_text)
            text_norm = normalize(text)
            if anchor_norm and anchor_norm not in text_norm:
                errors.append(
                    f"{manifest}:{line_no}: warmup_anchor_text must come from the visible input text"
                )

    if provider == "elevenlabs":
        compiled_text = job.get("elevenlabs_text")
        if compiled_text is not None:
            if not isinstance(compiled_text, str) or not compiled_text.strip():
                errors.append(f"{manifest}:{line_no}: elevenlabs_text must be a non-empty string when present")
            elif len(compiled_text) > char_limit:
                errors.append(
                    f"{manifest}:{line_no}: elevenlabs_text exceeds {char_limit} chars ({len(compiled_text)})"
                )
        spoken_input = job.get("spoken_input")
        if spoken_input is not None and (not isinstance(spoken_input, str) or not spoken_input.strip()):
            errors.append(f"{manifest}:{line_no}: spoken_input must be a non-empty string when present")

if errors:
    for err in errors:
        print(err, file=sys.stderr)
    raise SystemExit(1)

print(f"Validated {count} jobs in {manifest}")
PY
}

estimate_cost() {
  local rate="$1"
  local text_key="$2"
  shift 2
  python3 - "$rate" "$text_key" "$@" <<'PY'
import json
import sys
from pathlib import Path

rate = float(sys.argv[1])
text_key = sys.argv[2]
manifests = [Path(p) for p in sys.argv[3:]]
grand_total = 0

for manifest in manifests:
    chars = 0
    jobs = 0
    for raw in manifest.read_text().splitlines():
        raw = raw.strip()
        if not raw:
            continue
        job = json.loads(raw)
        text = job.get(text_key) or job.get("input") or ""
        chars += len(text)
        jobs += 1
    usd = chars / 1_000_000 * rate
    grand_total += chars
    print(f"{manifest.name}: jobs={jobs} chars={chars} est_usd=${usd:.4f}")

grand_usd = grand_total / 1_000_000 * rate
print(f"total: chars={grand_total} est_usd=${grand_usd:.4f}")
print("note: this is a planning estimate calibrated to the current Cascade Effects workflow, not invoice-accurate billing")
PY
}

manifest_has_jobs() {
  local manifest="$1"
  python3 - "$manifest" <<'PY'
import sys
from pathlib import Path

manifest = Path(sys.argv[1])
if not manifest.exists():
    raise SystemExit(1)

for raw in manifest.read_text().splitlines():
    line = raw.strip()
    if line and not line.startswith("#"):
        raise SystemExit(0)

raise SystemExit(1)
PY
}

manifest_has_warmup_jobs() {
  local manifest="$1"
  python3 - "$manifest" <<'PY'
import json
import sys
from pathlib import Path

manifest = Path(sys.argv[1])
if not manifest.exists():
    raise SystemExit(1)

for raw in manifest.read_text().splitlines():
    line = raw.strip()
    if not line or line.startswith("#"):
        continue
    job = json.loads(line)
    prefix = job.get("warmup_prefix")
    if isinstance(prefix, str) and prefix.strip():
        raise SystemExit(0)

raise SystemExit(1)
PY
}

estimate_default_cost() {
  local rate
  local text_key="input"
  local effective_final="$FINAL_JOBS"
  local effective_audition="$AUDITION_JOBS"
  rate="$(provider_estimated_usd_per_million_chars)"

  if [[ "$TTS_PROVIDER" == "elevenlabs" ]]; then
    text_key="elevenlabs_text"
    effective_final="$(prepare_jobs_manifest_for_tts "$FINAL_JOBS" "$PIPELINE_DIR/effective_cost_final_jobs.elevenlabs.jsonl" "cost-final")"
  fi

  estimate_cost "$rate" "$text_key" "$effective_final"

  if manifest_has_jobs "$AUDITION_JOBS"; then
    if [[ "$TTS_PROVIDER" == "elevenlabs" ]]; then
      effective_audition="$(prepare_jobs_manifest_for_tts "$AUDITION_JOBS" "$PIPELINE_DIR/effective_cost_audition_jobs.elevenlabs.jsonl" "cost-audition")"
    fi
    echo "optional audition estimate:"
    estimate_cost "$rate" "$text_key" "$effective_audition"
  fi
}

prepare_jobs_manifest_for_tts() {
  local manifest="$1"
  local effective_manifest="$2"
  local phase="${3:-render}"
  local compiled_manifest="$effective_manifest"
  local warmed_manifest="$effective_manifest"
  local script_path
  local provider_model_id

  source_env_file_if_present
  require_supported_provider
  provider_model_id="$(provider_model)"

  if [[ "$TTS_PROVIDER" == "elevenlabs" ]]; then
    if [[ "$phase" == "render" || "$phase" == "guard" || "$phase" == "cost-final" ]]; then
      require_episode_dir
      if [[ "$ELEVENLABS_STRICT_SOURCE_ALIGNMENT" == "0" ]]; then
        run_elevenlabs_helper compile-manifest \
          --input "$manifest" \
          --output "$compiled_manifest" \
          --model "$provider_model_id" \
          --continuity-chars "$ELEVENLABS_CONTINUITY_CHARS" >&2
      else
        script_path="$(canonical_episode_script_path)"
        run_elevenlabs_helper compile-manifest \
          --input "$manifest" \
          --output "$compiled_manifest" \
          --script-path "$script_path" \
          --strict-source-alignment \
          --model "$provider_model_id" \
          --continuity-chars "$ELEVENLABS_CONTINUITY_CHARS" >&2
      fi
    else
      run_elevenlabs_helper compile-manifest \
        --input "$manifest" \
        --output "$compiled_manifest" \
        --model "$provider_model_id" \
        --continuity-chars "$ELEVENLABS_CONTINUITY_CHARS" >&2
    fi
    run_pronunciation_preflight_verify_compiled "$compiled_manifest"

    if manifest_has_warmup_jobs "$manifest"; then
      warmed_manifest="${effective_manifest%.jsonl}.warmup.jsonl"
      python3 "$WARMUP_HELPER" prepare-manifest \
        --manifest "$compiled_manifest" \
        --output "$warmed_manifest" >&2
      printf '%s\n' "$warmed_manifest"
    else
      printf '%s\n' "$compiled_manifest"
    fi
    return
  fi

  if manifest_has_warmup_jobs "$manifest"; then
    python3 "$WARMUP_HELPER" prepare-manifest \
      --manifest "$manifest" \
      --output "$effective_manifest" >&2
    printf '%s\n' "$effective_manifest"
  else
    printf '%s\n' "$manifest"
  fi
}

run_provider_batch() {
  local manifest="$1"
  local out_dir="$2"
  local provider_model_id
  provider_model_id="$(provider_model)"

  case "$TTS_PROVIDER" in
    openai)
      run_tts_cli speak-batch \
        --input "$manifest" \
        --out-dir "$out_dir" \
        --model "$provider_model_id" \
        --voice "$VOICE" \
        --response-format "$RESPONSE_FORMAT" \
        --force
      ;;
    elevenlabs)
      run_elevenlabs_helper render-batch \
        --input "$manifest" \
        --out-dir "$out_dir" \
        --model "$provider_model_id" \
        --output-format "$ELEVENLABS_OUTPUT_FORMAT" \
        --force
      ;;
  esac
}

trim_warmup_outputs() {
  local manifest="$1"
  local render_dir="$2"
  local phase="$3"

  if ! manifest_has_warmup_jobs "$manifest"; then
    return
  fi

  require_cmd transcribe
  mkdir -p "$WARMUP_TRIM_DIR/$phase"
  python3 "$WARMUP_HELPER" trim-rendered \
    --manifest "$manifest" \
    --render-dir "$render_dir" \
    --work-dir "$WARMUP_TRIM_DIR/$phase" \
    --transcribe-model "$WARMUP_TRANSCRIBE_MODEL"
}

run_audition() {
  local effective_manifest
  validate_manifest "$AUDITION_JOBS"
  load_env
  require_supported_response_format
  mkdir -p "$AUDITION_OUT_DIR"
  effective_manifest="$(prepare_jobs_manifest_for_tts "$AUDITION_JOBS" "$PIPELINE_DIR/effective_audition_jobs${TTS_PROVIDER:+.$TTS_PROVIDER}.jsonl" "audition")"
  validate_manifest "$effective_manifest"
  run_provider_batch "$effective_manifest" "$AUDITION_OUT_DIR"
  trim_warmup_outputs "$AUDITION_JOBS" "$AUDITION_OUT_DIR" "audition"
}

run_render() {
  local effective_manifest
  validate_manifest "$FINAL_JOBS"
  load_env
  require_supported_response_format
  mkdir -p "$RENDER_OUT_DIR"
  effective_manifest="$(prepare_jobs_manifest_for_tts "$FINAL_JOBS" "$PIPELINE_DIR/effective_final_jobs${TTS_PROVIDER:+.$TTS_PROVIDER}.jsonl" "render")"
  validate_manifest "$effective_manifest"
  run_provider_batch "$effective_manifest" "$RENDER_OUT_DIR"
  trim_warmup_outputs "$FINAL_JOBS" "$RENDER_OUT_DIR" "render"
}

get_effective_jobs_manifest() {
  local effective_jobs
  effective_jobs="$PROSODY_GUARD_DIR/effective_jobs.jsonl"
  if [[ -f "$effective_jobs" ]]; then
    printf '%s\n' "$effective_jobs"
  else
    printf '%s\n' "$FINAL_JOBS"
  fi
}

resolve_sibilance_master() {
  local candidate
  if [[ -n "$SIBILANCE_MASTER" ]]; then
    candidate="$SIBILANCE_MASTER"
  elif [[ -n "$EPISODE_DIR" ]]; then
    candidate="$(release_qa_target)"
    if [[ ! -f "$candidate" && -f "$MASTER_OUT" ]]; then
      candidate="$MASTER_OUT"
    fi
  elif [[ -f "$MASTER_OUT" ]]; then
    candidate="$MASTER_OUT"
  else
    echo "No packaged or staged master available for sibilance analysis." >&2
    exit 1
  fi

  if [[ ! -f "$candidate" ]]; then
    echo "SIBILANCE_MASTER does not exist: $candidate" >&2
    exit 1
  fi
  printf '%s\n' "$candidate"
}

append_sibilance_seed_args() {
  local token
  local seeds="${SIBILANCE_SEED_TIMES//$'\n'/,}"
  if [[ -z "$seeds" ]]; then
    return
  fi
  IFS=',' read -r -a _seed_tokens <<<"$seeds"
  for token in "${_seed_tokens[@]}"; do
    token="${token#"${token%%[![:space:]]*}"}"
    token="${token%"${token##*[![:space:]]}"}"
    if [[ -n "$token" ]]; then
      printf '%s\0%s\0' "--seed-time" "$token"
    fi
  done
}

run_sibilance_analyze() {
  local master_target
  local effective_jobs
  require_cmd ffmpeg
  require_cmd ffprobe
  master_target="$(resolve_sibilance_master)"
  effective_jobs="$(get_effective_jobs_manifest)"
  validate_manifest "$effective_jobs"
  mkdir -p "$(dirname "$SIBILANCE_REPORT")"
  run_sibilance_helper analyze \
    --master "$master_target" \
    --jobs-manifest "$effective_jobs" \
    --render-dir "$RENDER_OUT_DIR" \
    --output "$SIBILANCE_REPORT" \
    --top-n "$SIBILANCE_TOP_N"
}

run_sibilance_audition() {
  local effective_jobs
  local -a seed_args=()
  local -a helper_args=()
  require_supported_provider
  if [[ "$TTS_PROVIDER" != "openai" ]]; then
    echo "sibilance-audition is OpenAI-only in v1. Set TTS_PROVIDER=openai for cedar/marin comparisons." >&2
    exit 1
  fi
  validate_manifest "$FINAL_JOBS"
  effective_jobs="$(get_effective_jobs_manifest)"
  validate_manifest "$effective_jobs"
  if [[ ! -f "$SIBILANCE_REPORT" ]]; then
    run_sibilance_analyze
  fi
  if [[ -n "$SIBILANCE_SEED_TIMES" ]]; then
    while IFS= read -r -d '' token; do
      seed_args+=("$token")
    done < <(append_sibilance_seed_args)
  fi
  mkdir -p "$(dirname "$SIBILANCE_AUDITION_JOBS")"
  mkdir -p "$SIBILANCE_AUDITION_OUT_DIR"
  if [[ "$SIBILANCE_AUDITION_STAGE" == "second-pass" && -z "$SIBILANCE_WINNER_VOICE" ]]; then
    echo "SIBILANCE_WINNER_VOICE is required for SIBILANCE_AUDITION_STAGE=second-pass" >&2
    exit 1
  fi
  helper_args=(
    build-auditions
    --jobs-manifest "$effective_jobs"
    --render-dir "$RENDER_OUT_DIR"
    --report "$SIBILANCE_REPORT"
    --output "$SIBILANCE_AUDITION_JOBS"
    --stage "$SIBILANCE_AUDITION_STAGE"
    --response-format "$RESPONSE_FORMAT"
    --top-n "$SIBILANCE_TOP_N"
    --seed-tolerance "$SIBILANCE_SEED_TOLERANCE"
  )
  if [[ -n "$SIBILANCE_WINNER_VOICE" ]]; then
    helper_args+=(--winner-voice "$SIBILANCE_WINNER_VOICE")
  fi
  helper_args+=("${seed_args[@]}")
  run_sibilance_helper "${helper_args[@]}"
  validate_manifest "$SIBILANCE_AUDITION_JOBS"
  load_env
  run_tts_cli speak-batch \
    --input "$SIBILANCE_AUDITION_JOBS" \
    --out-dir "$SIBILANCE_AUDITION_OUT_DIR" \
    --model "$(provider_model)" \
    --voice "$VOICE" \
    --response-format "$RESPONSE_FORMAT" \
    --force
}

run_guard() {
  local effective_manifest
  local provider_model_id
  require_cmd transcribe
  load_env
  require_supported_response_format
  mkdir -p "$PROSODY_GUARD_DIR"
  provider_model_id="$(provider_model)"
  effective_manifest="$(prepare_jobs_manifest_for_tts "$FINAL_JOBS" "$PIPELINE_DIR/effective_guard_jobs${TTS_PROVIDER:+.$TTS_PROVIDER}.jsonl" "guard")"
  validate_manifest "$effective_manifest"
  python3 "$ROOT_DIR/scripts/prosody_guard.py" \
    --final-jobs "$effective_manifest" \
    --render-dir "$RENDER_OUT_DIR" \
    --guard-dir "$PROSODY_GUARD_DIR" \
    --provider "$TTS_PROVIDER" \
    --model "$provider_model_id" \
    --voice "$VOICE" \
    --response-format "$RESPONSE_FORMAT" \
    --tts-gen "$TTS_GEN" \
    --openai-python-spec "$OPENAI_PYTHON_SPEC" \
    --elevenlabs-helper "$ELEVENLABS_HELPER" \
    --elevenlabs-output-format "$ELEVENLABS_OUTPUT_FORMAT"
}

run_merge() {
  local codec_args=()
  local -a audio_files=()
  local -a input_args=()
  local filter_complex=""
  local merge_jobs
  local effective_jobs
  local merge_target
  local premaster_target
  local backup_path
  local backup_dir
  local mastering_scan_json
  local mastering_second_pass_json
  local mastering_filter
  local mastering_log
  local measured_i
  local measured_tp
  local measured_lra
  local measured_thresh
  local target_offset
  local premaster_sample_rate
  local premaster_channels
  local packaged_out
  local idx=0
  require_episode_package_contract
  merge_jobs="$(get_effective_jobs_manifest)"
  effective_jobs="$PROSODY_GUARD_DIR/effective_jobs.jsonl"
  mkdir -p "$(dirname "$MASTER_OUT")"
  mkdir -p "$(dirname "$PREMASTER_OUT")"
  mkdir -p "$MASTERING_DIR"
  require_supported_response_format
  require_master_out_matches_format
  require_premaster_out_matches_format
  require_distinct_premaster_if_mastering
  validate_manifest "$merge_jobs"

  while IFS= read -r audio; do
    audio_files+=("$audio")
  done < <(python3 - "$merge_jobs" "$RENDER_OUT_DIR" <<'PY'
import json
import sys
from pathlib import Path

manifest = Path(sys.argv[1])
render_dir = Path(sys.argv[2])
for raw in manifest.read_text().splitlines():
    raw = raw.strip()
    if not raw:
        continue
    job = json.loads(raw)
    audio = render_dir / job["out"]
    if not audio.exists():
        raise SystemExit(f"Missing rendered chunk: {audio}")
    print(audio)
PY
  )

  if [[ "${#audio_files[@]}" -eq 0 ]]; then
    echo "No rendered chunks found to merge." >&2
    exit 1
  fi

  for audio in "${audio_files[@]}"; do
    input_args+=(-i "$audio")
    filter_complex+="[$idx:a]"
    idx=$((idx + 1))
  done
  filter_complex+="concat=n=${#audio_files[@]}:v=0:a=1[outa]"

  case "$RESPONSE_FORMAT" in
    wav)
      codec_args=(-c:a pcm_s16le)
      ;;
    flac)
      codec_args=(-c:a flac)
      ;;
    *)
      echo "Unsupported RESPONSE_FORMAT during merge: $RESPONSE_FORMAT" >&2
      exit 1
      ;;
  esac

  premaster_target="$PREMASTER_OUT"
  merge_target="$MASTER_OUT"
  if [[ "$merge_jobs" == "$effective_jobs" ]]; then
    mkdir -p "$PROSODY_GUARD_DIR/backups"
    if [[ -f "$MASTER_OUT" ]]; then
      backup_dir="$PROSODY_GUARD_DIR/backups"
      backup_path="$backup_dir/$(basename "${MASTER_OUT%.*}").$(date +%Y%m%d-%H%M%S).bak.${MASTER_OUT##*.}"
      mv "$MASTER_OUT" "$backup_path"
      echo "Backed up previous master to $backup_path"
    fi
    merge_target="$PROSODY_GUARD_DIR/merge_candidate.${RESPONSE_FORMAT}"
  fi

  ffmpeg -y "${input_args[@]}" -filter_complex "$filter_complex" -map "[outa]" "${codec_args[@]}" "$premaster_target"
  read -r premaster_sample_rate premaster_channels < <(
    ffprobe -v error -select_streams a:0 -show_entries stream=sample_rate,channels -of default=noprint_wrappers=1:nokey=1 "$premaster_target"
  )

  if [[ "$MASTERING_ENABLED" == "1" ]]; then
    mastering_scan_json="$MASTERING_DIR/loudnorm_scan.json"
    mastering_second_pass_json="$MASTERING_DIR/loudnorm_second_pass.json"
    mastering_log="$MASTERING_DIR/loudnorm_scan.log"
    ffmpeg -hide_banner -y -i "$premaster_target" \
      -af "loudnorm=I=$LOUDNESS_TARGET_I:TP=$LOUDNESS_TARGET_TP:LRA=$LOUDNESS_TARGET_LRA:print_format=json" \
      -f null - >"$mastering_log" 2>&1

    python3 - "$mastering_log" "$mastering_scan_json" <<'PY'
import json
import re
import sys
from pathlib import Path

log_path = Path(sys.argv[1])
json_path = Path(sys.argv[2])
text = log_path.read_text()
match = re.search(r"\{\s*\"input_i\"[\s\S]*?\}", text)
if not match:
    raise SystemExit(f"Could not find loudnorm JSON block in {log_path}")
data = json.loads(match.group(0))
json_path.write_text(json.dumps(data, indent=2) + "\n")
PY

    while IFS='=' read -r key value; do
      case "$key" in
        input_i) measured_i="$value" ;;
        input_tp) measured_tp="$value" ;;
        input_lra) measured_lra="$value" ;;
        input_thresh) measured_thresh="$value" ;;
        target_offset) target_offset="$value" ;;
      esac
    done < <(python3 - "$mastering_scan_json" <<'PY'
import json
import sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text())
for key in ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset"):
    print(f"{key}={data[key]}")
PY
    )

    python3 - "$mastering_second_pass_json" "$LOUDNESS_TARGET_I" "$LOUDNESS_TARGET_TP" "$LOUDNESS_TARGET_LRA" "$measured_i" "$measured_tp" "$measured_lra" "$measured_thresh" "$target_offset" <<'PY'
import json
import sys
from pathlib import Path

payload = {
    "target_i": sys.argv[2],
    "target_tp": sys.argv[3],
    "target_lra": sys.argv[4],
    "measured_i": sys.argv[5],
    "measured_tp": sys.argv[6],
    "measured_lra": sys.argv[7],
    "measured_thresh": sys.argv[8],
    "target_offset": sys.argv[9],
}
Path(sys.argv[1]).write_text(json.dumps(payload, indent=2) + "\n")
PY

    mastering_filter="loudnorm=I=$LOUDNESS_TARGET_I:TP=$LOUDNESS_TARGET_TP:LRA=$LOUDNESS_TARGET_LRA:measured_I=$measured_i:measured_TP=$measured_tp:measured_LRA=$measured_lra:measured_thresh=$measured_thresh:offset=$target_offset:linear=true:print_format=summary"
    ffmpeg -y -i "$premaster_target" -af "$mastering_filter" -ar "$premaster_sample_rate" -ac "$premaster_channels" "${codec_args[@]}" "$merge_target"
  else
    if [[ "$merge_target" != "$premaster_target" ]]; then
      cp "$premaster_target" "$merge_target"
    fi
  fi

  if [[ "$merge_jobs" == "$effective_jobs" ]]; then
    mv "$merge_target" "$MASTER_OUT"
  fi
  ffprobe -v error -show_entries format=duration,size -of default=noprint_wrappers=1:nokey=0 "$PREMASTER_OUT"
  ffprobe -v error -show_entries format=duration,size -of default=noprint_wrappers=1:nokey=0 "$MASTER_OUT"
  packaged_out="$(package_master_into_episode_final)"
  write_audio_package_sidecar "$packaged_out"
  ffprobe -v error -show_entries format=duration,size -of default=noprint_wrappers=1:nokey=0 "$packaged_out"
}

run_qa() {
  local qa_target
  local qa_started_at
  local transcript_path
  require_cmd transcribe
  mkdir -p "$TRANSCRIPT_OUT_DIR"
  qa_target="$(release_qa_target)"
  qa_started_at="$(date +%s)"
  transcribe -m small -o "$TRANSCRIPT_OUT_DIR" "$qa_target"
  transcript_path="$(find_generated_transcript_path "$TRANSCRIPT_OUT_DIR" "$qa_target" "$qa_started_at")"
  append_audio_package_qa_sidecar "$transcript_path"
}

main() {
  require_cmd python3
  require_cmd uv
  require_cmd ffmpeg
  require_cmd ffprobe

  case "${1:-help}" in
    validate)
      validate_manifest "$FINAL_JOBS"
      run_pronunciation_preflight_scan "$FINAL_JOBS"
      ;;
    cost)
      estimate_default_cost
      ;;
    audition)
      run_audition
      ;;
    render)
      run_render
      ;;
    guard)
      run_guard
      ;;
    merge)
      run_merge
      ;;
    qa)
      run_qa
      ;;
    sibilance-analyze)
      run_sibilance_analyze
      ;;
    sibilance-audition)
      run_sibilance_audition
      ;;
    all)
      require_episode_package_contract
      validate_manifest "$FINAL_JOBS"
      estimate_default_cost
      run_render
      run_guard
      run_merge
      run_qa
      ;;
    help|-h|--help)
      usage
      ;;
    *)
      echo "Unknown command: $1" >&2
      usage
      exit 1
      ;;
  esac
}

main "$@"
