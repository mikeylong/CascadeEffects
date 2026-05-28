# Standalone Vertical Style Lab

`/Users/mike/StyleLab_CascadeEffects` is a zero-integration lab for pushing a new Cascade Effects house style without touching the current episode pipeline.

The v1 lab treats the brief as a hard visual grammar:

- radical simplicity of form
- dominant emotional color fields
- asymmetric composition with active negative space
- one restrained vivid accent
- painterly edge bleed with quiet surfaces
- stillness with implied story

Primary output is vertical `9:16` at exactly `1080x1920`.

## Command Surface

```bash
bin/cestyle bootstrap
bin/cestyle still render scene_01_shuttle_exterior --mode sketch
bin/cestyle still render scene_01_shuttle_exterior --mode final
bin/cestyle still render scene_01_shuttle_exterior --mode lock
bin/cestyle motion render motion_01_shuttle_exterior --preset stillness_breathe
bin/cestyle short build challenger_short_v1
bin/cestyle board build
bin/cestyle eval
```

## Layout

- `bin/cestyle`: shell entrypoint
- `scripts/lib.sh`: shared runtime defaults
- `scripts/cestyle_tool.py`: Python CLI launcher
- `stylelab/`: style lab implementation
- `profiles/`: lab style profiles
- `scenes/`: benchmark scene manifests
- `shorts/`: reusable short-form manifests
- `references/benchmark_pack.json`: benchmark inventory
- `renders/`, `exports/`, `boards/`, `evaluations/`: lab-owned outputs
- `tests/`: unit and smoke coverage

## Runtime

The lab shares the existing `/Users/mike/AI` runtime. By default it uses:

- `CE_HOME=/Users/mike/AI`
- `CE_STYLELAB_PYTHON=/Users/mike/AI/mlx-video/.venv/bin/python`

Override those in `config/paths.env` if needed.

## Current Backend

The lab now uses a source-free symbolic compositor and motion renderer. Scene manifests describe a single subject archetype and the renderer stages that subject directly from the style grammar rather than translating external reference images. Prompt canon and mode contracts are still structured so a future FLUX/Comfy or Kontext-backed implementation can replace the compositor without changing scene manifests or export contracts.

## Current Short Pilot

`challenger_short_v1` is the first reusable vertical short package in the lab.

- Timing comes from the existing mastered short audio and transcript.
- Beat scenes live in `scenes/scene_challenger_beat_*.json`.
- The short manifest lives at `shorts/challenger_short_v1.json`.
- The packaging frame is reused from the beat-07 closing image rather than maintained as a separate short-only scene.
