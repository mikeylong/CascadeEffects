# Tacoma Narrows Living Cover Visual System Baseline

Episode ID: `tacoma-narrows`

Baseline status: `rolling_caption_rail_rough_assembly_review_ready_pending_human_keep`

## Active Source Art

- Active source art: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/source_art/tacoma_living_cover_candidate_k3_b3_failure_in_progress_snapped_suspenders_20260523T020003Z/assets/source_art/candidate_k3_b3_failure_in_progress_snapped_suspenders_1920x1080.png`
- Active source art SHA-256: `580e69bea2f7d278f2aed000ccf669cfaa45fcbf562238694085809eac4363b8`
- Source manifest: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/source_art/tacoma_living_cover_candidate_k3_b3_failure_in_progress_snapped_suspenders_20260523T020003Z/source_art_manifest.json`
- Source manifest SHA-256: `0df777907a08fd0ab792ad58761c7913c275abca8d5a83cba7b51e573aff93cc`
- Style lane: `cascade-ink-lit-photoreal-v1`

## Canonical Read

The active Tacoma Narrows Living Cover backplate is B3: the Option B / K3 original story plate regenerated as a failure-in-progress source-art successor. Human review kept the B3 source-art direction after the diagnostic assembly review, then kept the K3 B3 highlighted rolling-caption rough proof for final assembly.

The current rough proof preserves the rolling caption rail, audio, music timing, intro/outro timing, and end-screen behavior while swapping in the kept B3 source-art plate and resampling the end-screen palette:

- Kept rough proof: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma-narrows_rolling_caption_rail_k3_b3_highlighted_rough_proof_20260523T050034Z`
- Rough assembly manifest: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma-narrows_rolling_caption_rail_k3_b3_highlighted_rough_proof_20260523T050034Z/rough_assembly_manifest.json`
- Review URL: `http://127.0.0.1:8766/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma-narrows_rolling_caption_rail_k3_b3_highlighted_rough_proof_20260523T050034Z/player.html?v=tacoma-narrows_rolling_caption_rail_20260523050034198Z`

Required source-art reads:

- `historical_accuracy_read: pass`
- `source_reference_alignment_read: pass`
- `public_anchor_geometry_read: pass`
- `bridge_deck_read: pass`
- `wave_torsion_read: pass`
- `original_bridge_anchor_read: pass`
- `period_vehicle_read: pass`
- `anonymous_witness_scale_read: pass`
- `no_recognizable_faces_read: pass`
- `right_rail_safe_space_read: pass`
- `video_visual_style_scope_read: pass`
- `paper_architecture_visual_style_read: pass`

Hard blockers:

- diagnostic overlays, labels, or visible UI on the source plate
- recognizable witnesses or face-forward close-ups
- geometry that loses bridge deck, wave, torsion, or original bridge anchoring
- local paint, rotoscope look, or full source-plate repainting

## Ambient And Effects Lane

The active rough-proof ambient lane is `foreground_glass_rain_image_only_v1`, weather-app glass-rain beads opacity v7. It is an image-only layer masked left of the fixed right rail and captions. It adds soft bead droplets and short runners moving diagonally down the viewer-facing glass, with seeded audio-time parameters and no source-plate geometry changes.

Ambient additions must preserve right-rail and caption exclusion.

## Rail And End Screen

- Living Cover system: `living_cover_system_v1`
- Rail preset: `fixed_16x9_right_rail_v1`
- End-screen template: `challenger_titleless_end_screen_overlay_on_living_cover_v1`
- Caption policy: captions remain out of the glass-rain mask and inside the fixed rail model.

## Current Blockers

- Rough proof human `keep` is recorded.
- Final assembly/full-runtime MP4 render is open; publish readiness, YouTube action, and public release remain blocked.

<!-- rolling-caption-rail-redesign:start -->

## Rolling Caption Rail Redesign

