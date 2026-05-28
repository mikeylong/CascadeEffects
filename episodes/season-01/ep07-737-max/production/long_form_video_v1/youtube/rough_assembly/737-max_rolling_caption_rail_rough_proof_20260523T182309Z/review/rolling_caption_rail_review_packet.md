# 737 MAX Rolling Caption Rail Rough Proof

## Review Target

- Episode ID: `737-max`
- Player: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/youtube/rough_assembly/737-max_rolling_caption_rail_rough_proof_20260523T182309Z/player.html`
- Manifest: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/youtube/rough_assembly/737-max_rolling_caption_rail_rough_proof_20260523T182309Z/rough_assembly_manifest.json`
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
- Highlight color model: `source_sampled_backplate_contrast_takeaway_accent_v3`
- Highlight visual timing model: `active_band_presence_aligned_v1`
- Caption collision guard: `fixed_line_box_visual_gap_guard_v1`


## Gate Handling

- Action: `create_reviewable_right_rail_rough_proof_from_kept_candidate_l_after_music_contract_creation`
- Status: `rolling_caption_rail_rough_assembly_review_ready_pending_human_keep`
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

- same automated system (38.443 to 40.87s): #efef9f; human_approved_lesson_takeaway_span_20260523
- depended on a single sensor (60.854 to 62.858s): #efef9f; human_approved_lesson_takeaway_span_20260523
- pilot cannot clearly see (82.767 to 84.148s): #efef9f; human_approved_lesson_takeaway_span_20260523
- commonality was not incidental (107.83 to 114.44s): #efef9f; human_approved_lesson_takeaway_span_20260523
- changed the aircraft's aerodynamic behavior (177.585 to 184.936s): #efef9f; human_approved_lesson_takeaway_span_20260523
- make it fly like one (216.773 to 221.22s): #efef9f; human_approved_lesson_takeaway_span_20260523
- special pilot awareness (268.861 to 274.049s): #efef9f; human_approved_lesson_takeaway_span_20260523
- single angle-of-attack sensor (295.752 to 298.658s): #efef9f; human_approved_lesson_takeaway_span_20260523
- system was not described (322.002 to 324.004s): #efef9f; human_approved_lesson_takeaway_span_20260523
- familiar aircraft with improved engines (334.476 to 336.479s): #efef9f; human_approved_lesson_takeaway_span_20260523
- system was hidden from pilots not through malice (369.987 to 377.001s): #efef9f; human_approved_lesson_takeaway_span_20260523
- The crew encountered the same system (437.423 to 441.427s): #efef9f; human_approved_lesson_takeaway_span_20260523
- competitive business pressure became a design requirement (470.797 to 477.075s): #efef9f; human_approved_lesson_takeaway_span_20260523
- outcome that threatened the commonality argument (507.314 to 512.281s): #efef9f; human_approved_lesson_takeaway_span_20260523
- system originally designed (521.037 to 522.598s): #efef9f; human_approved_lesson_takeaway_span_20260523
- qualitatively different from what had originally been certified (543.639 to 549.448s): #efef9f; human_approved_lesson_takeaway_span_20260523
- calibrated to the system's origin (561.968 to 567.918s): #efef9f; human_approved_lesson_takeaway_span_20260523
- single point of failure (577.444 to 579.526s): #efef9f; human_approved_lesson_takeaway_span_20260523
- pilots to recognize a failure mode (596.565 to 602.979s): #efef9f; human_approved_lesson_takeaway_span_20260523
- decision not to name or describe MCAS (618.048 to 621.072s): #efef9f; human_approved_lesson_takeaway_span_20260523
- commercial argument and the safety argument (652.059 to 658.509s): #efef9f; human_approved_lesson_takeaway_span_20260523
- architectural question (694.849 to 700.431s): #efef9f; human_approved_lesson_takeaway_span_20260523
- sufficient independent review (765.767 to 768.737s): #efef9f; human_approved_lesson_takeaway_span_20260523
- commercial constraint became a design requirement (830.729 to 833.313s): #efef9f; human_approved_lesson_takeaway_span_20260523
- pilots had been given what they needed (919.259 to 924.489s): #efef9f; human_approved_lesson_takeaway_span_20260523

## Required Response

Reply with exactly one disposition: `keep`, `tighten`, or `reject`.
