# Therac-25 Living Cover Visual System Baseline

Episode ID: `therac-25`

Baseline status: `rolling_caption_rail_rough_assembly_review_ready_pending_human_keep`

## Active Source Art

- Active source art: `/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/production/longform_v1/youtube/source_art/therac_living_cover_accuracy_cue_repair_imagegen_source_art_20260516T195352Z/assets/source_art/variant_h_control_room_active_terminal_1920x1080.png`
- Active source art SHA-256: `cf08a25f31ea122daf9996827a56b28cc6692cebd83b2bebe5e48fa78cc0365e`
- Source manifest: `/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/production/longform_v1/youtube/source_art/therac_living_cover_accuracy_cue_repair_imagegen_source_art_20260516T195352Z/source_art_manifest.json`
- Source manifest SHA-256: `f75b6619dd4bf83460e6053f0bd11a98e49b6e208e2e6cf26b797fd1e9e53b7f`
- Style lane: `cascade-ink-lit-photoreal-v1`

## Disposition Discrepancy

The source-art plan still records the source-art plan disposition as `defer`, but the publish-readiness actual-outro-prelap package records human `keep` for the active visual package. Future work must cite this discrepancy instead of treating the older `defer` field as a visual rejection.

Publish-readiness package:

- `/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/production/longform_v1/youtube/publish_readiness/therac25_publish_readiness_actual_outro_prelap_20260518T182800Z/publish_readiness_manifest.json`

## Canonical Read

The active Therac-25 Living Cover backplate is Variant H: a period control-room scene with an active monochrome terminal, operator/patient workflow, and quiet clinical tension. The terminal must not be black, blank, modern, readable, or spectacular. The screen can show period monochrome fields, block rows, cursor structure, scanline glow, and non-readable interface texture only.

Required source-art reads:

- `operator_gender_script_alignment_read: pass`
- `active_period_terminal_fields_read: pass`
- `screen_not_black_read: pass`
- `period_dec_vt100_pdp11_crt_read: pass`
- `screen_text_legibility_read: pass`
- `patient_operator_workflow_read: pass`
- `patient_calm_in_treatment_room_read: pass`
- `right_rail_safe_space_read: pass`
- `video_visual_style_scope_read: pass`
- `paper_architecture_visual_style_read: pass`

Hard blockers:

- gore, injury, suffering, beam spectacle, or visible radiation effect
- readable UI, readable numbers, readable codes, fake logs, labels, or text
- black terminal screen
- modern flat-panel display
- celebrity, identifiable patient, or face-forward close-up
- diagnostic cyan overlays on the source plate

## Ambient And Effects Lane

Ambient behavior should stay restrained: CRT glow, subtle scanline/terminal life, quiet treatment-room separation, and rail-safe darkness. It must support the operator/patient workflow read without turning the scene into horror, action, or UI exposition.

## Rail And End Screen

- Living Cover system: `living_cover_system_v1`
- Rail preset: `fixed_16x9_right_rail_v1`
- End-screen template: `challenger_titleless_end_screen_overlay_on_living_cover_v1`
- Music/outro transition: `subtle_tail_outro_v1`

## Current Blockers

- Record the source-art-plan `defer` vs publish-readiness `keep` discrepancy in future plans until the older plan metadata is backfilled or superseded.
- Public upload, publish, scheduling, and release actions remain outside this baseline codification.

<!-- rolling-caption-rail-redesign:start -->

## Rolling Caption Rail Redesign

- Rollout date: `2026-05-20`
- Rail content model: `rolling_caption_anchor_v1`
- Caption display model: `rolling_rail_caption_window_v1`
- Action: `supersede_publish_final_surfaces_create_successor_rough_proof`
- Successor rough manifest: `/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/production/longform_v1/youtube/rough_assembly/therac-25_rolling_caption_rail_rough_proof_20260523T182309Z/rough_assembly_manifest.json`
- Successor player: `/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/production/longform_v1/youtube/rough_assembly/therac-25_rolling_caption_rail_rough_proof_20260523T182309Z/player.html`
- Active source art: `/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/production/longform_v1/youtube/rough_assembly/therac_living_cover_challenger_music_html_rough_proof_20260517T073904Z/qa/screenshots/rough-proof-challenger-music-music_intro.png`
- Active source art SHA-256: `e8ecf391b899e52f22c698e49c9f727e9725785818350413d132bc59e39c1798`

- Source art rollback: not opened by default; revalidate right-rail safe space only.
- Downstream gates: final assembly, publish readiness, and YouTube action remain blocked until the refreshed rough proof receives human `keep`.


<!-- rolling-caption-rail-redesign:end -->
