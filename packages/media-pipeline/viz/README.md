# Cascade Effects Local Generation Workspace

Shell-first workflow repo for the local Cascade Effects generation stack on Apple Silicon.

This repo is the control plane for:

- ComfyUI Desktop on macOS for graph workflows and quick iteration
- MFLUX for still-image generation from the terminal
- `mlx-video` for MLX-native video generation
- One shared runtime root at `/Users/mike/AI`

The website repo at `/Users/mike/CascadeEffects` is intentionally separate.

## Command Surface

From this repo:

```bash
bin/ce doctor
bin/ce bootstrap
bin/ce configure-comfy
bin/ce orchestrate doctor
bin/ce orchestrate board
bin/ce orchestrate sync --all
bin/ce workflow list
bin/ce workflow validate
bin/ce workflow build all
bin/ce workflow sync all
bin/ce workflow compare all
bin/ce video backend status
bin/ce video backend prepare
bin/ce workbench init --project /Users/mike/CascadeEffects/packages/media-pipeline/viz/references/episodes/challenger/launch_commit_dolly/workbench/project.json --source-image /absolute/path/to/approved.png --episode-id challenger --motion-item-id launch_commit_dolly --behavior "Other period objects clear from frame as Challenger takes focus and blasts off."
bin/ce workbench serve --project /Users/mike/CascadeEffects/packages/media-pipeline/viz/references/episodes/challenger/launch_commit_dolly/workbench/project.json
bin/ce workbench export-shot --project /Users/mike/CascadeEffects/packages/media-pipeline/viz/references/episodes/challenger/launch_commit_dolly/workbench/project.json
bin/ce render server start
bin/ce render stage shorts_scene_plate challenger_field_joint_closeup draft_txt2img --set variant_count=8
bin/ce render stage thumbnail_plate one_red_flag draft_txt2img --set variant_count=8
bin/ce render stage shorts_cover_plate signal_object_portrait draft_txt2img --set variant_count=8
bin/ce render pipeline shorts_scene_plate challenger_field_joint_closeup --selected-seed <seed>
bin/ce typography apply --target still --artifact /absolute/path/to/final.png --intent /absolute/path/to/intent.json
bin/ce typography validate --target handoff_asset --artifact /absolute/path/to/staged.png --intent /absolute/path/to/intent.json
bin/ce smoke-image
bin/ce smoke-video
bin/ce smoke-motion
bin/ce smoke-typography
bin/ce smoke-text
bin/ce handoff-stage /absolute/path/to/file.png --from comfy --typography-intent /absolute/path/to/intent.json
bin/ce handoff-i2v /absolute/path/to/staged-file.png --typography auto
```

`bin/ce orchestrate ...` delegates to the Agents orchestration helper in `/Users/mike/CascadeEffects/packages/production-tools` while keeping one user-facing `ce` surface.

## Particle Workbench

Particle Workbench is the local hero-subject authoring path for particle breakup shot proofs.

New standalone particle experiments and branch history now live in `/Users/mike/Particle_Playground` and the private `mikeylong/Particle_Playground` repository. Keep this repo focused on the integrated Viz CLI surface and production handoff paths.

- `bin/ce workbench init --project <project.json> --source-image <source-image> [--mask-image <mask.png>] --episode-id <episode> --motion-item-id <motion> --behavior "<approved beat>"` creates a workbench project bundle from any single source image. Existing alpha auto-approves the mask; otherwise the workbench generates a proposal mask for review.
- `bin/ce workbench serve --project <project.json>` launches the local browser UI as a three-step product surface: `Source`, `Mask`, then `Effect`.
- `bin/ce workbench export-shot --project <project.json>` renders a reviewable opaque MP4 proof plus a JSON export manifest with duration, fps, poster, and still paths.
- `bin/ce workbench export-shot --project <project.json> --alpha` renders a transparent-background ProRes 4444 `.mov` for overlay/compositing use. Use this for plume, smoke, sparks, or other FX elements that will be layered in the final edit.
- The shell wrapper runs through `${CE_MLX_VIDEO_PYTHON}` so the same local image/video environment handles project analysis and proof export.
- Step 1 can upload additional source candidates into the project-local `sources/` bundle. One candidate is active at a time, and switching candidates resets mask/effect state for that source while preserving the candidate record.
- Step 1 also exposes an experimental `model_source_spike` panel. This is a research-only fallback, not the primary authored path.
- The currently connected providers are `NASA 3D` (`open_access`, enabled, best for real-world and aerospace subjects), `Poly Pizza` (`open_license`, enabled, but only `CC0` assets are currently eligible), and `Smithsonian Open Access` (`open_access`, currently search-only in the local runtime).
- The broader generic-production shortlist is `Poly Haven`, `Quaternius`, and `Kenney`, but those sources are not connected yet. Research-only references such as `OpenGameArt`, `Wikimedia Commons 3D`, `Objaverse-XL`, and `Google Scanned Objects` are not surfaced as production-ready providers.
- Selecting a fetched model switches `scene.volume_backend` from `acquired_shell` to `model_source_spike`.
- Model-source downloads stay local. Raw assets are cached under `~/.cache/cascade-effects/model-sources/<provider>/<id>/`, and project-local selections are normalized into `<project>/model_source/` with a deterministic sampled point cache for preview/export parity.
- The current renderer is built for one hero subject even when the source image includes scenery: the approved mask defines the subject, the background is discarded from the effect, and preview/export both fail until the mask is approved.
- The Effect stage is a local WebGL point-cloud viewer. Orbit, pan, and dolly the camera in the viewport directly; that saved camera becomes the authoritative export camera for `export-shot`.

