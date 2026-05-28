# Living Cover HTML Rough Proof Review Packet

## Review Target

- Episode ID: `EPISODE_ID`
- Packet: `PACKET_ID`
- Player: `PLAYER_PATH`
- Living Cover system version: `living_cover_system_v1`
- Rail preset: `fixed_16x9_right_rail_v1`
- Rail content model: `rolling_caption_anchor_v1`
- Caption display model: `rolling_rail_caption_window_v1`
- Caption display chunking: `script_locked_chunk_split_v1`
- Review chrome policy: `hidden_in_render_mode`
- Highlight render policy: `reviewed_cue_map_spans_only`
- Caption window role: `middle_two_thirds_right_rail`
- Caption blur scope: `caption_window_only`
- Caption highlight source: `living_cover_cue_map_key_phrases`
- Caption palette source: `sampled_episode_backplate`
- Captioning process: `living_cover_captioning_process_v1`
- Ambient/effects process: `living_cover_ambient_effects_layer_v1`
- Music integration process: `living_cover_music_integration_contract_v1`
- Caption output model: `dual_visible_rail_and_youtube_vtt_sidecar`
- Caption text source: locked narration script path/hash
- Caption timing source: WhisperX JSON or timed VTT/SRT path/hash, timing only
- Override status: `none`

## Review Focus

Review the proof as a YouTube video frame, not as an interactive web app.

- Fixed `1920x1080` canvas scales inside the browser shell without rail reflow.
- Source art remains the episode-specific visual carrier.
- Generated carriers record explicit generation tool/model provenance.
- Source art has been measured against the episode's historical/source-reference criteria; wrong architecture, equipment, period setting, or public anchor blocks promotion even when the image looks good.
- A packet-local Living Cover cue map explains chapter shifts, typography cues, effect-map moments, source-safe motion, and outro/end-screen behavior.
- The cue map is internal only and must not appear as a standalone visible cue card, cue panel, node list, label, or implementation-status surface unless explicitly human-approved.
- A packet-local ambient/effects layer declares source-integrated motion, micro-life, occlusion, or reviewed `none|minimal` restraint.
- A packet-local music integration contract declares the active series music pattern, approved intro/outro sources, voice-start offset, fade/outro policy, final VO-to-outro blend plan, transition review sample, caption/chapter retiming, level/rights reads, and any waiver. Without this contract, the proof is `review_ready_blocked_missing_music_contract`, not keep-ready.
- When the proof has a music-only intro or voice-start offset, the first minimal rail anchor must already be readable at `0s`, mid-intro, and voice start; no ghosted legacy title/summary/context stack should appear while story time is clamped at `0`.
- Ambient/effects debug overlays, matte previews, route overlays, QA labels, effect-lane names, and implementation-status panels must not appear in viewer-facing proof frames unless explicitly human-approved for diagnostic review.
- Right rail stays in the safe area and does not cover the main public anchor.
- Rail backlight/readability treatment is localized; it must not become a permanent full-height opaque right column below the active scene text.
- Rail content suppresses top title/chapter copy for caption-only review, or uses only a minimal top anchor when explicitly enabled, plus a middle/right rolling caption window.
- Legacy previous/upcoming context rows are removed.
- The caption window has subtle localized blur/fill only behind captions, with softened top and bottom fade masks; it must not read as a rectangle, card, or full-height right-rail panel.
- Rolling captions are deterministic from audio/render time: the proof must expose `window.__railCaptionStateAt(time)` and preserve `window.__setRenderTime(time)`, with no free-running scroll drift, jumps, layout reflow, or seek/scrub jitter.
- Long cues split into script-locked display chunks before layout, with the active chunk and faint adjacent chunks only.
- Key phrase highlights render only from reviewed Living Cover cue-map spans, with exact phrase text, normalized script token range, timing window, source-sampled color, fade-in/out, and review status. Missing reviewed spans suppress highlight rendering and keep the packet pending.
- Review controls, transport chrome, model IDs, QA labels, and internal review copy must stay outside the video frame in review mode and be hidden in render/QA mode.
- All viewer-facing story/chapter/caption/effect/end-screen text stays inside the fixed right rail unless a human-approved override names another surface.
- Ordinal-only labels such as `CHAPTER 01`, `PART 1`, or `SECTION 03` are invalid visible chapter/title copy.
- Rail typography is video-legible and fixed-metric: top anchor title copy is suppressed in caption-only review, and rolling captions target `32-34px` with lighter density, narrower measure, and enough vertical breathing room.
- Rolling captions use script-locked cue text in the middle right rail window; ASR/WhisperX/VTT/SRT sources are timing-only.
- If the music contract shifts voice start, captions, chapters, cue-map anchors, and rail story time must be retimed from locked-script text.
- Generated caption words must normalize to the locked narration script; ASR/WhisperX/VTT/SRT text may provide timing only.
- Caption typography matches the rail, avoids word-by-word karaoke, and adds no card, badge, border, glow, timecode, progress bar, or accent embellishment.
- Captions are required by default; final renders should burn visible rail captions into the video while preserving the approved VTT sidecar for YouTube upload.
- Right-rail labels must be episode-specific viewer-facing copy, with stale cross-episode/internal labels blocked.
- End-screen review checks static platform target geometry; continuous ambient background motion is allowed only when its read passes.
- End-screen review checks a passing `end_screen_palette_contract`: target fill, borders, subscribe ring, muted rail text, and accents are sampled from or harmonized with the approved backplate, with no copied Challenger/default colors unless a named human-approved override is recorded.
- End-screen review checks that captions continue upward into the transition, then the caption window, blur, fill, and all rail/caption/highlight text fade to zero before the YouTube target-geometry window.
- End-screen review checks that no faint chapter, context, caption, cue, rail, or diagnostic text remains behind YouTube target geometry unless a human-approved title policy explicitly scopes it.
- Final render may start only from this proof if this proof is kept, and the renderer must record the kept proof path/hash.
- Chapter-driven source-art `x/y/scale/roll/warmth` changes use `challenger_staged_visual_transition_v1`: hold previous visual state for `0-120ms`, smoothstep mix from `120-600ms`, then settle on the next visual state.
- Rough-proof QA must sample every chapter boundary at `+0.00s`, `+0.12s`, `+0.36s`, `+0.60s`, and `+0.80s`, expose `window.__visualStateAt(time)`, and provide a focused transition review strip. Hard visual switches block review.

