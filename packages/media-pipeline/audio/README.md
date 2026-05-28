# Cascade Effects TTS Pipeline

This workspace contains the current production-ready text-to-speech pipeline for Cascade Effects YouTube narration.

Active reusable workflow skill:

- [/Users/mike/Audio_CascadeEffects/references/skills/youtube_shorts_audio_elevenlabs_v1/SKILL.md](/Users/mike/Audio_CascadeEffects/references/skills/youtube_shorts_audio_elevenlabs_v1/SKILL.md)

That skill is the audio-side dependency of the current active production workflow in:

- [/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_production_v1/SKILL.md](/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_production_v1/SKILL.md)

Long-form audio podcast remains future work and is not part of the active routing in this README.

The working flow is:

1. Lock the narration script.
2. Create semantic full-episode chunk manifests with per-chunk instructions and speed.
3. Render the full episode in chunks.
4. Run pre-merge repair/guard checks when needed.
5. Merge chunk audio into one raw premaster and one publish master.
6. Run local transcription QA before publish.

Opening auditions are now an explicit exception path for new voices, major style experiments, or user-requested comparisons. They are no longer part of the default `all` workflow.

This pipeline is optimized for fast iteration, repeatability, and a lossless production path. It supports two render providers inside the same production wrapper:

- ElevenLabs custom voices with a configured voice ID, configured default model, and provider-specific effective manifests
- OpenAI built-in voices plus instruction steering as an explicit fallback path

Generated audio and temp manifests live in ignored local output paths during production and are not part of the tracked repository.

## Technologies

- OpenAI `gpt-4o-mini-tts-2025-12-15` and a configured ElevenLabs default model for speech generation.
- Built-in OpenAI voices such as `cedar`, `onyx`, and `sage`.
- Bundled OpenAI speech CLI: `$CODEX_HOME/skills/speech/scripts/text_to_speech.py`
- Local ElevenLabs batch helper: `scripts/elevenlabs_provider.py`
- Local ElevenLabs PVC helper: `scripts/elevenlabs_pvc.py`
- `uv` to run the OpenAI CLI with the OpenAI Python SDK dependency.
- `.env.local` for `OPENAI_API_KEY`, `ELEVEN_LABS_API_KEY`, `ELEVEN_LABS_VOICE_ID`, and `ELEVENLABS_DEFAULT_MODEL`.
- `ffmpeg` and `ffprobe` for merge and duration checks.
- Local `transcribe` for WhisperX-based QA on the finished audio.

Official references used for this pipeline:

