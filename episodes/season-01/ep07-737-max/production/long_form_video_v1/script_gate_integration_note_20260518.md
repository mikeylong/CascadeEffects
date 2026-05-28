# 737 MAX Script Gate Integration Note

Date: 2026-05-18

Workflow: `long_form_video_production_v1`

Gate: `critique_integration`

Disposition: `pass_required_change_integrated_human_audio_approval_pending`

## Integration Summary

Claude returned `pass_with_tightening`. No factual rewrite was required. The required pre-render changes were handled as follows:

- Bracketed performance tags are removed from the generated ElevenLabs `input` fields and carried only as chunk `instructions` in `final_jobs.jsonl`.
- Pronunciation handling was added to the local ElevenLabs risk lexicon for `MCAS`, `CFM LEAP`, `A320neo`, and `FAA`; place-name review markers were added for `Addis Ababa`, `Jakarta`, and `Java Sea`.
- The closing line was restored to the canonical Cascade Effects long-form closer after human correction against Challenger, Therac-25, and Hyatt Regency precedent.

## Canonical Closer Precedent

- Challenger source script: `[calm] Next time: another design failure. Another system that taught itself to ignore what it already knew.`
- Therac-25 source script: `[calm] Next time: another design failure. Another system that taught itself to ignore what it already knew.`
- Hyatt Regency source script: `[deliberate] Next time: another design failure. Another system that taught itself to ignore what it already knew.`

## Critique Artifact

- Prompt path: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/prompts/737_max_frontier_script_critique_prompt_20260518T220546Z.md`
- Prompt SHA-256: `e7fe24627897cb10a6e86890e27919344af3a0fd665879a7f2b887b7d1db746f`
- Critique path: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/frontier_model_script_critique_claude_20260518.md`
- Critique SHA-256: `92de6a5bc25e56a7ad858a883dad396f957726c81917b5b4bf6b7d97746ec040`
- Critic model/tool: `Claude CLI, model alias opus`
- Reviewed script SHA-256: `3f95aaf72b3144f0c33ee85e77d18140a888ba97c46eb89b0cfaad5c61a7c718`
- Critique result: `pass_with_tightening`

## Script Change

Removed interim repair:

`[calm] Next time: another cascade.`

Restored canonical closer:

`[calm] Next time: another design failure. Another system that taught itself to ignore what it already knew.`

This restores the reviewed canonical closer and introduces no new factual claim.

## Pronunciation Preflight Basis

- Lexicon path: `/Users/mike/Audio_CascadeEffects/references/pronunciation/known_risks_v1.json`
- Lexicon SHA-256 after 737 additions: `3bbd0ab315d1afc8913f5684c728b89096536c921459d96edbb100311b61f861`
- Required aliases: `mcas_em_cass`, `cfm_leap_letters`, `a320neo_spoken`, `faa_letters`
- Review markers: `addis_ababa_review`, `jakarta_review`, `java_sea_review`

## TTS Manifest Prepared

- Final jobs path: `/Users/mike/Audio_CascadeEffects/tmp/ep7_737max_production/final_jobs.jsonl`
- Final jobs SHA-256: `b8ccd39b6a814097c6efaa89c3679e233437fe0f65384ee082662642f5395458`
- Chunk count: `5`
- Chunk 01: `737_max_longform_01.wav`, 2935 chars
- Chunk 02: `737_max_longform_02.wav`, 2799 chars
- Chunk 03: `737_max_longform_03.wav`, 2896 chars
- Chunk 04: `737_max_longform_04.wav`, 2801 chars
- Chunk 05: `737_max_longform_05.wav`, 1990 chars

## Post-Integration Script

- Script path: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/Ep7_737-MAX.txt`
- Post-integration SHA-256: `3f95aaf72b3144f0c33ee85e77d18140a888ba97c46eb89b0cfaad5c61a7c718`
- Post-integration word count: `2166`
- Runtime target: `12-15 minutes`

## Optional Tightening Deferred

Claude suggested a few cadence polish changes. They are deferred because they are not factual or render blockers, and the plan targets the compact locked script with only required pre-render repairs plus the restored series closer.

## Gate Reads

- `frontier_model_script_critique_read`: `pass_with_tightening`
- `critique_integration_read`: `pass_required_change_integrated`
- `pronunciation_preflight_plan_read`: `pass_aliases_and_review_markers_added`
- `performance_tag_strip_read`: `pass_manifest_inputs_strip_tags`
- `canonical_closer_read`: `pass_restored_from_challenger_therac_hyatt_precedent`
- `stale_next_episode_promise_read`: `pass_human_series_signature_override`
- `new_claim_fact_check_read`: `pass_no_new_factual_claims`
- `post_integration_script_hash_read`: `pass`
- `human_script_approval_for_audio_read`: `missing`
- `may_render_audio`: `false_pending_human_script_approval`

## Next Gate

Mike must explicitly approve the post-integration script for long-form audio render. Until then, TTS render, audio promotion, visual-system planning, rough assembly, upload, and public release remain blocked.
