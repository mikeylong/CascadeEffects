# Piltdown Man Long-Form Inventory Gate

Date: 2026-05-18

Workflow: `long_form_video_production_v1`

Gate: `inventory`

Disposition: `keep_opened_for_package_audio_gate`

## Inventory Summary

Piltdown Man is entering compact long-form production as a 12-15 minute watchable audio essay. The Short is already in private/manual pre-release review and may later serve as a bridge asset, but it is not the long-form source of truth.

The current long-form source has a locked fact-checked script and no long-form audio master. The next required work is the script/audio authorization path: frontier-model critique, integration, explicit human approval for audio, then long-form audio render and timing provenance.

## Source Reads

- Script path: `/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/Ep6_Piltdown-Man.txt`
- Original script SHA-256 before this gate: `cfbc86ee950be091bc303e25d26a66044fda8417dd0bdab71c59293ed4bc31e6`
- Post-integration script SHA-256: `b9993d242adcef5352b372f9e3168749c6b513024ca0f566ea6b488ac35c5b5c`
- Post-integration script word count: `1982`
- Fact-check report: `/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/fact_check.md`
- Fact-check SHA-256: `0ccd013ac21bdd95f2e3a6bd074966199a343e4af4c379431140d9dd9da128d1`
- Configured long-form audio target: `/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/final/Ep6_Piltdown-Man.wav`
- Long-form audio master status: `missing`
- Long-form timing source status: `missing`

## Series-Bible Alignment

- Episode order: `06`
- Lane: `Mystery That Has Receipts`
- Season role: `first full receipts mystery`
- Mechanism: `authority protects the flattering lie`
- Causal hook: `a hoax survived because it confirmed what respected institutions wanted to believe`
- Evidence package direction for later visual work: artifact cards, excavation sketches, specimen overlays, and timeline of doubts

## Existing Short Bridge

- Short id: `piltdown_man_short_scoped_v1`
- Short state: `private review upload processed; manual Studio checks pending`
- Private video id: `Q6vhGyqH3EQ`
- Private review URL: `https://www.youtube.com/watch?v=Q6vhGyqH3EQ`
- Bridge read: `available_private_review_manual_phase`
- Production-source read: `short_assets_not_long_form_source_of_truth`

## Gate Reads

- `long_form_script_read`: `pass_locked_script_present_post_integration`
- `fact_check_read`: `pass_fact_check_present`
- `runtime_target_read`: `pass_compact_12_15_minute_target`
- `series_bible_alignment_read`: `pass_episode_06_first_full_receipts_mystery`
- `frontier_model_script_critique_read`: `pass_with_tightening`
- `critique_integration_read`: `pass_required_change_integrated`
- `human_script_approval_for_audio_read`: `missing`
- `audio_source_integrity_read`: `missing`
- `long_form_audio_master_read`: `missing`
- `caption_timing_source_read`: `missing`
- `existing_short_bridge_read`: `pass_available_private_review_manual_phase`
- `visual_system_plan_read`: `blocked_pending_audio_gate`
- `rough_assembly_read`: `blocked_pending_audio_gate`
- `publish_readiness_read`: `blocked_no_final_assembly`

## Next Gate

Capture explicit human approval for audio from the post-integration script. Only after that may the long-form audio render and timing provenance be created.

`may_advance_to_visual_system`: `false`

`may_start_rough_assembly`: `false`

`may_render_final_mp4`: `false`

`may_youtube_action`: `false`

`public_release_ready`: `false`
