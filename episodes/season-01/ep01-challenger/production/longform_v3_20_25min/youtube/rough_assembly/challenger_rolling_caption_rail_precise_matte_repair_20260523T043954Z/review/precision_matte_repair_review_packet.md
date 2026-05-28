# Challenger Candidate B Precision Matte Repair

- Proof ID: `challenger_rolling_caption_rail_precise_matte_repair_20260523T043954Z`
- Player: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/challenger_rolling_caption_rail_precise_matte_repair_20260523T043954Z/player.html`
- Mask: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/challenger_rolling_caption_rail_precise_matte_repair_20260523T043954Z/assets/masks/foreground_occlusion_matte.png`
- QA: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/challenger_rolling_caption_rail_precise_matte_repair_20260523T043954Z/qa/matte/candidate_b_precision_matte_qa.json`
- Contact sheet: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/challenger_rolling_caption_rail_precise_matte_repair_20260523T043954Z/qa/matte/candidate_b_precision_matte_contact_sheet.png`

## Disposition

Pending human review. Final assembly, publish readiness, and YouTube actions remain blocked until this repair receives `keep`.

## Repair Read

- Preserves current right-rail/practical-light intent: `tower_shuttle_only_no_light_or_right_rail_mask`.
- Replaces broad silhouettes with source-pixel tower/shuttle occlusion and a 2px edge guard.
- Relies on the player matte clip for aircraft/fog glow rather than expanding the matte.
- Route QA requires zero source-core visible leak samples.

## QA Reads

- `tower_shuttle_precision_matte_read`: `pass`
- `no_light_or_right_rail_mask_read`: `pass`
- `open_air_and_ground_allowed_read`: `pass`
- `aircraft_shuttle_silhouette_leak_read`: `pass`
- `aircraft_pixel_clip_matte_read`: `pass`
- `matte_tightness_read`: `pass`

