# Living Cover Visual System Plan Template

## Packet

- Episode ID: `EPISODE_ID`
- Phase gate: `visual_system_gate`
- Living Cover system version: `living_cover_system_v1`
- Rail preset: `fixed_16x9_right_rail_v1`
- Captioning process: `living_cover_captioning_process_v1`
- Ambient/effects process: `living_cover_ambient_effects_layer_v1`
- Music integration process: `living_cover_music_integration_contract_v1`
- Caption required: `true`
- Caption output model: `dual_visible_rail_and_youtube_vtt_sidecar`
- Override status: `none`
- Human disposition: `defer`

## Episode Visual-System Baseline

- Baseline path: `TBD`
- Baseline status: `TBD`
- Active baseline source-art path: `TBD`
- Active baseline source-art SHA-256: `TBD`
- Baseline source manifest path: `TBD`
- Baseline source manifest SHA-256: `TBD`
- Inherited required reads: `TBD`
- Inherited visual grammar: `TBD`
- Known superseded artifacts: `TBD`
- Deliberate deviations from baseline: `none`
- Baseline read: `pending_human_review`

## Source-Art Carrier

- Carrier type: `generated_raster_source_art`
- Source-art generator: `codex_builtin_image_gen`
- Long-form source-art style lane: `cascade-ink-lit-photoreal-v1 | episode_specific_source_preserving_photoreal_public_scene`
- Video visual style scope: `long_form_video_asset`
- Paper Architecture visual style policy: `blocked_for_video_assets`
- ImageGen primary source read: `pending_human_review`
- Non-ImageGen source-art exception: `not_applicable`
- Source/reference evidence path: `TBD`
- Source/reference evidence SHA-256: `TBD`
- Dimensions: `1920x1080`
- Source-art reads: `pending_human_review`
- Foreground admin prop read: `pending_human_review`
- Implied action/anticipation read: `pending_human_review`
- Ambient affordance read: `pending_human_review`

Non-default carriers such as `sourced_raster_source_art`, `hybrid_raster_source_art`, or `deterministic_composition_over_approved_raster` require a human-approved source-art exception before they can be active production backplates. Without that exception, sourced frames and deterministic compositions are reference-only or diagnostic-only.

Long-form episode backplates must not use `cascade-paper-architectures-ink-lit-v1` or resemble Paper Architecture. Active prompts must avoid folded-paper/foam-core aircraft or building models, paper planes, paper cutaway tableaux, cream paper forms, clean paper planes, and similar Paper Architecture cues. Record `video_visual_style_scope_read` and `paper_architecture_visual_style_read`; Paper Architecture resemblance is `reject`.

Source-art prompts must not default to foreground clipboards, binders, folders, paperwork stacks, legal pads, or generic desk evidence. Those props are blocked unless a human-approved episode exception names the exact object, explains why it is mechanism-critical, and keeps it from becoming the dominant foreground read. Prefer implied action, anticipation, subject/event presence, layered depth, practical light/screen glow, weather surfaces, crowd attention, machinery readiness, or other ambient/effects affordances.

## Historical Accuracy Context

- Real-world visual target: `TBD`
- Reference basis: `TBD source paths/URLs used to judge or guide ImageGen output`
- Canonical visual facts: `TBD`
- Allowed abstraction: `TBD`
- Hard mismatch blockers: `TBD`
- Episode-specific accuracy read: `TBD such as hyatt_atrium_architecture_read`

## Generation Provenance

- Tool: `codex_builtin_image_gen | mflux_generate_z_image_turbo | apple_ltx23_ltx_2_mlx | comfyui_flux | deterministic_composition | TBD`
- Model: `TBD`
- Model confidence: `explicit | inferred_from_path | unknown`
- Mode: `text_to_image | image_to_image | image_to_video | deterministic_render`
- Source generation path/SHA-256: `TBD`
- Final packet asset path/SHA-256: `TBD`
- Prompt path/SHA-256: `TBD`
- Init/reference image path/SHA-256: `TBD | not_applicable`
- Provenance notes: `TBD`

## Chapter Model