## What `bootstrap` Does

- Verifies macOS on Apple Silicon
- Creates the `/Users/mike/AI` folder tree
- Installs missing `uv` and ComfyUI Desktop via Homebrew
- Installs `mflux` with `uv tool install --upgrade mflux`
- Initializes `/Users/mike/AI/mlx-lab`
- Initializes `/Users/mike/AI/mlx-video`

It is designed to be idempotent.

## Required Manual Step

ComfyUI Desktop first launch stays manual by design.

1. Launch ComfyUI Desktop.
2. Choose `MPS`.
3. Set the install location to `/Users/mike/AI/comfy`.
4. Let ComfyUI finish its managed-environment setup.
5. Return here and run:

```bash
bin/ce configure-comfy
```

That writes:

- `/Users/mike/Library/Application Support/ComfyUI/extra_models_config.yaml`

from the template in this repo, pointing ComfyUI at `/Users/mike/AI/models`.

## Smoke Tests

The prompt fixtures live in:

- `/Users/mike/CascadeEffects/packages/media-pipeline/viz/config/prompts/smoke-image.txt`
- `/Users/mike/CascadeEffects/packages/media-pipeline/viz/config/prompts/smoke-video.txt`

Outputs land in:

- `/Users/mike/AI/outputs/mlx-images`
- `/Users/mike/AI/outputs/mlx-video`
- `/Users/mike/AI/outputs/handoff`

Cross-asset text certification is matrix-driven:

- The matrix lives at `/Users/mike/CascadeEffects/packages/media-pipeline/viz/config/text_governance_matrix.json`
- `bin/ce smoke-text` runs the full certification set
- `bin/ce smoke-text --only family/preset` runs one preset
- `bin/ce smoke-text --skip-handoff` keeps the run on still certification only
- Each smoke run writes a summary JSON under `/Users/mike/AI/outputs/logs/smoke-text-*`

## Workflow As Code

Comfy workflows are now treated as repo-managed assets.

- Canonical fragments live in `/Users/mike/CascadeEffects/packages/media-pipeline/viz/workflows/fragments`
- Canonical workflow specs live in `/Users/mike/CascadeEffects/packages/media-pipeline/viz/workflows/specs`
- Shared art-direction profiles live in `/Users/mike/CascadeEffects/packages/media-pipeline/viz/workflows/style_profiles`
- Generated native Comfy workflow JSON lives in `/Users/mike/CascadeEffects/packages/media-pipeline/viz/workflows/generated`
- Generated API prompt JSON lives alongside the workflow artifacts as `*.prompt.json`
- Reference boards live in `/Users/mike/CascadeEffects/packages/media-pipeline/viz/references`

The live Comfy sync target is:

- `/Users/mike/AI/comfy/user/default/workflows`

Typical workflow commands:

```bash
bin/ce workflow list
bin/ce workflow validate
bin/ce workflow build shorts_scene_plate
bin/ce workflow sync all
bin/ce workflow compare all
bin/ce workflow diff shorts_scene_plate
```

## Active Art Direction

The active image system now runs on a shared `systems_failure_collage` profile.

