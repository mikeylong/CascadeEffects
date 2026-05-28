# FLUX.2 Dev 9:16 Still-Series Lab

`/Users/mike/FluxLab_CascadeEffects` is a standalone Cascade Effects look-dev lab for real ComfyUI FLUX.2 Dev still-image workflows.

This repo does not touch `/Users/mike/StyleLab_CascadeEffects` or the current orchestration repos.

## Scope

- Vertical `9:16` still-image look development only
- Six scene variants:
  - `challenger_a`
  - `challenger_b`
  - `therac25_a`
  - `therac25_b`
  - `boeing737max_a`
  - `boeing737max_b`
- Two explicit stages:
  - `lookdev`: `864x1536`, batch size `4`
  - `refine`: `1024x1792`, batch size `1`

## Command Surface

```bash
bin/ceflux bootstrap
bin/ceflux workflow export challenger_a --stage lookdev
bin/ceflux render challenger_a --stage lookdev
bin/ceflux refine challenger_a --run <lookdev-run-id> --pick 2
bin/ceflux benchmark export minimal_surreal_v1_v2_v3_go_no_go --case single_object_or_device --style minimal_surreal_editorial_v3
bin/ceflux benchmark render minimal_surreal_v1_v2_v3_go_no_go
bin/ceflux benchmark report minimal_surreal_v1_v2_v3_go_no_go --run <benchmark-run-id>
bin/ceflux proof export minimal_surreal_v3_first_look --case single_object_or_device
bin/ceflux proof render minimal_surreal_v3_first_look
bin/ceflux proof report minimal_surreal_v3_first_look --run <proof-run-id>
```

## Layout

- `bin/ceflux`: shell entrypoint
- `scripts/ceflux_tool.py`: Python launcher
- `fluxlab/`: implementation
- `prompts/canon.json`: shared prompt canon
- `scenes/`: six scene manifests
- `benchmarks/suites/`: isolated benchmark suite manifests
- `proofs/suites/`: isolated proof-review suite manifests
- `templates/raw/`: vendored official ComfyUI FLUX.2 Dev UI workflow
- `templates/api/`: canonical API prompt template adapted from the official workflow
- `exports/`: exported scene-stage workflow JSONs
- `runs/`: run manifests and lookdev/refine selection metadata
- `reports/`: benchmark and proof review reports
- `tests/`: contract and smoke coverage

## Official Sources

- Raw UI template source: [ComfyUI FLUX.2 Dev Example](https://docs.comfy.org/tutorials/flux/flux-2-dev)
- FLUX family source of truth: [Black Forest Labs FLUX.2 overview](https://docs.bfl.ai/flux_2/flux2_overview)

The repo vendors the official ComfyUI `image_flux2_text_to_image.json` workflow in raw form. The API template in `templates/api/` is derived from that workflow and adapted to expose the extra lab fields needed by this project: `negative_prompt`, `batch_size`, `seed`, and `filename_prefix`.

## Runtime

Defaults live in [config/paths.env](/Users/mike/FluxLab_CascadeEffects/config/paths.env):

- `CE_COMFY_ROOT=/Users/mike/AI/comfy`
- `CE_COMFY_API_URL=http://127.0.0.1:8000`
- `CE_FLUXLAB_OUTPUT_NAMESPACE=cascadeeffects_fluxlab`
- `CE_FLUXLAB_DIFFUSION_MODEL_FILENAME=flux2-dev.safetensors`

`bootstrap` validates repo assets, the local Comfy root, required model files, and server reachability. Missing model files fail bootstrap explicitly. Server reachability is reported but not required for workflow export.

As of April 4, 2026, the official ComfyUI FLUX.2 Dev example still points at the quantized `flux2_dev_fp8mixed.safetensors` file, but this lab defaults to the full-size `flux2-dev.safetensors` checkpoint for Apple Silicon compatibility. If you use a different BF16/FP16 diffusion filename locally, set `CE_FLUXLAB_DIFFUSION_MODEL_FILENAME` to that exact filename.

## Notes

- The official FLUX.2 Dev text-to-image template is positive-guidance-first. This repo retains the shared negative prompt as an explicit exported field and an unconnected CLIP encode branch for portability and future template swaps.
- Lookdev seed selection is recorded as `base_seed + image_index` so refine runs can lock onto one chosen candidate deterministically.
- Exported UI and API workflows patch the model loader nodes from runtime config, so queued renders stay aligned with the local checkpoint filenames instead of the vendored template defaults.