- Major section count: `6-8`
- Active panel hierarchy: current chapter label / active beat title / one short chapter summary.
- Context list: nearby previous/upcoming chapter titles only; current chapter omitted.
- Native rail captions: browser WebVTT/TextTrack cue behavior, bottom right rail slot, rail-native typography, no karaoke timing, no embellishment.
- Copy density: video-safe and sparse.

## Living Cover Cue Map

- Cue map path: `TBD`
- Cue map SHA-256: `TBD`
- Coverage: every major chapter has a source-safe visual cue.
- Cue types: chapter shift, right-rail key phrase typography, effect map/cascade moment as rail behavior or non-textual source-safe motion, source-safe motion/composition treatment, outro/end-screen.
- Render policy: internal production artifact only; do not render a standalone cue card, cue panel, node list, label, or implementation-status surface unless explicitly human-approved.
- Photoreal/source-preserving rule: no diagnostic connector lines, cyan signal traces, generated UI paths, or procedural marks over source art unless explicitly human-approved.

## Ambient/Effects Layer

- Ambient/effects layer path: `TBD`
- Ambient/effects layer SHA-256: `TBD`
- Lane decision: `none | minimal | source_drift_lighting | particles_dust | practical_light_or_screen_glow | public_scene_motion | mixed`
- Enabled lanes: `TBD`
- Rationale: `TBD`; required for `none` or `minimal`
- Source/matte coordinate policy: fixed `1920x1080` coordinates shared by source plate, matte, and effects when depth/occlusion is used.
- Foreground occlusion policy: effects that pass behind scene elements require matte or equivalent occlusion QA.
- Additive integration policy: successor proofs preserve prior approved effects unless a replacement is explicitly scoped.
- Determinism policy: record seed, count, speed, route, anchor, opacity, and timing parameters for reproducible effects.
- Browser/range QA: sample intro, middle, chapter-transition, and outro/end-screen times; use range-scrub review for late-episode checks.
- Debug policy: matte previews, route overlays, QA labels, implementation-status panels, and effect-lane names are review artifacts only and must not appear in viewer-facing proof frames.

## Music Integration Contract

- Music integration contract path: `TBD`
- Music integration contract SHA-256: `TBD`
- Contract lane: `challenger_style_intro_outro | episode_alternate_contract | no_music_or_temp_music_waiver`
- Series precedent: `Challenger-style unless human-approved alternate or waiver is recorded`
- Approved intro source path/SHA-256: `TBD`
- Approved outro source path/SHA-256: `TBD`
- Voice-start offset seconds: `TBD`
- Intro policy: `music_only_lead_in_when_source_has_lead_in; 2s fade tail under VO when using Challenger pattern`
- Outro/end-screen policy: `full outro music through static YouTube end-screen target window`
- VO/outro policy: `subtle_tail_outro_v1; approved full outro source enters only under the last 1-2s of VO at low bed level, reaches target only after voice end, and does not restart`
- Broad actual-outro prelap override: `none`; any 5s/high-gain prelap or target-at-voice-end behavior requires explicit human-approved override and validator evidence.
- Caption/chapter/story-time retiming policy: `retime locked-script captions, chapters, cue map, and rail anchors when voice_start_offset_seconds is nonzero`
- Intro rail readiness policy: `first right-rail state is settled and readable at 0s, mid-intro, and voice start when voice_start_offset_seconds is nonzero`
- Mix QA: `TBD level targets, fade curves, sample times, and no-clipping checks`
- Rights/Content ID notes: `TBD`
- Therac/Challenger regression policy: do not use under-opening-voice bed plus short 15s tail when matching Challenger.
- Waiver: `none` unless a human-approved waiver records rationale, affected episode/output/gates, and next required music action.

## Captioning

- Caption text source path: `TBD locked narration script`
- Caption text source SHA-256: `TBD`
- Caption timing source path: `TBD WhisperX JSON or timed VTT/SRT`
- Caption timing source SHA-256: `TBD`
- Timing source text usage: `timing_only_asr_text_not_used_for_output`
- Required generation model: `script_locked_canonical_text_timing_from_asr_v1`
- Required automatic alignment gate: `>=98.5%` coverage and no unmatched script span over `8` tokens, unless a human-approved deviation ledger is recorded.
- HTML proof behavior: browser-native `TextTrack` active WebVTT cues mirrored into the lower right rail.
- Final render behavior: visible rail captions burned into the video frame.
- Publish behavior: approved VTT sidecar preserved for YouTube upload.
- Known regression fixture behavior: record `caption_known_regression_fixture_read` for episode-specific homophone or ASR-risk phrases.
- Waiver: `none` unless a human-approved override records reason and affected outputs.

