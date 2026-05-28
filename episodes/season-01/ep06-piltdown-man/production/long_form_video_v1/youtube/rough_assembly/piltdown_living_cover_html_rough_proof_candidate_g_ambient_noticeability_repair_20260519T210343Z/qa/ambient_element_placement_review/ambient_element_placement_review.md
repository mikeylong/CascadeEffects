# Piltdown Ambient Element Placement Review

Status: `diagnostic_review_only_not_gate_advancing`

This review shows where the current repaired ambient elements sit on the Candidate G backplate. It is not loaded by the viewer-facing player and does not add story text, labels, overlays, or diagnostics to the proof itself.

![Ambient placement overlay](/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/production/long_form_video_v1/youtube/rough_assembly/piltdown_living_cover_html_rough_proof_candidate_g_ambient_noticeability_repair_20260519T210343Z/qa/ambient_element_placement_review/ambient_element_placement_backplate_overlay.png)

## Placement Reads

- `lamp_warm_flicker_roi`: broad warm practical-light area around the task lamp.
- `lamp_hotspot_roi`: smaller warm hotspot near the lamp falloff.
- `microscope_stage_glint_roi`: localized microscope-stage and central glass highlight region.
- `dust_motion_envelope`: warm background/bench air where motes are allowed to drift.
- `dust_exclusion_cranium_hand` and `dust_exclusion_jaw`: foreground masks where dust is rejected by the player code.
- `right_rail_story_text_safe_zone`: fixed rail zone where viewer-facing story text remains isolated.
- `source_plate_drift`: whole-backplate subpixel drift, represented by green arrows for diagnostic review only.

## Gate Reads

- `diagnostic_overlay_absence_in_viewer_proof_read`: `pass_overlay_review_artifact_only_not_loaded_by_player`
- `dust_foreground_exclusion_read`: `pass_dust_motes_rejected_inside_two_foreground_masks_in_player_code`
- `right_rail_safe_space_read`: `pass_story_text_zone_identified_and_viewer_text_remains_right_rail_only`
- `modern_screen_glow_read`: `pass_no_screen_tablet_ui_led_or_cool_glow_region_defined`
- `source_art_pointer_read`: `pass_candidate_g_backplate_only`

Downstream locks remain closed: no final MP4, no publish readiness, no YouTube action, and no public release.