## Human Review Reads

| Read | Status |
| --- | --- |
| living_cover_system_version_read | `pending_human_review` |
| captioning_process_version_read | `pending_human_review` |
| fixed_16x9_canvas_read | `pending_human_review` |
| browser_shell_letterbox_read | `pending_human_review` |
| source_art_carrier_read | `pending_human_review` |
| generation_tool_provenance_read | `pending_human_review` |
| historical_accuracy_read | `pending_human_review` |
| source_reference_alignment_read | `pending_human_review` |
| public_anchor_geometry_read | `pending_human_review` |
| episode_specific_architecture_or_equipment_read | `pending_human_review` |
| living_cover_cue_map_read | `pending_human_review` |
| chapter_cue_coverage_read | `pending_human_review` |
| typography_cue_read | `pending_human_review` |
| effect_map_cue_read | `pending_human_review` |
| source_safe_motion_read | `pending_human_review` |
| cue_no_diagnostic_overlay_read | `pending_human_review` |
| cue_map_internal_artifact_read | `pending_human_review` |
| visible_cue_overlay_read | `pending_human_review` |
| ambient_effects_plan_read | `pending_human_review` |
| ambient_effect_lane_decision_read | `pending_human_review` |
| source_plate_matte_registration_read | `pending_human_review` |
| foreground_occlusion_read | `pending_human_review` |
| effect_layer_source_safety_read | `pending_human_review` |
| deterministic_ambient_read | `pending_human_review` |
| additive_effect_integration_read | `pending_human_review` |
| debug_overlay_absence_read | `pending_human_review` |
| ambient_effect_browser_sample_read | `pending_human_review` |
| range_scrub_effect_review_read | `pending_human_review` |
| localized_particle_density_read | `not_applicable` |
| particle_foreground_leak_read | `not_applicable` |
| public_motion_occlusion_reappearance_read | `not_applicable` |
| practical_light_micro_life_read | `not_applicable` |
| screen_glow_motion_read | `not_applicable` |
| music_integration_plan_read | `pending_human_review` |
| series_music_contract_read | `pending_human_review` |
| approved_music_source_read | `pending_human_review` |
| intro_music_contract_read | `pending_human_review` |
| voice_start_offset_read | `pending_human_review` |
| caption_timing_shift_read | `pending_human_review` |
| full_outro_music_read | `pending_human_review` |
| end_screen_music_handoff_read | `pending_human_review` |
| vo_outro_blend_plan_read | `pending_human_review` |
| vo_outro_music_blend_read | `pending_human_review` |
| outro_transition_review_sample_read | `pending_human_review` |
| outro_entry_level_match_read | `pending_human_review` |
| outro_prelap_source_read | `pending_human_review` |
| outro_prelap_start_read | `pending_human_review` |
| outro_no_restart_at_voice_end_read | `pending_human_review` |
| outro_source_continuity_read | `pending_human_review` |
| audio_level_mix_read | `pending_human_review` |
| music_rights_read | `pending_human_review` |
| music_contract_regression_read | `pending_human_review` |
| no_music_or_temp_music_waiver_read | `not_applicable_no_waiver_requested` |
| intro_music_fade_tail_read | `pending_human_review` |
| intro_rail_readiness_read | `pending_human_review` |
| intro_active_title_read | `pending_human_review` |
| intro_summary_legibility_read | `pending_human_review` |
| intro_context_readability_read | `pending_human_review` |
| intro_transition_completion_read | `pending_human_review` |
| right_rail_safe_space_read | `pending_human_review` |
| rail_backlight_scope_read | `pending_human_review` |
| right_rail_opacity_balance_read | `pending_human_review` |
| context_region_source_visibility_read | `pending_human_review` |
| caption_softener_scope_read | `pending_human_review` |
| viewer_text_surface_inventory_read | `pending_human_review` |
| right_rail_text_boundary_read | `pending_human_review` |
| out_of_rail_text_read | `pending_human_review` |
| ordinal_chapter_label_read | `pending_human_review` |
| end_screen_text_boundary_read | `pending_human_review` |
| human_presence_read | `pending_human_review` |
| no_recognizable_faces_read | `pending_human_review` |
| rail_preset_read | `pending_human_review` |
| rail_content_model_read | `pending_human_review` |
| caption_display_model_read | `pending_human_review` |
| caption_display_chunking_read | `pending_human_review` |
| review_chrome_policy_read | `pending_human_review` |
| highlight_render_policy_read | `pending_human_review` |
| caption_window_role_read | `pending_human_review` |
| caption_window_blur_scope_read | `pending_human_review` |
| caption_highlight_source_read | `pending_human_review` |
| caption_palette_source_read | `pending_human_review` |
| no_responsive_rail_reflow_read | `pending_human_review` |
| no_rail_scale_hack_read | `pending_human_review` |
| chapter_label_legibility_read | `pending_human_review` |
| active_beat_title_legibility_read | `pending_human_review` |
| summary_legibility_read | `pending_human_review` |
| context_legibility_read | `pending_human_review` |
| old_context_rows_absence_read | `pending_human_review` |
| minimal_anchor_read | `pending_human_review` |
| copy_hierarchy_read | `pending_human_review` |
| current_context_deduplication_read | `pending_human_review` |
| native_caption_behavior_read | `pending_human_review` |
| rolling_caption_behavior_read | `pending_human_review` |
| rolling_caption_state_hook_read | `pending_human_review` |
| caption_scroll_smoothness_read | `pending_human_review` |
| caption_window_fade_mask_read | `pending_human_review` |
| caption_window_fill_palette_read | `pending_human_review` |
| caption_key_phrase_span_read | `pending_human_review` |
| caption_highlight_fade_read | `pending_human_review` |
| caption_required_read | `pending_human_review` |
| caption_output_model_read | `pending_human_review` |
| caption_text_source_read | `pending_human_review` |
| caption_timing_source_read | `pending_human_review` |
| caption_text_matches_script_read | `pending_human_review` |
| caption_alignment_coverage_read | `pending_human_review` |
| caption_asr_text_not_used_read | `pending_human_review` |
| caption_known_regression_fixture_read | `pending_human_review` |
| caption_phrase_level_read | `pending_human_review` |
| no_karaoke_caption_read | `pending_human_review` |
| rail_typography_match_read | `pending_human_review` |
| caption_bottom_rail_fit_read | `pending_human_review` |
| caption_spacing_read | `pending_human_review` |
| caption_no_embellishment_read | `pending_human_review` |
| caption_vtt_reference_read | `pending_human_review` |
| caption_sidecar_preservation_read | `pending_human_review` |
| caption_waiver_read | `pending_human_review` |
| stale_cross_episode_label_read | `pending_human_review` |
| transition_staging_read | `pending_human_review` |
| challenger_staged_transition_model_read | `pending_human_review` |
| first_chapter_boundary_visual_ease_read | `pending_human_review` |
| chapter_boundary_hard_shift_read | `pending_human_review` |
| focused_transition_review_strip_read | `pending_human_review` |
| visual_state_debug_hook_read | `pending_human_review` |
| end_screen_hold_read | `pending_human_review` |
| end_screen_palette_contract_read | `blocked_pending_approved_backplate_palette_sample` |
| end_screen_target_fill_palette_read | `blocked_pending_approved_backplate_palette_sample` |
| end_screen_target_contrast_read | `blocked_pending_approved_backplate_palette_sample` |
| no_cross_episode_default_palette_read | `blocked_pending_approved_backplate_palette_sample` |
| continuous_ambient_end_screen_preservation_read | `pending_human_review` |
| youtube_target_geometry_static_read | `pending_human_review` |
| end_screen_title_policy_read | `pending_human_review` |
| end_screen_text_artifact_read | `pending_human_review` |
| viewer_text_suppression_read | `pending_human_review` |
| caption_suppression_read | `pending_human_review` |
| caption_end_screen_rollout_read | `pending_human_review` |
| rail_fade_read | `pending_human_review` |
| current_kept_proof_render_source_read | `pending_future_final_render` |
| caption_sidecar_read | `pending_future_final_render` |
| visible_rail_captions_burned_in_read | `pending_future_final_render` |
| downstream_gate_read | `pending_human_review` |
| no_progress_bar_read | `pending_human_review` |
| no_timecode_read | `pending_human_review` |
| gradient_vignette_read | `pending_human_review` |
| copied_media_read | `pending_human_review` |

## Locked Scope

HTML-only review proof. No MP4 render, final assembly, Shorts work, publish readiness, or YouTube action is authorized unless a later human review explicitly authorizes it.

## Required Response

Reply with exactly one disposition: `keep`, `tighten`, or `reject`.