## Visual Defaults

- Fixed `1920x1080` canvas.
- Browser review shell may scale/letterbox/pillarbox outside the frame.
- Right rail uses `fixed_16x9_right_rail_v1` unless an override is proposed.
- Under `fixed_16x9_right_rail_v1`, all viewer-facing story/chapter/caption/effect/end-screen text stays inside the fixed right rail unless a human-approved override names another surface.
- Rail backlight/readability treatment must be localized around the active panel and caption region; do not plan a full-height opaque right-column veil below the active scene text unless a human-approved override scopes it.
- Ordinal-only labels such as `CHAPTER 01`, `PART 1`, or `SECTION 03` are invalid visible chapter/title copy.
- Right-rail labels are episode-specific viewer-facing language and require `stale_cross_episode_label_read`.
- End-screen holds use static YouTube target geometry, not whole-frame stillness; background motion policy must be recorded.
- End-screen text policy must prove chapter, context, caption, cue, rail, and diagnostic text are fully suppressed in the YouTube target-geometry window unless a human-approved title policy scopes visible text. Faint residual text fails QA.
- Final render starts only from the current kept HTML proof and records `current_kept_proof_render_source_read`.
- No baked progress bars, top timecode, global gradients/vignettes, evidence rows, left rules, copied media, or downstream advancement.

## Overrides

Use this only when the episode subject or safe-space requires changing the preset.

- Override status: `none | proposed | approved`
- Field changed: `TBD`
- Reason: `TBD`
- QA evidence: `TBD`
- Human disposition: `defer`

## Required Review Reads

| Read | Status |
| --- | --- |
| living_cover_system_version_read | `pending_human_review` |
| captioning_process_version_read | `pending_human_review` |
| fixed_16x9_canvas_read | `pending_human_review` |
| source_art_carrier_read | `pending_human_review` |
| video_visual_style_scope_read | `pending_human_review` |
| paper_architecture_visual_style_read | `pending_human_review` |
| foreground_admin_prop_read | `pending_human_review` |
| implied_action_anticipation_read | `pending_human_review` |
| ambient_affordance_read | `pending_human_review` |
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
| rail_preset_read | `pending_human_review` |
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
| copy_hierarchy_read | `pending_human_review` |
| youtube_legibility_read | `pending_human_review` |
| native_caption_behavior_read | `pending_human_review` |
| caption_required_read | `pending_human_review` |
| caption_output_model_read | `pending_human_review` |
| caption_text_source_read | `pending_human_review` |
| caption_timing_source_read | `pending_human_review` |
| caption_text_matches_script_read | `pending_human_review` |
| caption_alignment_coverage_read | `pending_human_review` |
| caption_asr_text_not_used_read | `pending_human_review` |
| caption_known_regression_fixture_read | `pending_human_review` |
| no_karaoke_caption_read | `pending_human_review` |
| caption_bottom_rail_fit_read | `pending_human_review` |
| caption_no_embellishment_read | `pending_human_review` |
| caption_vtt_reference_read | `pending_human_review` |
| caption_sidecar_preservation_read | `pending_human_review` |
| caption_waiver_read | `pending_human_review` |
| stale_cross_episode_label_read | `pending_human_review` |
| end_screen_hold_read | `pending_human_review` |
| continuous_ambient_end_screen_preservation_read | `pending_human_review` |
| youtube_target_geometry_static_read | `pending_human_review` |
| end_screen_title_policy_read | `pending_human_review` |
| end_screen_text_artifact_read | `pending_human_review` |
| viewer_text_suppression_read | `pending_human_review` |
| current_kept_proof_render_source_read | `pending_future_final_render` |
| texture_noise_read | `pending_human_review` |

## Review Question

Reply with exactly one disposition: `keep`, `tighten`, or `reject`.
