# Promotion Workflow

Use this workflow after rendering. It turns the v3 judgment layer into explicit promotion decisions for stills, motion clips, contact sheets, and video proofs.

For Cascade Effects YouTube Shorts, map this workflow to the coordinator sequence:

`script -> audio -> stills contact sheet -> stills video proof -> motion contact sheet -> motion video proof -> video final`

This workflow owns visual promotion decisions through `motion video proof`. It does not own `video final`; final caption overlays and publishable export route to `/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_final_export_v1/SKILL.md`.

Consult it together with:

- `judgment/subject_render_matrix.md`
- `judgment/review_rubric.md`
- `judgment/casebook.md`
- `judgment/keeper_registry.md`

## Shared Vocabulary

Use only these dispositions:

- `keep`
- `tighten`
- `diagnostic only`
- `reject`

Additional reel class:

- `mixed review reel`: a reel containing any clip that is not `keep`
- `mixed review short`: a Shorts proof containing any still or motion clip that is not `keep`

## Gate 1: Stills Contact Sheet Before Stills Video Proof

Prerequisites:

- short audio is already `keep`
- short audio provenance is recorded and validated: `short_audio_package_path`, `expected_voice_profile_id`, `audio_package_sha256`, `audio_disposition`, `caption_source_path`, and `transcript_sha256`
- each candidate still has a current review note
- the contact sheet path is recorded

Contact-sheet review questions:

- Does each beat have enough candidate coverage to choose a current best still or name a gap?
- Does the selected still preserve subject identity and expose the mechanism?
- Are any candidates blocked by text leakage, anatomy corruption, warped geometry, or hidden mechanism?

Promotion rule:

- Only selected or `keep` stills can enter `stills video proof`.
- `tighten`, `diagnostic only`, and `reject` stills stay in the still lane.
- Contact sheets are human-visible selection gates, not final outputs.

## Gate 2: Stills Video Proof Before Motion Contact Sheet

Prerequisites:

- the stills contact sheet has been reviewed
- selected stills or named gaps are recorded
- the static proof uses approved short audio and preserves the validated package/transcript provenance

Proof review questions:

- Does the static proof cover opening, middle, and closing beats?
- Do the selected stills read in the intended sequence against narration?
- Are pacing, timing, beat order, and visual variety acceptable before motion?

Promotion rule:

- Only beats with selected or `keep` stills can enter motion candidate generation.
- If the static proof exposes a weak beat or missing carrier, return to the still lane.
- A diagnostic stills video proof does not authorize motion for unresolved beats.

## Gate 3: Motion Contact Sheet Before Motion Video Proof

Prerequisite:

- the source still must already be selected or `keep`
- the default motion contact sheet matrix must compare both model families for each eligible source still: two `distilled` candidates using `mlx-community/LTX-2-distilled-bf16` and two `apple-ltx23-q8-one-stage` candidates using `dgrauet/ltx-2.3-mlx-q8` plus `mlx-community/gemma-3-12b-it-4bit`
- the two seed slots must match across model families
- candidate A must use the canonical beat motion prompt
- candidate B must use the beat-class stability prompt for `locked context`, `human/tableau`, or `documentary anomaly`
- hard or motion-brittle beats must have a primary still plus one alternate motion-ready still before the matrix is rendered; hard beats include `human/tableau`, strict historical geometry, locked-context shots, or beats where motion already exposed source-baked defects

Required review questions:

- Does each motion candidate preserve canonical subject identity across time?
- Does the anomaly stay plausible under motion?
- Does motion clarify the subject instead of obscuring it?
- Is there temporal text leakage, edge tearing, liquid warping, geometry boil, or short-lived artifacting?
- If the motion problem is inherited from the still, was the still repaired upstream first?
- Did either model family win cleanly, or did both models fail in a way that requires still or carrier repair?
- Does any alternate still produce a better motion outcome without weakening the still-stage read?

Hard blockers:

- temporal anatomy corruption
- motion-induced warped geometry
- inherited still defects left unresolved
- readable text or UI leakage becoming more dominant in motion

Promotion rule:

- A motion candidate may enter `motion video proof` only if the source still is selected or `keep` and motion introduces no blocking artifact.
- Motion contact sheets must be grouped by beat, source still, model family, prompt variant, and seed.
- Motion candidate notes must record `beat_id`, `source_still_path`, `source_still_variant_role`, `motion_pipeline`, `model_repo`, `text_encoder_repo` when applicable, `seed`, `prompt_variant_id`, prompt text or prompt path, raw and normalized clip paths, disposition, and whether the clip is selected for the motion video proof.
- The standard four-candidate dual-model matrix counts as one planned comparison pass. Further rerenders require a recorded prompt, still, or carrier decision.
- Use denser sampling than 1fps when short-lived defects matter.
- If motion exposes a source-baked issue, disposition the still as `tighten` and rerender upstream before attempting another motion pass.
- If both model families fail on the same still for the same reason, route back to stills instead of endlessly rerendering motion.
- Do not use motion rerenders as anatomy repair.

## Gate 4: Motion Video Proof Before Final Export

Prerequisites:

- every included clip already has a recorded motion review
- every included clip has a current disposition
- the motion proof uses approved short audio and preserves the validated package/transcript provenance
- a beat sheet is generated beside the proof and recorded as `beat_sheet_path`

