# Source Preserving Documentary Package v1

`source_preserving_documentary_v1` is the active documentary-first reset package for scoped Cascade Effects visual work. It exists to keep recognizable researched subjects intact while still allowing one restrained mechanism-bearing wrong state when the beat needs it.

For the Challenger-first restart, this package is a scoped reference library, not an automatic source of active constraints. The active episode constraint ledger decides which parts of this package apply to the current scoped short.

This package is intentionally separate from earlier versions:

- `minimal_surreal_editorial` is frozen as historical v1.
- `minimal_surreal_editorial_v2` is frozen as an intermediate experiment.
- `minimal_surreal_editorial_v3` is the superseded reset package name retained only in historical proofs, manifests, and provenance.

## Design Intent

This package is built around a simple rule:

- renderable subject archetypes are the base vocabulary
- research anchors decide what identity must survive
- editorial meaning is added through tightly scoped wrong-state carriers
- prompts should stay concrete, short, and model-friendly

The generator should be told what is in frame, what must remain recognizable, and what one thing is wrong. It should not be asked to solve abstract layout theory.

## Anti-Confusion Rules

- `reference inputs` means generation inputs only: source photos, boards, subject plates, composition guides, or other assets used to steer generation.
- `generated outputs` means images produced by a model: drafts, candidate stills, approved stills, or final exported assets.
- Files in this style package are contract and guidance files only. They are not generated outputs.
- This package does not adopt itself into any lane automatically.
- This package does not hydrate archived, experimental, retired, or prior episode context unless an exact file is DP-imported in the workflow scope manifest.

## Adoption Status

- `source_preserving_documentary_v1` is the active style-package name for live coordinator docs, templates, and profiles.
- Historical proofs, manifests, keeper records, and generated outputs that still mention `minimal_surreal_editorial_v3` remain valid provenance and should not be rewritten just to match the new name.

## Package Layout

- `SKILL.md`: human-readable style guidance
- `visual.contract.json`: structured contract for the style
- `judgment/subject_render_matrix.md`: archetype-by-archetype rules for preserving subjects while carrying anomaly
- `judgment/casebook.md`: proof-backed examples of what worked, what needed tightening, and what failed
- `judgment/review_rubric.md`: human review checklist and disposition rules
- `judgment/promotion_workflow.md`: still -> motion -> reel gate logic and escalation rules
- `archival_signal_texture_recipes.json`: global era-aware full-bleed historical signal texture profiles for approved archival, broadcast-linked, or period-media-derived Shorts motion
- `judgment/keeper_registry.md`: current keepers, tighten queue, and unresolved lanes
- `prompts/master_prompt.txt`: shortest generator-facing style anchor
- `prompts/negatives.txt`: default negative terms
- `prompts/archetypes.txt`: renderable subject classes
- `prompts/modifiers.txt`: attachable style/state controls
- `prompts/examples.txt`: cross-domain prompt examples
- `comfyui/workflow-spec.md`: prompt recipe and FLUX/Comfy usage
- `eval/evaluator-spec.json`: evaluation weights and hard fails
- `eval/sample-score-output.json`: sample evaluator payload
- `eval/starter_evaluator.py`: starter evaluator scaffold

## Judgment Layer

This package includes a subject-render judgment layer. During the restart, use it only after checking the workflow scope manifest and active constraint ledger.

- `judgment/subject_render_matrix.md` tells you how each archetype should carry anomaly without losing canonical identity.
- `judgment/casebook.md` shows legacy proof-backed examples from recent Challenger, Therac-25, Hyatt Regency, and 737 MAX runs. They are inactive unless imported and activated by DP.
- `judgment/review_rubric.md` defines the keep / tighten / diagnostic only / reject decision rules.
- `judgment/promotion_workflow.md` defines what may advance from still to motion and from motion to reel use.
- `judgment/keeper_registry.md` records the current promoted examples and unresolved lanes.

Historically, this layer was intended to prevent repeated failure modes across the full episode slate:

- subject deformation masquerading as surrealism
- camera choices that hide the actual mechanism of failure
- anomaly cues that read as sampler corruption instead of believable wrong-state conditions
- anonymous evidence-room drift where the researched subject collapses into a generic folder, tray, or prop with no recognizable source anchor left

FluxLab proof notes should mirror this same disposition vocabulary so review state is consistent across stills, motion clips, and reels.

## Compatibility Note

The linked style profiles still carry `caption_safe_defaults` for pipeline compatibility. In `source_preserving_documentary_v1`, that field is downstream frame-safety metadata, not generator-facing prompt guidance.