- [OpenAI pricing](https://developers.openai.com/api/docs/pricing)
- [GPT-4o mini TTS model](https://developers.openai.com/api/docs/models/gpt-4o-mini-tts)
- [ElevenLabs PVC sample upload API](https://elevenlabs.io/docs/api-reference/voices/pvc/samples/create)
- [ElevenLabs PVC sample update API](https://elevenlabs.io/docs/api-reference/voices/pvc/samples/update)
- [ElevenLabs PVC training API](https://elevenlabs.io/docs/api-reference/voices/pvc/train)

## Operating Cost

The numbers below are the current house estimates used for production planning in this workspace. They are based on the approved EP3 run and are meant for planning, not invoice reconciliation.

- Full EP3 master render: about `$0.18`
- Optional opening audition round: about `$0.05`
- One comparison iteration, meaning auditions plus one full master: about `$0.24`
- Each additional full rerender of similar length: about `$0.18`

The current helper script uses an estimate of `$15.00` per 1M input characters so the planning math matches the approved EP3 cost model.
For the active manifests in this workspace, run `./scripts/cascade_tts_pipeline.sh cost`. That command now estimates the standard full render from `final_jobs.jsonl` and reports auditions as optional extra cost if an `audition_jobs.jsonl` file is present.

## Rapid Kickoff

Use the checked-in orchestration script:

```bash
EPISODE_DIR=/Users/mike/Episodes_CascadeEffects/Ep4_New-Episode \
./scripts/cascade_tts_pipeline.sh all
```

If your ElevenLabs credentials or default model live in another checkout, point the wrapper at that file with `ENV_FILE=/absolute/path/to/.env.local`.

That command runs:

1. Manifest validation
2. Cost estimate
3. Full chunked render
4. Pre-merge prosody guard and auto-repair
5. Build premaster, then loudness-master the publish output
6. Local transcription QA

### Current Defaults

The script defaults to the current working EP3 layout:

- `PIPELINE_DIR=/Users/mike/Audio_CascadeEffects/tmp/speech_emotive`
- `AUDITION_JOBS=/Users/mike/Audio_CascadeEffects/tmp/speech_emotive/audition_jobs.jsonl`
- `FINAL_JOBS=/Users/mike/Audio_CascadeEffects/tmp/speech_emotive/final_jobs.jsonl`
- `AUDITION_OUT_DIR=/Users/mike/Audio_CascadeEffects/output/speech/auditions`
- `RENDER_OUT_DIR=/Users/mike/Audio_CascadeEffects/tmp/speech_emotive/rendered`
- `PROSODY_GUARD_DIR=/Users/mike/Audio_CascadeEffects/tmp/speech_emotive/prosody_guard`
- `MASTER_OUT=/Users/mike/Audio_CascadeEffects/output/speech/ep3_narration_emotive_v2.wav`
- `PREMASTER_OUT=/Users/mike/Audio_CascadeEffects/tmp/speech_emotive/premaster.wav`
- `MASTERING_DIR=/Users/mike/Audio_CascadeEffects/tmp/speech_emotive/mastering`
- `TRANSCRIPT_OUT_DIR=/Users/mike/Audio_CascadeEffects/tmp/transcripts_final`
- `VOICE=cedar`
- `TTS_PROVIDER=elevenlabs`
- `MODEL` defaults to `gpt-4o-mini-tts-2025-12-15` for OpenAI and to the configured `ELEVENLABS_DEFAULT_MODEL` for ElevenLabs
- `RESPONSE_FORMAT=wav`
- `ELEVENLABS_OUTPUT_FORMAT=wav_44100`
- `MASTERING_ENABLED=1`
- `LOUDNESS_TARGET_I=-14`
- `LOUDNESS_TARGET_TP=-1.0`
- `LOUDNESS_TARGET_LRA=11`
- `EPISODE_DIR` is unset by default and required for `merge`, `qa`, and `all`
- `EPISODE_SCRIPT=<EPISODE_DIR>/<basename(EPISODE_DIR)>.txt` unless explicitly overridden

### Useful Commands

Validate manifests without making API calls:

```bash
./scripts/cascade_tts_pipeline.sh validate
```

Estimate cost before running:

```bash
./scripts/cascade_tts_pipeline.sh cost
```

Run only the audition phase when you explicitly want an opening comparison or a one-off spot check:

```bash
./scripts/cascade_tts_pipeline.sh audition
```

Run only the full render phase:

```bash
./scripts/cascade_tts_pipeline.sh render
```

Run the pre-merge guard against existing rendered chunks:

```bash
./scripts/cascade_tts_pipeline.sh guard
```

Merge existing rendered chunks:

```bash
EPISODE_DIR=/Users/mike/Episodes_CascadeEffects/Ep4_New-Episode \
./scripts/cascade_tts_pipeline.sh merge
```

By default, `merge` now writes a raw `PREMASTER_OUT`, scans it with `ffmpeg loudnorm`, stores the scan plus second-pass settings under `MASTERING_DIR`, writes the loudness-mastered staging file to `MASTER_OUT`, and then packages the canonical release file under `<EPISODE_DIR>/final/`. Here, raw means pre-mastered, not uncompressed PCM by definition. Under the house default, both files are WAV. Set `MASTERING_ENABLED=0` if you need the older concat-only behavior.

`merge` also writes `<PIPELINE_DIR>/audio_package.json` with the packaged WAV path, provider, voice, model, and the provider-specific source manifest that produced the reviewable package. Compile-only costing manifests are not reviewable packages and do not create this sidecar.

Run QA on the current master:

```bash
EPISODE_DIR=/Users/mike/Episodes_CascadeEffects/Ep4_New-Episode \
./scripts/cascade_tts_pipeline.sh qa
```

When `EPISODE_DIR` is set, `qa` transcribes the packaged canonical file in the episode `final/` directory rather than the staging `MASTER_OUT`.

After `qa`, the same `audio_package.json` sidecar is updated with the QA transcript path, transcript checksum, and `qa_completed_at`. Downstream review should only use a package after both `merge` and `qa` have populated this sidecar, and the orchestration repo has run `ce-orchestrate promote-audio <episode_id>` to sync the manifest-backed review asset.

Analyze a packaged master for likely sibilance hotspots:

```bash
EPISODE_DIR=/Users/mike/Episodes_CascadeEffects/Ep1_Challenger \
PIPELINE_DIR=/Users/mike/Audio_CascadeEffects/tmp/ep1_challenger_production \
./scripts/cascade_tts_pipeline.sh sibilance-analyze
```

Build and render hotspot comparison clips:

```bash
EPISODE_DIR=/Users/mike/Episodes_CascadeEffects/Ep1_Challenger \
PIPELINE_DIR=/Users/mike/Audio_CascadeEffects/tmp/ep1_challenger_production \
SIBILANCE_SEED_TIMES="00:31.147,00:34.773,02:26.773,03:32.779,06:46.059,08:59.861,10:09.323,11:01.888,12:45.995" \
./scripts/cascade_tts_pipeline.sh sibilance-audition
```

### ElevenLabs Provider

The shell wrapper defaults to `TTS_PROVIDER=elevenlabs` for the normal `render` and `all` workflow, while still supporting `TTS_PROVIDER=openai|elevenlabs` for explicit overrides.

For ElevenLabs, set:

- `ELEVEN_LABS_API_KEY`
- `ELEVEN_LABS_VOICE_ID`
- `ELEVENLABS_DEFAULT_MODEL=<confirmed-elevenlabs-model-id>` unless you are passing `MODEL=...` for that run
- `ELEVENLABS_OUTPUT_FORMAT=wav_44100` or another WAV-based ElevenLabs format

The ElevenLabs path keeps the base JSONL manifest contract unchanged. Before render or guard, the pipeline generates provider-specific effective manifests under `PIPELINE_DIR` that add:

- compiled `elevenlabs_text`
- normalized `spoken_input`
- continuity windows via `previous_text` and `next_text`
- deterministic `seed`
- default voice settings for the current PVC path
- pronunciation preflight provenance, including the lexicon path/hash and applied local alias rules

Continuity payloads are model-capability aware: `eleven_v3`-style runs omit `previous_text` and `next_text`, while non-v3 models can include them when continuity is enabled.

Example:

```bash
ENV_FILE=/absolute/path/to/.env.local \
PIPELINE_DIR=/Users/mike/Audio_CascadeEffects/tmp/ep1_challenger_production \
EPISODE_DIR=/Users/mike/Episodes_CascadeEffects/Ep1_Challenger \
./scripts/cascade_tts_pipeline.sh render
```

### Mike PVC Automation

Mike voice maintenance now lives beside the render helper as a separate workflow. It does not change the behavior of `render`, `all`, `merge`, or `qa`.

Tracked voice profile config:

- `config/voice_profiles.toml`

Current Mike profile defaults:

- `voice_id=dPrTCMw2R7HQlznlgwCO`
- `category=professional`
- `target_training_models=["eleven_multilingual_sts_v2"]`
- render settings aligned with the current ElevenLabs render path:
  - `stability=0.6`
  - `similarity_boost=0.8`
  - `style=0.0`
  - `use_speaker_boost=true`
  - `speed=0.95`

Voice inspection:

```bash
./scripts/elevenlabs_pvc.py status --voice mike
./scripts/elevenlabs_pvc.py status --voice mike --json
```

Curated sample sync:

```bash
./scripts/elevenlabs_pvc.py sync-samples \
  --voice mike \
  --samples-dir /absolute/path/to/mike-curated-wavs \
  --sample-manifest /absolute/path/to/mike-curated-wavs/sample_manifest.json \
  --dry-run
```

Training missing configured models:

```bash
./scripts/elevenlabs_pvc.py train --voice mike --all-missing
./scripts/elevenlabs_pvc.py train --voice mike --all-missing --dry-run
```

The helper expects a caller-provided directory of curated local WAVs. Those source files stay outside git. An optional `sample_manifest.json` may sit beside them and must be a top-level object keyed by filename:

```json
{
  "mike_take_01.wav": {
    "remove_background_noise": false,
    "trim_start": 120,
    "trim_end": 980,
    "speaker_separation": {
      "start": true
    },
    "notes": "trim the slate before the first usable sentence"
  }
}
```

Supported per-sample keys:

- `remove_background_noise`: boolean
- `trim_start`: non-negative integer milliseconds
- `trim_end`: non-negative integer milliseconds
- `speaker_separation`: `true`, a list of selected speaker ids, or an object with `start` and optional `selected_speaker_ids`
- `notes`: freeform string for local operator context

The sync command diffs local WAVs against the remote Mike sample inventory by SHA-256 hash first and falls back to filename matching when hashes differ. In that fallback case it warns and skips duplicate upload rather than silently creating another remote sample. After training completes, use a small opening audition or hotspot check before any full-episode rerender.

## New Episode Workflow

For a new episode, copy the manifest layout under a new temp folder and override `PIPELINE_DIR`, `MASTER_OUT`, and `EPISODE_DIR`. The normal production path is now lossless WAV end-to-end. If you specifically need smaller lossless files for storage or transfer, you can override to `RESPONSE_FORMAT=flac` and keep both `MASTER_OUT` and `PREMASTER_OUT` aligned with that format, but release packaging still requires WAV. Full renders now also use `PROSODY_GUARD_DIR` under the same pipeline folder for pre-merge transcript analysis, repair manifests, and guarded backups, plus `MASTERING_DIR` for loudness artifacts.

Default WAV example:

```bash
PIPELINE_DIR=/Users/mike/Audio_CascadeEffects/tmp/ep4 \
MASTER_OUT=/Users/mike/Audio_CascadeEffects/output/speech/ep4_master.wav \
EPISODE_DIR=/Users/mike/Episodes_CascadeEffects/Ep4_New-Episode \
./scripts/cascade_tts_pipeline.sh all
```

Optional FLAC override:

```bash
PIPELINE_DIR=/Users/mike/Audio_CascadeEffects/tmp/ep4 \
MASTER_OUT=/Users/mike/Audio_CascadeEffects/output/speech/ep4_master.flac \
PREMASTER_OUT=/Users/mike/Audio_CascadeEffects/tmp/ep4/premaster.flac \
RESPONSE_FORMAT=flac \
./scripts/cascade_tts_pipeline.sh render
./scripts/cascade_tts_pipeline.sh merge
./scripts/cascade_tts_pipeline.sh qa
```

The default mastering target is YouTube-oriented spoken-word loudness:

- `LOUDNESS_TARGET_I=-14`
- `LOUDNESS_TARGET_TP=-1.0`
- `LOUDNESS_TARGET_LRA=11`

That means the checked-in wrapper now treats `PREMASTER_OUT` as the raw concatenated archive and `MASTER_OUT` as the publish-ready loudness-normalized delivery file. In this repo, WAV is the house default because it keeps the entire pipeline lossless while staying simple for DAWs, ffmpeg, inspection, and interchange. FLAC is kept only as an explicit lossless override when smaller files matter more than workflow simplicity.

### Episode Package Contract

Release commands now bind the audio pipeline to the sibling `Episodes_CascadeEffects` repo.

- `EPISODE_DIR` is required for `merge`, `qa`, and `all`
- `EPISODE_SCRIPT` is optional; by default the canonical script is `<EPISODE_DIR>/<basename(EPISODE_DIR)>.txt`
- the canonical release audio path is always `<EPISODE_DIR>/final/<basename(EPISODE_DIR)>.wav`

The release gate verifies that the canonical script exists, is non-empty, and uses only the canonical cue-tag allowlist documented below. After merge, the pipeline copies the staged `MASTER_OUT` into the episode `final/` directory and verifies the packaged file matches the staging master byte-for-byte.

The review asset contract is now explicit:

- Only the packaged WAV under `<EPISODE_DIR>/final/` plus the QA transcript recorded in `<PIPELINE_DIR>/audio_package.json` are promotable review assets.
- `effective_cost_final_jobs.elevenlabs.jsonl` and hotspot MP3 tests are compile-only artifacts. They must never replace the canonical review package.
- The March 30, 2026 Challenger mismatch is the reference failure mode for this rule: compile-only ElevenLabs manifests and hotspot clips do not count until `merge` and `qa` produce a packaged sidecar.

Your new `PIPELINE_DIR` should contain:

- `final_jobs.jsonl`
- `audition_jobs.jsonl` only when you explicitly plan to run `./scripts/cascade_tts_pipeline.sh audition`

And any referenced text chunk files should already be prepared before kickoff.
All active manifests should use `.wav` outputs unless you are explicitly running a FLAC override.

### Cue Tag Convention

Some scripts may include inline editorial cues such as `[calm]`, `[deliberate]`, `[sorrowful]`, or `[pauses]`. Treat the canonical cue-tagged episode script as the source of truth and compile it differently per provider.

- OpenAI path: strip bracket tags from the spoken text and translate them into the instruction fields already used in audition and chunk manifests.
- ElevenLabs path: compile the cue-tagged source script plus the chunk manifest into an effective manifest that is model-aware. `eleven_v3`-style runs keep inline cue tags and pause markers; non-v3 runs fall back to normalized spoken text plus continuity windows and deterministic seeds so cue labels are never read aloud.

The canonical bracket-tag set for checked-in episode scripts is exactly:

- `[calm]`
- `[deliberate]`
- `[matter-of-fact]`
- `[flatly]`
- `[sorrowful]`
- `[resigned]`
- `[frustrated]`
- `[nervous]`
- `[pauses]`

Only these nine tags should appear in canonical episode scripts. Release packaging validates against this allowlist.

If an authored draft uses near-synonyms, normalize them before commit:

- `composed` -> `[calm]`
- `analytical` -> `[matter-of-fact]`
- `somber` -> `[sorrowful]`

If a script uses conflicting, ambiguous, or overly theatrical tags, normalize them to the nearest canonical documentary cue before rendering.

Provider-specific cue handling rules:

- `deliberate` and `matter-of-fact` stay plain; they do not become invented inline audio tags.
- `pauses` becomes punctuation plus `[pause]` or `[short pause]` only for `eleven_v3`-style runs.
- Non-v3 ElevenLabs models use normalized spoken text without inline cue tags.
- The ElevenLabs path in this pipeline does not use SSML `<break>` tags.
- The checked-in base manifests stay provider-neutral; provider-specific manifests are generated artifacts under `PIPELINE_DIR`.

### Pronunciation Preflight

Known ElevenLabs pronunciation risks are checked before render through `scripts/pronunciation_preflight.py`.

- The curated lexicon lives at `references/pronunciation/known_risks_v1.json`.
- `validate` scans `FINAL_JOBS` for known risks.
- `render` compiles provider-specific text, applies approved TTS-only aliases, and fails closed if a required rule was not applied.
- Locked scripts, captions, and `spoken_input` stay canonical; only `elevenlabs_text` may receive pronunciation aliases.
- The active `eleven_multilingual_v2` profile defaults to local aliases, such as `live load` -> `lyve load`, verb `duplicate` -> `dupli-kate`, and `wind-tunnel` -> `wind tunnel`.
- Optional official ElevenLabs pronunciation dictionaries can be passed with `ELEVENLABS_PRONUNCIATION_DICTIONARY_LOCATORS` as JSON or comma-separated `dictionary_id:version_id` entries.

When comparing cue handling for a new script, use these three modes:

- `Mostly flat`: steady documentary tone with minimal emotional variance.
- `Subtle mapping`: restrained cue-driven variation inside the documentary style.
- `Stronger contrast`: more noticeable cue-driven shifts that still stay disciplined and non-theatrical.

For cue-tagged `cedar` documentary narration, `Stronger contrast` is now the house default. `Mostly flat` and `Subtle mapping` remain available as explicit override modes when a project calls for them.

Example:

```text
[sorrowful] This is not a story about a failed part.
```

Can become an instruction summary such as:

```text
Tone: Serious and composed.
Emotion: Restrained somberness.
Pauses: Slight hold after the sentence.
```

### Warm-Up Trim

Some opening jobs benefit from a hidden lead-in so the rendered delivery settles before the audible script starts. The pipeline now supports this as an opt-in manifest feature:

- `warmup_prefix`: hidden text prepended for synthesis only
- `warmup_preroll_ms`: preserved audio before the matched visible start; defaults to `120`
- `warmup_anchor_text`: optional explicit phrase from the visible script used to align the trim point

When `warmup_prefix` is present, the pipeline renders with the hidden lead-in, runs local `transcribe` alignment on the finished file, trims back to the visible start, and fails closed if the real opening cannot be matched confidently.

### Sibilance Workflow

When a finished master sounds sharp on `S`, `SH`, or `CH` sounds, use the reusable sibilance workflow before rerendering whole episodes blindly.

- `sibilance-analyze` scans the packaged master, ranks likely hotspots, and maps them back to chunk IDs plus local chunk offsets.
- `sibilance-audition` builds paired comparison clips using the existing per-job `voice`, `speed`, and `instructions` overrides, then renders them through the normal TTS CLI.
- The first-pass comparison matrix is intentionally small: `cedar@0.95` versus `marin@0.95`.
- If first-pass results are inconclusive, rerun `sibilance-audition` with `SIBILANCE_AUDITION_STAGE=second-pass` and `SIBILANCE_WINNER_VOICE=cedar|marin` to test the anti-sibilance instruction suffix at `0.95` and `0.93`.
- Keep `RESPONSE_FORMAT=wav`; the current offline Speech API quality levers are still `model`, `voice`, `instructions`, and `speed`. `stream_format` is transport-only and not part of this pipeline.
- `sibilance-audition` remains OpenAI-only in v1. It is intentionally not reused for the ElevenLabs provider cutover.

## Production Checks

- Compare opening audition clips only when testing a new voice, a major style change, or an explicit user-requested comparison.
- For sharp fricatives, compare hotspot auditions before rerendering a full episode or applying any master-wide processing.
- Keep every OpenAI TTS input under `4096` characters and every compiled ElevenLabs text payload under `3000` characters.
- Treat `guard` as the automatic pre-merge safety gate for full renders. It can create local repair manifests under `PROSODY_GUARD_DIR`, rerender split micro-repairs, and fail closed before merge if transcript parity is uncertain.
- Check publish loudness before release; the default mastering pass targets `-14 LUFS` and stores its scan artifacts under `MASTERING_DIR`.
- Use warm-up trim for flagged openings that sound soft or unnatural in the first seconds.
- Confirm the merged file stays on one narrator profile.
- Run a human listen pass on the opening, joins, and ending before publish.
- Disclose externally that the narration is AI-generated.
