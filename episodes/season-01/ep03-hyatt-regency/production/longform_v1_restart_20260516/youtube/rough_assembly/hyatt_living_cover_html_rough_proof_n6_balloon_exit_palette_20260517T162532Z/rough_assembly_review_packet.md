# Hyatt Living Cover HTML Rough Proof - N6 Balloon Exit Palette

Status: `review_ready_pending_human_n6_source_art_and_balloon_exit_palette_keep`
Human disposition: `pending`
Final MP4 render: `locked`

This successor keeps the N6 source art, Challenger-style music proof, shifted captions, right-rail-only text, camera flashes, and downstream locks. It repairs the loose-balloon behavior and color palette.

## Review Surface

- Localhost URL: `http://127.0.0.1:8844/player.html`
- Player: `/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/rough_assembly/hyatt_living_cover_html_rough_proof_n6_balloon_exit_palette_20260517T162532Z/player.html`
- Manifest: `/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/rough_assembly/hyatt_living_cover_html_rough_proof_n6_balloon_exit_palette_20260517T162532Z/rough_assembly_manifest.json`
- Ambient layer: `/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/rough_assembly/hyatt_living_cover_html_rough_proof_n6_balloon_exit_palette_20260517T162532Z/living_cover_ambient_effects_layer.json`

## What Changed

- Loose balloons keep rising until they leave the top of frame.
- Balloon opacity is constant during flight; they no longer fade out as the exit mechanism.
- Balloon colors are restricted to muted colors sampled from the N6 table-bouquet decor: champagne gold, dusty lavender, tea rose, peach coral, ivory tan, and muted plum.
- Camera flashes, music timing, rail captions, and right-rail text behavior are unchanged.

## Browser QA

- Status: `pass`
- QA report: `/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/rough_assembly/hyatt_living_cover_html_rough_proof_n6_balloon_exit_palette_20260517T162532Z/qa/browser_qa_1920x1080.json`
- Screenshots: `16`
- Range request: `206 Partial Content`
- Active balloon samples: `13`
- Balloon exit samples: `6`
- Palette-matched balloon samples: `13`
- Constant-alpha no-fade samples: `13`

QA reads passed for right-rail-only text, no ordinal labels, no captions before voice start, visible camera flash, visible balloon rises, off-frame balloon exit, no balloon fade-out, palette match, source-safe effect integration, and byte-range scrubbing.

## Locked Actions

- No final MP4 render until explicit N6 source-art keep and this rough-proof keep.
- No publish-readiness package.
- No private upload.
- No YouTube visibility action.