Keeper short rule:

- a `keeper short` may contain only `keep` motion clips
- a `keeper short` must use selected motion winners from the reviewed motion contact sheet, not unreviewed comparison clips

Mixed review short rule:

- if any included clip is `tighten`, `diagnostic only`, or `reject`, the proof must be labeled `mixed review short`
- timed A/B comparison proofs that include both model families are diagnostic unless all included clips are independently reviewed as `keep`; they are not final-export inputs until selected winners are assembled into a keeper proof
- mixed review shorts are internal review tools, not final-export inputs

No-placeholder rule:

- diagnostic placeholders are never allowed in a keeper short or `video final`

## Legacy Gate: Still Before Motion

Required review questions:

- Does the subject remain canonical?
- Does the anomaly read as a believable wrong state?
- Is the anomaly visible without prompt explanation?
- Does the camera actually expose the mechanism?
- Is there any text leakage, anatomy corruption, or source-baked defect?

Hard blockers:

- anatomy corruption
- readable text or logo leakage
- warped geometry used as surrogate surrealism
- a camera angle that hides the claimed failure mechanism

Promotion rule:

- Only `keep` stills are eligible for motion promotion.
- `tighten`, `diagnostic only`, and `reject` stills stay in the still lane.
- If the still is unresolved, no downstream motion clip may be treated as a keeper.

## Legacy Gate: Motion Before Reel

Prerequisite:

- the source still must already be `keep`

Required review questions:

- Does the clip preserve canonical subject identity across time?
- Does the anomaly stay plausible under motion?
- Does motion clarify the subject instead of obscuring it?
- Is there temporal text leakage, edge tearing, liquid warping, or geometry boil?
- If the motion problem is inherited from the still, was the still repaired upstream first?

Hard blockers:

- temporal anatomy corruption
- motion-induced warped geometry
- inherited still defects left unresolved
- readable text or UI leakage becoming more dominant in motion

Promotion rule:

- A motion clip may be `keep` only if the source still is `keep` and motion introduces no blocking artifact.
- If motion exposes a source-baked issue, disposition the still as `tighten` and rerender upstream before attempting another motion pass.
- Do not use motion rerenders as anatomy repair.

Backend adoption rule:

- Keep `distilled` using `mlx-community/LTX-2-distilled-bf16` as the baseline motion lane.
- Use Apple-native LTX 2.3 MLX Q8, `apple-ltx23-q8-one-stage` with `dgrauet/ltx-2.3-mlx-q8` and `mlx-community/gemma-3-12b-it-4bit`, as the standard comparison lane in motion contact sheets.
- Treat model or backend wins as beat-level carrier evidence first.
- A single hard-case win does not justify a full-short or full-episode rerender on that backend.
- If a broader comparison reel makes previously rational beats read as nonsense, text drift, or invented causality, mark the reel `diagnostic only` or `reject` and keep the prior baseline as the default lane.
- Keep comparison-only manifests out of the active short namespace. Store them under `shorts/experiments/` and build them only with an explicit manifest-path command.
- When reopening prompts for a new backend family, separate motion briefs into `locked context`, `human/tableau`, and `documentary anomaly` carriers instead of reusing one generic restrained-motion prompt.
- For Apple-native LTX 2.3 human/tableau briefs, use concrete role/blocking clauses and fixed-room/object clauses. Avoid abstract micro-body-motion phrases and chair or seat-negation wording that can trigger generic sit-down behavior or furniture hallucination.

## Legacy Gate: Reel Before Downstream Use

Prerequisites:

- every included clip already has a recorded motion review
- every included clip has a current disposition

Keeper reel rule:

- a keeper reel may contain only `keep` clips

Mixed review reel rule:

- if any included clip is `tighten`, `diagnostic only`, or `reject`, the reel must be labeled `mixed review reel`
- mixed review reels are internal review tools, not promoted selects

No-placeholder rule:

- diagnostic placeholders are never allowed in a keeper reel
- diagnostic placeholders are never allowed in a keeper short or `video final`

## Escalation Rules

Use this escalation order:

1. fix the still if the defect is source-baked
2. tighten camera or anomaly carrier if the mechanism is hidden
3. review the stills contact sheet before building a stills video proof
4. rerender motion only after the still is trustworthy
5. review the motion contact sheet before building a motion video proof
6. update the keeper registry only after the result is genuinely promotable

If a lane keeps failing for the same named reason, add that failure mode to `judgment/casebook.md` before running a broader sweep.

## Required Review Artifacts

Every still, motion, contact sheet, and video proof review should be recorded in the FluxLab note shape at:

- `/Users/mike/FluxLab_CascadeEffects/proofs/suites/_proof_review_template.md`

Required fields:

- `review_type`
- `gate_level`
- `episode_id`
- `case_id`
- `archetype`
- `source_asset`
- `artifact_path`
- `motion_carrier`
- `contact_sheet_path`
- `proof_video_path`
- `beat_sheet_path`
- `source_baked_issue`
- `disposition`
- `failure_reason`
- `next_action`

## Registry and Casebook Discipline

- Add every current keeper to `judgment/keeper_registry.md`.
- Add every reusable success or failure lesson to `judgment/casebook.md`.
- Do not promote an asset without both a dispositioned review note and a registry decision.
