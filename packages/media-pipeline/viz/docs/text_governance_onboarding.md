# Text Governance Onboarding

Use this flow when adding a new preset to the shared still-and-handoff certification surface.

## 1. Create the preset specs

- Add `draft_txt2img`, `refine_img2img`, and `final_upscale` specs under `workflows/specs/<family>/`.
- Validate the family with `bin/ce workflow validate <family>`.

## 2. Choose the governance class

- `strict_zero_letter`
  - No readable text is allowed in the final certified still.
  - Use cleanup-only repair policy when needed.
  - Keep `typography_mode=off`.
- `controlled_text`
  - Readable text must come from deterministic typography sidecars or shared intents.
  - Add a repair policy if the preset needs source-text repair or post-final cleanup.
  - Add typography sidecars before certification.
- `negative_control`
  - Keep the preset outside the shared cleanup and typography approval path.
  - Do not add repair or typography sidecars.

## 3. Add sidecars only when the class needs them

- Repair policy path: `workflows/source_text_repair/<family>/<preset>.json`
- Typography sidecar path: `workflows/typography/<family>/<preset>.json`
- Shared handoff intent path, when handoff needs typography metadata:
  - `workflows/typography/shared/<preset>_handoff_asset.intent.json`

## 4. Add the matrix entry

Add one entry to `config/text_governance_matrix.json` with:

- `family`
- `preset`
- `canonical_seed`
- `governance_class`
- `source_text_repair_mode`
- `typography_mode`
- `handoff_probe`
- `handoff_frames`
- `width`
- `height`
- `expected_typography_metadata`
- `handoff_typography_intent_path` when `handoff_probe` is `with_typography`

The matrix entry is the certification source of truth. If the preset is not in the matrix, it is not onboarded.

## 5. Run targeted certification

- Still-only:
  - `bin/ce smoke-text --only <family>/<preset> --skip-handoff`
- Full certification when the matrix entry includes a handoff probe:
  - `bin/ce smoke-text --only <family>/<preset>`

Certification passes only when the preset clears its governance-class rules and, if configured, its staged handoff/video probe.

## 6. Promote only after certification

- Add the preset to broader batch generation only after its matrix entry passes.
- If onboarding a preset requires code changes rather than specs + sidecars + one matrix entry, treat that as a pipeline gap and fix the shared system before adding more presets.
