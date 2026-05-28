# Hyatt Living Cover HTML Rough Proof - Right Rail Text Only

Status: `review_ready_blocked_missing_music_contract`
Human disposition: `pending`
Final MP4 render: `locked`

This successor proof repairs the invalid out-of-rail text surfaces from `hyatt_living_cover_html_rough_proof_n5b_20260517T074301Z`. It is the current Hyatt N5B rough-proof review artifact for MP4 eligibility, but final rendering still requires human `keep` plus the required music integration contract or explicit waiver.

## Review Surface

- Localhost URL: `http://127.0.0.1:8844/player.html`
- Player: `/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/rough_assembly/hyatt_living_cover_html_rough_proof_n5b_right_rail_text_only_20260517T081101Z/player.html`
- Manifest: `/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/rough_assembly/hyatt_living_cover_html_rough_proof_n5b_right_rail_text_only_20260517T081101Z/rough_assembly_manifest.json`
- Player SHA-256: `fbe8aa9963a9efbc29133ab1269c86f181dd43389f55f8d1e1d3d2bf9257aa10`
- Browser QA: `/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/rough_assembly/hyatt_living_cover_html_rough_proof_n5b_right_rail_text_only_20260517T081101Z/qa/browser_qa_1920x1080.json`
- Browser QA SHA-256: `607a3006910bf35bda3fc49f14fbdb33b4d7be558bb685ae9d104e3dc95eac5b`

## Source Carrier

![Hyatt N5B source-art carrier](/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/source_art/hyatt_living_cover_variant_n_believable_table_bouquets_20260517T051623Z/assets/source_art/n5b_plausible_table_centerpieces_1920x1080.png)

- Source art: N5B, `n5b_plausible_table_centerpieces`
- Audio: approved long-form WAV
- Captions: script-locked VTT in the lower right rail, ASR timing only
- Canvas: fixed `1920x1080`
- Render API: `window.__setRenderTime(seconds)`

## What Changed

- Removed the left chapter slate.
- Removed the left effect card.
- Removed the bottom-left end-screen label.
- Replaced ordinal `CHAPTER 01` labels with semantic right-rail chapter copy.
- Kept end-screen geometry as textless platform target boxes.

## What To Review

- All viewer-facing text should be inside the right rail.
- The active rail should read as chapter title, active beat title, and one support line.
- Context rows should show nearby chapter titles only.
- Rail captions should remain readable and script-locked.
- End-screen target boxes should hold static geometry without out-of-rail text.

## Browser QA

- QA status: `pass`
- Samples: `8`
- Range server: `pass_206_partial_content`
- Viewer text inventory: `pass`
- Right-rail text boundary: `pass`
- Out-of-rail text: `pass_no_visible_out_of_rail_text`
- Ordinal labels: `pass_no_visible_ordinal_chapter_labels`
- End-screen text boundary: `pass_no_end_screen_text_outside_rail`

## Locked Actions

- No final MP4 render until rough-proof `keep`.
- No rough-proof `keep` until the music integration contract or explicit human waiver is recorded.
- No publish-readiness package.
- No private upload.
- No YouTube visibility action.

Review answer: `rough-proof keep`, `tighten`, or `reject`.
