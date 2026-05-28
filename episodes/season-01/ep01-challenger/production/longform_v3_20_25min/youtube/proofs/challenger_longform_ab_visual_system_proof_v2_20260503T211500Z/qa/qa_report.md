# Challenger A/B Proof v2 QA Report

Status: `blocked_pending_ink_lit_source_art_keep`

## Audio And Timing

- Source audio duration: `1289.131s`
- Excerpt start/end: `677.275s-807.975s`
- Excerpt duration: `130.700s`
- Both proof players reference the same audio file: `assets/audio/challenger_ab_excerpt.wav`
- Browser audio metadata read: `130.7s`
- Caption track attached: `1`
- Duration exception: exact phrase-bounded passage exceeds requested `90-120s`; shortened audio would violate the approved-timeline boundary. Exception is acknowledged for the A/B proof.

## Direction Decision

- Selected direction: `Living Cover`
- Living Cover human disposition: `keep`
- Living Cover may advance to motion readiness: `false`
- Living Cover source art disposition: `keep`
- Living Cover selected source-art variant: `B`
- Evidence Table human disposition: `defer`
- Evidence Table role: `reference_only_for_later_evidence_diagram_punctuation`
- Rough assembly created or unblocked: `blocked_pending_ink_lit_source_art_keep`

## Visual Carrier

- Evidence Table carrier: `generated_raster_source_art`
- Living Cover carrier: `generated_raster_source_art`
- HTML/CSS/JS role: proof shell, timing, light/camera treatment, deterministic local UI, and compositing over generated source art.
- CSS/SVG/canvas public-anchor or evidence-object drawings: `none`

## Text, Logo, And Contamination

- Generated readable text: `pass`
- Generated logos/watermarks: `pass`
- Archival contamination: `pass`
- OCR check: Tesseract returned noise fragments only; no coherent generated labels, captions, logos, or words.

## Paper Architecture Compliance

- Bright tactile paper material: `pass`
- Public anchor readability: `pass`
- Evidence object readability: `pass` for Evidence Table; `not_primary` for Living Cover by design.
- Sparse composition: `pass` for Living Cover; `tighten` for Evidence Table due density/fatigue risk.
- Deterministic local typography only: `pass`
- Surface texture boundary: `pass`
- Evidence Table texture_noise_read: `pass`
- Living Cover texture_noise_read: `pass`
- Texture rule applied: subtle paper fiber only, clean low-detail paper planes, no speckle/noise/grain/grit/sandy texture.
- Block rule: `texture_noise_read: tighten|reject` prevents `keep`, motion readiness, rough assembly, thumbnails, and package assets.

## Screenshots

- A/B index desktop: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/proofs/challenger_longform_ab_visual_system_proof_v2_20260503T211500Z/qa/screenshots/ab_index_desktop.png`
- Evidence Table desktop: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/proofs/challenger_longform_ab_visual_system_proof_v2_20260503T211500Z/qa/screenshots/evidence_table_desktop_full.png`
- Evidence Table frame: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/proofs/challenger_longform_ab_visual_system_proof_v2_20260503T211500Z/qa/screenshots/evidence_table_frame_desktop.png`
- Evidence Table preview: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/proofs/challenger_longform_ab_visual_system_proof_v2_20260503T211500Z/qa/screenshots/evidence_table_youtube_preview_320x180.png`
- Evidence Table mini preview: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/proofs/challenger_longform_ab_visual_system_proof_v2_20260503T211500Z/qa/screenshots/evidence_table_youtube_preview_168x94.png`
- Living Cover desktop: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/proofs/challenger_longform_ab_visual_system_proof_v2_20260503T211500Z/qa/screenshots/living_cover_desktop_full.png`
- Living Cover frame: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/proofs/challenger_longform_ab_visual_system_proof_v2_20260503T211500Z/qa/screenshots/living_cover_frame_desktop.png`
- Living Cover preview: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/proofs/challenger_longform_ab_visual_system_proof_v2_20260503T211500Z/qa/screenshots/living_cover_youtube_preview_320x180.png`
- Living Cover mini preview: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/proofs/challenger_longform_ab_visual_system_proof_v2_20260503T211500Z/qa/screenshots/living_cover_youtube_preview_168x94.png`

## Rejection Checks

- Static-thumbnail video: `pass`
- Waveform video: `pass`
- Full-runtime loop: `pass`
- Motion-readiness input: `blocked_pending_ink_lit_source_art_keep`
- Rough assembly input: `blocked_pending_ink_lit_source_art_keep`

## Source-Art Repair

- Repair packet: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/source_art_repair/living_cover_texture_repair_20260504T043512Z`
- Repair status: `blocked_stale_daylight_profile_reference_only`
- Selected variant: `B`
- Selected variant texture_noise_read: `pass`
- Selected variant visual_profile_read: `tighten_stale_daylight_profile`
- Ink-lit repair packet: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/source_art_repair/living_cover_ink_lit_repair_20260504T061353Z`
