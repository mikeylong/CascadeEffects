# Tacoma Narrows Rolling Caption Rail Rough Proof

## Review Target

- Episode ID: `tacoma-narrows`
- Player: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma-narrows_rolling_caption_rail_k3_b3_highlighted_rough_proof_20260523T182309Z/player.html`
- Manifest: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma-narrows_rolling_caption_rail_k3_b3_highlighted_rough_proof_20260523T182309Z/rough_assembly_manifest.json`
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
- Source-art/highlight merge model: `tacoma_k3_b3_backplate_with_lesson_takeaway_highlights_v1`
- Source-art merge predecessor proof: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma-narrows_rolling_caption_rail_k3_b3_failure_in_progress_rough_proof_20260523T024555Z`


## Gate Handling

- Action: `refresh_current_rough_review_ready_proof`
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

- motion changed the air around it (37.279 to 42.149s): #efef9f; human_approved_lesson_takeaway_span_20260523
- feedback cycle the design had never been tested against (81.455 to 85.62s): #efef9f; human_approved_lesson_takeaway_span_20260523
- outside the design process (104.334 to 107.18s): #efef9f; human_approved_lesson_takeaway_span_20260523
- not the one that got built (127.441 to 132.606s): #efef9f; human_approved_lesson_takeaway_span_20260523
- lightness and grace looked like the future (196.505 to 201.472s): #efef9f; human_approved_lesson_takeaway_span_20260523
- made the motion easier to categorize (264.879 to 267.002s): #efef9f; human_approved_lesson_takeaway_span_20260523
- Visible anomaly had been normalized (272.57 to 276.274s): #efef9f; human_approved_lesson_takeaway_span_20260523
- design framework of the time (304.674 to 308.56s): #efef9f; human_approved_lesson_takeaway_span_20260523
- advanced engineering within the limits (360.654 to 365.324s): #efef9f; human_approved_lesson_takeaway_span_20260523
- wind mainly as a static load (366.366 to 373.68s): #efef9f; human_approved_lesson_takeaway_span_20260523
- not as something that changed (397.208 to 402.659s): #efef9f; human_approved_lesson_takeaway_span_20260523
- helping create the conditions (420.004 to 421.846s): #efef9f; human_approved_lesson_takeaway_span_20260523
- discount the warning (462.835 to 466.14s): #efef9f; human_approved_lesson_takeaway_span_20260523
- lessons were learned after the bridge fell (512.483 to 514.566s): #efef9f; human_approved_lesson_takeaway_span_20260523
- wind did not need to become a hurricane (549.523 to 553.715s): #efef9f; human_approved_lesson_takeaway_span_20260523
- bridge did not merely fail in the wind (592.714 to 599.206s): #efef9f; human_approved_lesson_takeaway_span_20260523
- new engineering answer to a newly formalized problem (657.906 to 663.213s): #efef9f; human_approved_lesson_takeaway_span_20260523
- domain itself had an edge (678.318 to 680.461s): #efef9f; human_approved_lesson_takeaway_span_20260523
- not dynamically vetted against that problem (704.812 to 711.408s): #efef9f; human_approved_lesson_takeaway_span_20260523
- framework that has not yet formalized a real risk (722.581 to 727.867s): #efef9f; human_approved_lesson_takeaway_span_20260523
- trusted model stopped matching the world (780.78 to 785.465s): #efef9f; human_approved_lesson_takeaway_span_20260523
- boundary of a model (829.077 to 830.679s): #efef9f; human_approved_lesson_takeaway_span_20260523

## Required Response

Reply with exactly one disposition: `keep`, `tighten`, or `reject`.