- Rollout date: `2026-05-20`
- Rail content model: `rolling_caption_anchor_v1`
- Caption display model: `rolling_rail_caption_window_v1`
- Action: `refresh_current_rough_review_ready_proof`
- Successor rough manifest: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma-narrows_rolling_caption_rail_k3_b3_highlighted_rough_proof_20260523T182309Z/rough_assembly_manifest.json`
- Successor player: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma-narrows_rolling_caption_rail_k3_b3_highlighted_rough_proof_20260523T182309Z/player.html`
- Active source art: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/source_art/tacoma_living_cover_candidate_k3_b3_failure_in_progress_snapped_suspenders_20260523T020003Z/assets/source_art/candidate_k3_b3_failure_in_progress_snapped_suspenders_1920x1080.png`
- Active source art SHA-256: `580e69bea2f7d278f2aed000ccf669cfaa45fcbf562238694085809eac4363b8`
- Source-art/highlight merge model: `tacoma_k3_b3_backplate_with_lesson_takeaway_highlights_v1`
- Source-art/highlight merge read: `pass_k3_b3_backplate_with_approved_takeaway_highlights`

- Source art rollback: not opened by default; revalidate right-rail safe space only.
- Downstream gates: final assembly, publish readiness, and YouTube action remain blocked until the refreshed rough proof receives human `keep`.


<!-- rolling-caption-rail-redesign:end -->

## 2026-05-22 Suspension-Cable Geometry Repair

Status: `candidate_k4_suspension_cable_repair` is `tighten_story_loss_geometry_reference_only`. It is useful as a structural reference, but it is not the active aesthetic successor and must not advance to final render, publish readiness, upload, or public release.

- Source-art package: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/source_art/tacoma_living_cover_suspension_cable_repair_imagegen_candidate_k4_20260522T224753Z`
- Final plate: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma-narrows_rolling_caption_rail_k4_suspension_cable_repair_20260522T224753Z/assets/source_art/candidate_k4_suspension_cable_repair_1920x1080.png`
- Final plate sha256: `afa4f88d1a5477082e29dbc607f6580199a28b0518f0aae4f9b393c936c89a43`
- Source-art manifest: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/source_art/tacoma_living_cover_suspension_cable_repair_imagegen_candidate_k4_20260522T224753Z/source_art_manifest.json`
- Rough proof: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma-narrows_rolling_caption_rail_k4_suspension_cable_repair_20260522T224753Z`
- Gate policy: do not advance current `candidate_g`, `candidate_k3`, `candidate_k3_b2_boxed_cable_repair`, or `candidate_k4_suspension_cable_repair` backplates to final assembly, publish readiness, upload, or public release.
- Required read added: `suspension_cable_geometry_read: pass_left_and_right_suspenders_attach_to_main_cables_and_deck_edges`

## 2026-05-23 Option B Boxed Cable Repair

Status: `candidate_k3_b2_boxed_cable_repair` is `tighten_superseded_by_candidate_k3_b3_failure_in_progress_snapped_suspenders`. User selected `candidate_k3_roadway_wide_stance_1920x1080` as Option B / K3 original, unflipped. The repair target remains the right-hand side far-span/tower suspension-cable geometry inside the user-drawn magenta box.

- Source-art review package: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/source_art/tacoma_living_cover_candidate_k3_b2_boxed_cable_repair_20260523T001446Z`
- Candidate plate: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/source_art/tacoma_living_cover_candidate_k3_b2_boxed_cable_repair_20260523T001446Z/assets/source_art/candidate_k3_b2_boxed_cable_repair_1920x1080.png`
- Source-art manifest: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/source_art/tacoma_living_cover_candidate_k3_b2_boxed_cable_repair_20260523T001446Z/source_art_manifest.json`
- Target/contact sheet: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/source_art/tacoma_living_cover_candidate_k3_b2_boxed_cable_repair_20260523T001446Z/qa/candidate_k3_b2_boxed_cable_repair_contact_sheet.png`
- Gate policy: no rough proof rebuild, final render, publish readiness, upload, or public release from this source-art candidate.
- Wrong-target disposition: prior `candidate_k3_g2_right_cable_microrepair` is `reject_wrong_target_do_not_advance`.
- Required source review reads: `visual_story_continuity_read`, `deck_torsion_story_read`, `human_witness_bracing_read`, `weather_and_roadway_mood_read`, `suspension_cable_geometry_read`, and `pixel_diff_nonmask_read`.

## 2026-05-23 B3 Failure-In-Progress Snapped Suspenders

Status: `candidate_k3_b3_failure_in_progress_snapped_suspenders` is the kept source-art successor and the current promoted rough-proof backplate. It uses Option B / K3 original, unflipped as the source of truth and treats the target-region problem as a failure-in-progress moment: suspicious unattached-looking elements become snapped/slack suspenders or failed deck-edge hanger attachments. The main suspension cables must remain continuous.

- Source-art review package: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/source_art/tacoma_living_cover_candidate_k3_b3_failure_in_progress_snapped_suspenders_20260523T020003Z`
- Primary raw full-frame review candidate: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/source_art/tacoma_living_cover_candidate_k3_b3_failure_in_progress_snapped_suspenders_20260523T020003Z/assets/source_art/candidate_k3_b3_failure_in_progress_snapped_suspenders_1920x1080.png`
- Box-limited composite attempt: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/source_art/tacoma_living_cover_candidate_k3_b3_failure_in_progress_snapped_suspenders_20260523T020003Z/assets/source_art/candidate_k3_b3_failure_in_progress_snapped_suspenders_box_composite_1920x1080.png`
- Source-art manifest: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/source_art/tacoma_living_cover_candidate_k3_b3_failure_in_progress_snapped_suspenders_20260523T020003Z/source_art_manifest.json`
- Full-frame contact sheet: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/source_art/tacoma_living_cover_candidate_k3_b3_failure_in_progress_snapped_suspenders_20260523T020003Z/qa/candidate_k3_b3_failure_in_progress_full_frame_contact_sheet.png`
- Boxed-region contact sheet: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/source_art/tacoma_living_cover_candidate_k3_b3_failure_in_progress_snapped_suspenders_20260523T020003Z/qa/candidate_k3_b3_failure_in_progress_boxed_region_contact_sheet.png`
- Source of truth: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma_living_cover_html_rough_proof_candidate_k3_tail_lights_removed_20260520T054440Z/assets/source_art/candidate_k3_roadway_wide_stance_1920x1080.png`
- Source SHA-256: `8f85d657d6a2573ddeaf637e468d4a8b2db4a20b2017b369591579f086e6246c`
- Target bbox: `[1028, 160, 1391, 916]`
- Required source review reads: `failure_in_progress_story_read`, `main_cable_continuity_read`, `snapped_suspender_read`, `deck_edge_attachment_failure_read`, `no_main_cable_sever_read`, `visual_story_continuity_read`, `deck_torsion_story_read`, `human_witness_bracing_read`, `weather_and_roadway_mood_read`, `historical_plausibility_read`, `suspension_cable_geometry_read`, `texture_noise_read`, and `pixel_diff_nonmask_read`.
- Composite policy: the raw full-frame ImageGen candidate and the box-limited composite attempt are both review artifacts. The composite may advance only after human alignment keep; otherwise it remains diagnostic evidence.
- Gate policy: source-art keep is recorded. This diagnostic source-art section is superseded by the K3 B3 highlighted rolling-caption rough keep; publish readiness, upload, and public release remain blocked.

