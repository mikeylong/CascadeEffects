# Tacoma Narrows Rolling Caption Rail Rough Proof

## Review Target

- Episode ID: `tacoma-narrows`
- Player: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma-narrows_rolling_caption_rail_rough_proof_20260520T235500Z/player.html`
- Manifest: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma-narrows_rolling_caption_rail_rough_proof_20260520T235500Z/rough_assembly_manifest.json`
- Rail preset: `fixed_16x9_right_rail_v1`
- Rail content model: `rolling_caption_anchor_v1`
- Caption display model: `rolling_rail_caption_window_v1`
- Caption window role: `middle_two_thirds_right_rail`
- Caption blur scope: `none`
- Caption highlight source: `living_cover_cue_map_key_phrases`
- Caption palette source: `sampled_episode_backplate`
- Caption display chunking: `script_locked_chunk_split_v1`
- Review chrome policy: `hidden_in_render_mode`
- Highlight render policy: `reviewed_cue_map_spans_only`
- Caption motion model: `constant_speed_audio_time_aligned_scroll_v2`
- Caption timeline layout: `audio_time_positioned_stack_v1`
- Caption sync target: `pre_vo_reading_lead_active_band_v1`
- Caption reading lead: `0.65s`
- Caption speed scope: `per_episode_constant_px_per_second`
- Caption window treatment: `transparent_caption_mask_only_v1`
- Caption opacity model: `viewport_distance_smoothstep_v1`
- Highlight phrase scope: `exact_authored_span_only`
- Caption highlight model: `lesson_takeaway_highlight_v1`
- Highlight semantic role: `story_lesson_takeaway`
- Highlight density model: `memorable_takeaway_cadence_v1`
- Highlight color model: `source_sampled_high_contrast_warm_accent_v1`
- Highlight visual timing model: `active_band_presence_aligned_v1`
- Caption collision guard: `fixed_line_box_visual_gap_guard_v1`

## Gate Handling

- Action: `refresh_current_rough_review_ready_proof`
- Status: `rolling_caption_rail_tightened_production_integration_pending_reviewed_key_phrase_spans`
- Source art rollback: not opened by default because the rail footprint is unchanged.
- Downstream gates: final assembly, publish readiness, and YouTube action remain blocked until this refreshed rough proof receives human `keep`.


## Human Review Focus

- Captions roll smoothly through the middle two-thirds of the right rail with no seek jumps or layout jitter.
- The proof is injected into the predecessor rough proof shell so the kept source art, ambient behavior, audio timing, and end-screen timing remain active.
- The caption window has no blur, fill, panel, or container background; readability relies on source-aware text color, text shadow, and the entry/exit mask.
- Old previous/upcoming context rows are absent.
- Highlights render only from cue-map spans that are authored as story lesson/takeaway phrases, not technical labels or isolated single words.
- At the end-screen transition, captions continue upward and caption text/highlights fade fully out before YouTube target geometry.
- Right-rail safe space remains valid against the kept backplate.

## Key Phrase Spans

- No reviewed cue-map key phrase spans were found. Highlight rendering is suppressed until authored reviewed spans exist.

## Required Response

Reply with exactly one disposition: `keep`, `tighten`, or `reject`.

## K4 Suspension-Cable Geometry Repair

This successor replaces the Candidate G/K3 backplate lineage with `candidate_k3_b3_failure_in_progress_snapped_suspenders_diagnostic_assembly` because the prior left-side suspenders read as detached foreground bars. Review the full frame and left-cable crop before any rough-proof keep.

- New source art: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma-narrows_rolling_caption_rail_k3_b3_failure_in_progress_diagnostic_20260523T022349Z/assets/source_art/candidate_k3_b3_failure_in_progress_snapped_suspenders_1920x1080.png`
- Source-art package: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/source_art/tacoma_living_cover_suspension_cable_repair_imagegen_candidate_k4_20260522T224753Z`
- Left cable crop: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/source_art/tacoma_living_cover_suspension_cable_repair_imagegen_candidate_k4_20260522T224753Z/qa/candidate_k3_b3_failure_in_progress_snapped_suspenders_diagnostic_assembly_left_cable_crop.png`
- Required read: `suspension_cable_geometry_read = review_required_b3_failure_in_progress_snapped_suspenders_pending_human_source_art_keep`
- Downstream gates remain blocked until human rough-proof keep.
