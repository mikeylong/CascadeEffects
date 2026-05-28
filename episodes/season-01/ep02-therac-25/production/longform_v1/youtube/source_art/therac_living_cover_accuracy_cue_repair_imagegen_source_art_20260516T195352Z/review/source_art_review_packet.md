# Therac-25 Living Cover Source-Art Review Packet

- Packet: `therac_living_cover_accuracy_cue_repair_imagegen_source_art_20260516T195352Z`
- Gate: `source_art_gate`
- Status: `review_ready`
- Human disposition: `defer`
- Source-art lane: `cascade-ink-lit-photoreal-v1`
- Generation tool: `codex_builtin_image_gen`
- Local rendered backplate: `pass_not_used`

## Review Target

This packet repairs the active Therac photoreal backplate direction. The operator is female-presenting or script-neutral, the operator terminal is active instead of black, and generated screen content remains non-readable.

Selected candidate: `variant_h_control_room_active_terminal`

`/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/production/longform_v1/youtube/source_art/therac_living_cover_accuracy_cue_repair_imagegen_source_art_20260516T195352Z/assets/source_art/variant_h_control_room_active_terminal_1920x1080.png`

Reason: best balance of active period terminal, female-presenting operator, shielded treatment-room workflow, patient/machine visibility, and clean dark right-rail space.

## Candidates

- G: active terminal tableau, strongest console read.
- H: control-room-through-glass, selected for revised proof.
- I: machine/patient-forward frame with active console glow.

## Required Reads

- `operator_gender_script_alignment_read`: `pass`
- `operator_screen_historical_accuracy_read`: `pass_active_period_terminal_status_fields`
- `screen_not_black_read`: `pass`
- `period_terminal_read`: `pass_dec_vt100_pdp11_style_crt`
- `screen_text_legibility_read`: `pass_no_readable_text_numbers_or_codes`
- `patient_monitor_read`: `pass_terminal_or_monitor_glow_present`
- `right_rail_safe_space_read`: `pass_selected_variant_h_strong_dark_right_side`

## Locked Scope

This is source-art review only. No final MP4, publish-readiness package, upload, public release, or visibility action is authorized unless a later human review explicitly approves it.

## Required Response

Reply with exactly one disposition: `keep`, `tighten`, or `reject`.