- The visual language is zero-letter editorial collage rather than realism-adjacent reconstruction.
- Historical cues stay recognizable, but they should survive as fragments: torn-paper seams, schematic overlays, circuit traces, halftone/xerox grain, dark-cream field splits, and poster-like compression.
- `scene_still` is retired from the active workflow surface; use `shorts_scene_plate` for short beat stills and packaging families for cover/thumbnail work.
- `thumbnail_plate` and `shorts_cover_plate` stay packaging-aware, but they now use montage logic and title-friendly negative space instead of raw single-object hardware isolation.
- `evidence_card_plate` is active again for controlled-text clue, dossier, and memo surfaces that use deterministic overlay-ready layouts.
- `systems_failure_tense` remains on disk only as a legacy fallback reference.

Active specs still declare shared style metadata directly:

- `style_profile`
- `temperature`
- `palette_policy`
- `accent_palette`
- `human_presence`
- `safe_zone_intent`

Validation still enforces strict zero-letter for non-typography assets and controlled-text replacement surfaces for typography-enabled assets, while rejecting readable-text dependence in prompts, documentary-realism framing, astronaut heroics, courtroom shorthand, and explosion-poster melodrama.

## Headless Rendering

Comfy rendering no longer requires manual UI interaction.

- `bin/ce render server start` launches a dedicated headless Comfy backend on `http://127.0.0.1:8188`
- `bin/ce render stage <family> <preset> <stage>` builds the prompt artifact, queues the render over HTTP, waits for completion, and writes a run manifest
- `bin/ce render pipeline <family> <preset> --selected-seed <seed> --typography auto|off|force` runs the draft, refine, final, and optional controlled-typography stages in sequence when the required runtime assets are present
- `bin/ce render typography <family> <preset> --image /absolute/path/to/final.png` reapplies the controlled-typography pass to an existing still without rerunning generation

Run manifests land under:

- `/Users/mike/CascadeEffects/packages/media-pipeline/viz/workflows/generated/runs`

Each run manifest records the prompt id, selected seed, source image, artifact paths, and output files for reproducibility.

## Controlled Typography

Readable type in active imagery now stays outside the generative prompts by default.

- Zero-letter prompt validation still applies to the draft, refine, and final image-generation stages
- Controlled readable text is declared in preset sidecars under `/Users/mike/CascadeEffects/packages/media-pipeline/viz/workflows/typography`
- Producer-agnostic shared intent fixtures live under `/Users/mike/CascadeEffects/packages/media-pipeline/viz/workflows/typography/shared`
- `bin/ce typography apply --target still|handoff_asset|image_sequence|video --artifact <abs-path> --intent <abs-path>` applies the shared contract directly
- `bin/ce typography validate --target ...` validates an existing artifact against the same intent
- `bin/ce smoke-typography` is the required fixture smoke path for shared still intents, shared handoff intents, and the current explicit stubs
- `bin/ce smoke-text` is the matrix-driven certification harness for active presets across strict zero-letter, controlled-text, and negative-control classes
- `bin/ce smoke-motion` is the matrix-driven still-to-video certification harness for motion proofs and typography-metadata expectations
- `enabled: true` opts a preset into the automatic postprocess when `bin/ce render pipeline ... --typography auto` is used
- `enabled: false` keeps the sidecar available for manual smoke tests or targeted reruns through `bin/ce render typography ...`
- v1 ships `still` and `handoff_asset` adapters today; `image_sequence` and `video` currently return explicit not-yet-implemented errors
- `render pipeline` remains the only automatic production path today
- `handoff-stage` can attach `--typography-intent`, and `handoff-i2v` defaults to `--typography auto`, which means it only applies typography when the staged manifest already carries an enabled intent
- Shared source-text governance classes are certified through the matrix in `/Users/mike/CascadeEffects/packages/media-pipeline/viz/config/text_governance_matrix.json`
- Motion proof certification lives beside it in `/Users/mike/CascadeEffects/packages/media-pipeline/viz/config/motion_certification_matrix.json`
- Shared intents under `workflows/typography/shared` are checked-in reference fixtures, not auto-enabled rollout assets
- Current video scope is input-still robustness only. The handoff lane certifies staged stills and typography metadata, but there is no temporal OCR or frame-level cleanup yet.

## Rapid Production Loop

The default production loop now assumes:

- Start from the short-specific still lane or an approved still override
- Shortlist 1 to 2 stills from the generated batch
- Stage one shortlisted still into the MLX video lane
- Keep retired `scene_still` outputs out of new production decisions

Typical daily commands:

