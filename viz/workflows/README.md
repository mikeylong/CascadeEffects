# Comfy Workflows

This directory is the canonical source of truth for Comfy workflow-as-code.

## Layout

- `fragments/`
  Shared graph fragments with symbolic node keys.
- `specs/`
  Canonical family, preset, and stage definitions.
- `generated/`
  Native Comfy workflow JSON, build manifests, and compare reports produced by `bin/ce workflow`.

## Canonical Format

Each workflow spec is JSON and must include:

- `family`
- `preset`
- `base_fragment`
- `params`
- `nodes`
- `links`
- `output`

The specs are declarative. They override symbolic fragment nodes instead of hand-editing Comfy numeric node IDs.

Each asset family now ships in three stages:

- `draft_txt2img`
- `refine_img2img`
- `final_upscale`

Reference boards live outside this directory under `/Users/mike/Viz_CascadeEffects/references`.

## Build Flow

```bash
bin/ce workflow validate
bin/ce workflow build all
bin/ce workflow sync all
bin/ce workflow compare all
```

The repo is canonical. Sync is one-way into:

- `/Users/mike/AI/comfy/user/default/workflows`
