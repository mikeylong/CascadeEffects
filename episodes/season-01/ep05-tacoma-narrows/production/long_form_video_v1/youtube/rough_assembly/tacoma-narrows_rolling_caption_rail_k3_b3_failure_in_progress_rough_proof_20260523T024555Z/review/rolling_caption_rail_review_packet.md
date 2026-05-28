# Tacoma Narrows Rolling Caption Rail Rough Proof

## Review Target

- Episode ID: `tacoma-narrows`
- Player: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma-narrows_rolling_caption_rail_k3_b3_failure_in_progress_rough_proof_20260523T024555Z/player.html`
- Manifest: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma-narrows_rolling_caption_rail_k3_b3_failure_in_progress_rough_proof_20260523T024555Z/rough_assembly_manifest.json`
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
- Status: `rough_assembly_review_ready_pending_human_keep_candidate_k3_b3_failure_in_progress`
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

## B3 Failure-In-Progress Cable Repair

This successor replaces the rejected/tighten K3 repair lineage with `candidate_k3_b3_failure_in_progress_snapped_suspenders_source_art_keep` because the user-boxed right-hand far-span elements on Option B / K3 original read as unattached cable geometry. B3 keeps the main suspension cables continuous and reframes the suspect elements as snapped/slack suspenders or failed deck-edge hanger attachments.

- New source art: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma-narrows_rolling_caption_rail_k3_b3_failure_in_progress_rough_proof_20260523T024555Z/assets/source_art/candidate_k3_b3_failure_in_progress_snapped_suspenders_1920x1080.png`
- Source-art package: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/source_art/tacoma_living_cover_candidate_k3_b3_failure_in_progress_snapped_suspenders_20260523T020003Z`
- B3 browser QA: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma-narrows_rolling_caption_rail_k3_b3_failure_in_progress_rough_proof_20260523T024555Z/qa/b3_promoted_rough_proof_browser_qa.json`
- Required read: `suspension_cable_geometry_read = pass_human_source_art_keep_b3_failure_in_progress_snapped_suspenders`
- Browser runtime QA: `pass_b3_promoted_rough_proof_browser_runtime_qa`
- Downstream gates remain blocked until human rough-proof keep.