### Diagnostic Assembly Preview

Status: `diagnostic_assembly_preview_pending_human_source_art_keep_not_rough_proof_keep`. This preview swaps the B3 raw source-art candidate into the existing K4 rolling-caption assembly shell for in-context review only. It is not a promoted rough proof and does not open final render, publish readiness, upload, or public release gates.

- Diagnostic assembly package: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma-narrows_rolling_caption_rail_k3_b3_failure_in_progress_diagnostic_20260523T022349Z`
- Player URL: `http://127.0.0.1:8766/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma-narrows_rolling_caption_rail_k3_b3_failure_in_progress_diagnostic_20260523T022349Z/player.html?v=tacoma-narrows_rolling_caption_rail_k3_b3_diagnostic_20260523022349Z`
- Diagnostic assembly manifest: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma-narrows_rolling_caption_rail_k3_b3_failure_in_progress_diagnostic_20260523T022349Z/rough_assembly_manifest.json`
- Opening-frame screenshot: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma-narrows_rolling_caption_rail_k3_b3_failure_in_progress_diagnostic_20260523T022349Z/qa/screenshots/b3_diagnostic_assembly_opening_frame.png`
- Diagnostic browser QA: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma-narrows_rolling_caption_rail_k3_b3_failure_in_progress_diagnostic_20260523T022349Z/qa/diagnostic_assembly_browser_qa.json`
- Source-art load read: `pass_b3_source_plate_loaded_1920x1080`
- Promotion read: `blocked_diagnostic_assembly_only`

### Promoted Rough Proof

Status: `superseded_by_k3_b3_highlighted_rough_keep`. The B3 source-art keep was applied to this rolling-caption rough proof, then superseded by the highlighted successor that received human keep.

- Promoted rough proof package: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma-narrows_rolling_caption_rail_k3_b3_failure_in_progress_rough_proof_20260523T024555Z`
- Player URL: `http://127.0.0.1:8766/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma-narrows_rolling_caption_rail_k3_b3_failure_in_progress_rough_proof_20260523T024555Z/player.html?v=tacoma-narrows_rolling_caption_rail_k3_b3_rough_proof_20260523024555Z`
- Rough assembly manifest: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma-narrows_rolling_caption_rail_k3_b3_failure_in_progress_rough_proof_20260523T024555Z/rough_assembly_manifest.json`
- B3 runtime browser QA: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma-narrows_rolling_caption_rail_k3_b3_failure_in_progress_rough_proof_20260523T024555Z/qa/b3_promoted_rough_proof_browser_qa.json`
- B3 runtime browser QA read: `pass_b3_promoted_rough_proof_browser_runtime_qa`
- Static QA: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma-narrows_rolling_caption_rail_k3_b3_failure_in_progress_rough_proof_20260523T024555Z/qa/b3_rough_proof_static_qa.json`
- Legacy donor browser QA: non-gating; superseded by `b3_promoted_rough_proof_browser_qa_v1`.
- Gate policy: superseded by the highlighted rough proof keep; final assembly/full-runtime MP4 render is now open from the successor, while publish readiness, YouTube action, and public release remain blocked.


## Tacoma K3 B3 Highlighted Rough Keep

- Recorded UTC: `2026-05-23T05:17:55.117Z`
- Disposition: `keep`
- Kept proof: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma-narrows_rolling_caption_rail_k3_b3_highlighted_rough_proof_20260523T050034Z`
- Keep receipt: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma-narrows_rolling_caption_rail_k3_b3_highlighted_rough_proof_20260523T050034Z/review/human_rough_assembly_keep_rolling_caption_rail_k3_b3_highlighted_202605230517551Z.json`
- Gate effect: final assembly/full-runtime MP4 render may proceed; publish readiness and YouTube action remain blocked.
