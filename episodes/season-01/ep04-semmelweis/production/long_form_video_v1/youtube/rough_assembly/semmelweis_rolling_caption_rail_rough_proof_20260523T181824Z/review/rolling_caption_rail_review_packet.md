# Semmelweis Rolling Caption Rail Rough Proof

## Review Target

- Episode ID: `semmelweis`
- Player: `/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/production/long_form_video_v1/youtube/rough_assembly/semmelweis_rolling_caption_rail_rough_proof_20260523T181824Z/player.html`
- Manifest: `/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/production/long_form_video_v1/youtube/rough_assembly/semmelweis_rolling_caption_rail_rough_proof_20260523T181824Z/rough_assembly_manifest.json`
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

- Action: `advance_right_rail_alignment_with_ambient_effects_deferred`
- Status: `rolling_caption_rail_rough_assembly_review_ready_right_rail_alignment_only_pending_human_keep`
- Source art rollback: not opened by default because the rail footprint is unchanged.
- Downstream gates: final assembly, publish readiness, and YouTube action remain blocked until this refreshed rough proof receives human `keep`.
- Scope: `right_rail_alignment_review_only`; ambient/effects v7 is deferred and not approved by this proof.


## Human Review Focus

- Captions roll smoothly through the middle two-thirds of the right rail with no seek jumps or layout jitter.
- The proof is injected into the predecessor rough proof shell so the kept source art, ambient behavior, audio timing, and end-screen timing remain active.
- The caption window has no blur, fill, panel, or container background; readability relies on source-aware text color, text shadow, and the entry/exit mask.
- Old previous/upcoming context rows are absent.
- Highlights render only from cue-map spans that are authored as story lesson/takeaway phrases, not technical labels or isolated single words.
- At the end-screen transition, captions continue upward and caption text/highlights fade fully out before YouTube target geometry.
- Right-rail safe space remains valid against the kept backplate.

## Key Phrase Spans

- problem it could measure but not explain (7.378 to 9.421s): #dede35; human_approved_lesson_takeaway_span_20260523
- difference was documented (39.73 to 41.052s): #dede35; human_approved_lesson_takeaway_span_20260523
- look directly at evidence (72.028 to 76.133s): #dede35; human_approved_lesson_takeaway_span_20260523
- death rates told a story (105.017 to 106.9s): #dede35; human_approved_lesson_takeaway_span_20260523
- This was not a subtle difference (132.308 to 136.145s): #dede35; human_approved_lesson_takeaway_span_20260523
- Semmelweis examined all of them (174.437 to 177.762s): #dede35; human_approved_lesson_takeaway_span_20260523
- Second Division midwives did not perform autopsies (221.249 to 228.142s): #dede35; human_approved_lesson_takeaway_span_20260523
- Not plain soap and water (251.077 to 252.679s): #dede35; human_approved_lesson_takeaway_span_20260523
- evidence actually required the profession to believe (281.268 to 285.498s): #dede35; human_approved_lesson_takeaway_span_20260523
- preserved the assumption (316.025 to 321.452s): #dede35; human_approved_lesson_takeaway_span_20260523
- results within weeks (375.618 to 378.622s): #dede35; human_approved_lesson_takeaway_span_20260523
- data-driven discipline should have moved decisively (392.53 to 395.717s): #dede35; human_approved_lesson_takeaway_span_20260523
- absence of a theoretical framework (446.196 to 448.901s): #dede35; human_approved_lesson_takeaway_span_20260523
- accepting the evidence meant accusing the physicians themselves (453.048 to 460.16s): #dede35; human_approved_lesson_takeaway_span_20260523
- evidence was too strong (515.673 to 517.295s): #dede35; human_approved_lesson_takeaway_span_20260523
- persistence in the face of accumulating evidence (554.593 to 561.283s): #dede35; human_approved_lesson_takeaway_span_20260523
- handwashing become standard practice (612.765 to 615.129s): #dede35; human_approved_lesson_takeaway_span_20260523
- wrong in a specific, structural way (645.152 to 651.699s): #dede35; human_approved_lesson_takeaway_span_20260523
- resistance hardened (675.529 to 678.232s): #dede35; human_approved_lesson_takeaway_span_20260523
- easier to absorb (738.952 to 742.997s): #dede35; human_approved_lesson_takeaway_span_20260523
- institution could afford to believe it (824.082 to 828.873s): #dede35; human_approved_lesson_takeaway_span_20260523
- cost of believing it was too high (850.443 to 852.248s): #dede35; human_approved_lesson_takeaway_span_20260523

## Required Response

Reply with exactly one disposition: `keep`, `tighten`, or `reject`.