```bash
bin/ce render server start
bin/ce render stage shorts_scene_plate challenger_field_joint_closeup draft_txt2img --set variant_count=8
bin/ce handoff-stage /absolute/path/to/short-still.png --from comfy --prompt "<approved motion prompt>"
bin/ce handoff-i2v /Users/mike/AI/outputs/handoff/<staged-file>
bin/ce render server stop
```

`bin/ce handoff-i2v` now defaults to a cheaper proof pass:

- `33` frames
- the `distilled` pipeline
- the MLX-native repo `mlx-community/LTX-2-distilled-bf16`
- automatic backend preparation into `/Users/mike/AI/models/mlx-video/prepared`
- dimensions clamped to a lighter-weight size when using large still manifests
- Hugging Face downloads stored under `/Users/mike/AI/cache/huggingface`

Install the full FLUX assets before expecting `refine_img2img` and full Challenger still-pipeline validation to pass. Until those assets are present, the shared-typography rollout should stop at docs plus smoke coverage rather than treating the full render pipeline as production-ready.

The repo is canonical. Generated JSON can be synced one-way into Comfy Desktop, but live edits in Comfy are disposable unless they are brought back into the repo intentionally.

The production workflow is now staged:

- `draft_txt2img` for fast FP8 ideation
- `refine_img2img` for full-FLUX detail passes
- `final_upscale` for canonical deliverables

`bin/ce workflow compare` writes a report under `/Users/mike/CascadeEffects/packages/media-pipeline/viz/workflows/generated/reports` with workflow params, dependency status, and matching Comfy outputs.

## Custom Nodes

v1 policy is intentionally conservative:

- Prefer ComfyUI Manager
- Install only trusted nodes
- Keep trusted repos documented in `/Users/mike/CascadeEffects/packages/media-pipeline/viz/config/policies/trusted-custom-nodes.txt`
- If manual install is required, do it inside ComfyUI's managed environment, not your global shell environment

## Handoff Workflow

Stage a still for downstream MLX work:

```bash
bin/ce handoff-stage /absolute/path/to/image.png --from comfy --prompt "Slow documentary move through a lab" --typography-intent /absolute/path/to/intent.json
```

That creates:

- A symlinked staged asset in `/Users/mike/AI/outputs/handoff`
- A JSON sidecar manifest with prompt, seed, dimensions, next-step metadata, and optional `typography_intent_path`

Run image-to-video from the staged file:

```bash
bin/ce handoff-i2v /Users/mike/AI/outputs/handoff/<staged-file>.png --typography auto
```

The handoff lane currently certifies input-still robustness only:

- staged stills may carry a typography intent
- `handoff-i2v` may apply typography and shared cleanup before video generation
- no temporal OCR, frame-level cleanup, or sequence-aware text governance ships yet

`--typography auto` is the default and only applies typography when the staged manifest already carries an enabled intent. `--typography off` disables that behavior, and `--typography force` requires an explicit or staged intent.

Inspect or prepare the MLX backend explicitly:

```bash
bin/ce video backend status
bin/ce video backend prepare
bin/ce video backend status --model-repo prince-canuma/LTX-2-distilled
```

The backend helper keeps the official source repo as the canonical input, converts flat LTX repos into the modular layout expected by `mlx_video 0.0.1`, and stores prepared compatible backends under:

- `/Users/mike/AI/models/mlx-video/prepared`

`bin/ce handoff-i2v` now calls that prepare step automatically and records both the original source repo and the resolved prepared local path in the video manifest.

When typography is applied in the handoff path, the video manifest also records:

- `input_base_image_path`
- `input_image_path`
- `typography_run_manifest`
- `typography_intent_path`
- `typography_validation`

Override the default MLX video repo explicitly if needed:

```bash
bin/ce handoff-i2v /Users/mike/AI/outputs/handoff/<staged-file>.png --model-repo mlx-community/LTX-2-distilled-bf16
```

Experimental quantized repos can also be passed explicitly, and `handoff-i2v` now supports an optional paired text-encoder repo when a model bundle does not include one:

```bash
bin/ce handoff-i2v /Users/mike/AI/outputs/handoff/<staged-file>.png --model-repo <video-model-repo> --text-encoder-repo <text-encoder-repo>
```

## References

- [ComfyUI Desktop macOS](https://docs.comfy.org/installation/desktop/macos)
- [ComfyUI custom nodes](https://docs.comfy.org/installation/install_custom_node)
- [uv projects](https://docs.astral.sh/uv/guides/projects/)
- [MFLUX](https://github.com/filipstrand/mflux)
- [mlx-video](https://github.com/Blaizzy/mlx-video)
