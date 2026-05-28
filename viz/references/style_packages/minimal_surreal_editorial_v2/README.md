# Minimal Surreal Editorial Package v2

Drafted on 2026-04-10 as a looser FLUX-facing revision of `minimal_surreal_editorial`.

This version keeps the useful constraints:

- one dominant read
- one dominant anomaly
- controlled palette
- no text or UI artifacts
- clear thumbnail legibility

This version deliberately relaxes the overfit constraints from v1:

- no generator-facing caption-safe composition rule
- no forced outer-third placement
- no forced 60-75% empty field
- no mandatory single saturated accent
- no fixed soft-diffuse-only lighting
- no assumption that the image should behave like a quiet architecture poster

Tooling note:

- `caption_safe_defaults` still exists in the style profile for pipeline compatibility.
- In v2 it should be treated as downstream packaging metadata, not as prompt content to hand to the image model.

This package includes:

- `SKILL.md`
- `visual.contract.json`
- `prompts/master_prompt.txt`
- `prompts/negatives.txt`
- `prompts/variants.txt`
- `comfyui/workflow-spec.md`
- `eval/evaluator-spec.json`
- `eval/sample-score-output.json`
- `eval/starter_evaluator.py`

Suggested experiment lanes:

1. subject-first prompt only
2. subject-first prompt + v2 contract
3. subject-first prompt + v2 contract + evaluator gate
