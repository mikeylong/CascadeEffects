# Motion Contact Sheet Manifest Template

## Manifest

- `stage`: `motion contact sheet`
- `episode_id`:
- `short_id`:
- `workflow_scope_manifest_path`:
- `production_model_decision_path`:
- `production_model_lane`: `source_led_motion|source_derived_reanimation|sourced_stills|generated_stills|hybrid`
- `hero_source_family_ids`:
- `render_authorization_path`:
- `render_authorization_read`: `pass|tighten|reject`
- `dp_shot_packet_path`:
- `episode_constraint_ledger_path`:
- `input_stills_or_keyframe_manifest_path`:
- `archival_footage_review_path`:
- `shot_timing_edl_path`:
- `shot_timing_edl_disposition`: `keep|tighten|diagnostic only|reject`
- `historical_signal_texture_registry_path`: `/Users/mike/CascadeEffects/archive/season-01-reference/legacy-style-packages/style-packages/source_preserving_documentary_v1/archival_signal_texture_recipes.json`
- `contact_sheet_path`:
- `preview_reel_path`:
- `disposition`: `keep|tighten|diagnostic only|reject`
- `may_start_motion_video_proof`: `true|false`

## Candidate Items

- `case_id`:
- `beat_id`:
- `visual_beat_id`:
- `motion_strategy`: `direct_source_clip|source_derived_reanimation|direct_source_still|still_driven_i2v|generated_still|hybrid_generated`
- `source_or_generation_reason`:
- `render_authorization_read`: `pass|tighten|reject`
- `motion_pipeline`: `direct_source_clip|direct_source_still|distilled|apple-ltx23-q8-one-stage|apple-ltx23-keyframe-dev|other`
- `source_still_path`:
- `source_clip_path`:
- `source_span_in`:
- `source_span_out`:
- `start_keyframe_path`:
- `end_keyframe_path`:
- `raw_motion_path`:
- `normalized_no_audio_path`:
- `audio_stream_read`: `none|source_retained|backend_generated|unknown`
- `hygiene_read`: `pass|tighten|reject|not_applicable`
- `temporal_coherence_read`: `pass|tighten|reject`
- `physical_plausibility_read`: `pass|tighten|reject`
- `source_motion_alignment_read`: `pass|tighten|reject`
- `archival_fidelity_read`: `pass|tighten|reject|not_applicable`
- `texture_influence`: `none|house_crt`
- `historical_context_year_or_range`:
- `source_media_era`: `none|analog_broadcast_crt|analog_institutional_video|late_analog_news_camcorder|early_digital_news_web|mobile_social_news`
- `historical_signal_profile_id`: `none|era_1980s_broadcast_crt_v1`
- `texture_source_lane`: `none|baseline|conservative_clean|other`
- `texture_applied_path`:
- `signal_texture_strength`: `none|low|low_to_visible|visible_but_premium|medium|diagnostic_only`
- `texture_application_scope`: `none|house_crt_story_clips|diagnostic_only`
- `inter_clip_static_policy`: `none|randomized_tv_static_between_story_clips`
- `youtube_survival_proxy_path`:
- `historical_signal_texture_read`: `pass|tighten|reject|pending_human_review|not_applicable`
- `texture_visibility_read`: `pass|tighten|reject|pending_human_review|not_applicable`
- `house_crt_texture_read`: `pass|tighten|reject|pending_human_review|not_applicable`
- `signal_interruption_read`: `pass|tighten|reject|pending_human_review|not_applicable`
- `youtube_survival_read`: `pass|tighten|reject|pending_human_review|not_applicable`
- `compression_artifact_read`: `pass|tighten|reject|pending_human_review|not_applicable`
- `detail_survival_read`: `pass|tighten|reject|pending_human_review|not_applicable`
- `texture_failure_mode`: `texture_invisible_no_reviewable_historical_signal|historical_signal_overpowering_subject|compression_shimmer_or_mud|historical_signal_cheese|detail_loss_from_signal_texture|signal_interruption_masks_story_footage|house_crt_mismatch|none`
- `review_method`:
- `frame_audit_paths`:
- `shot_timing_edl_row_ids`:
- `no_internal_cut_read`: `pass|tighten|reject|not_applicable`
- `story_shot_duration_read`: `pass|tighten|reject|not_applicable`
- `continuity_vector`:
- `selected_for_motion_video_proof`: `true|false`
- `disposition`: `keep|tighten|diagnostic only|reject`

## Shot Timing EDL Gate

- `proof_assembly_requires_shot_timing_edl`: `true`
- `story_shot_duration_floor_seconds`: `2.0`
- `beat_rollup_is_secondary`: `true`
- `hidden_source_native_cuts_allowed`: `false unless each cut is represented by its own EDL row`
- `contact_sheet_to_proof_parity_required`: `true`

## Historical Signal Texture Gate

- Texture is the active house style for proof/final story clips unless explicitly waived.
- A textured candidate may be selected only when the underlying motion candidate is `keep`, no-audio, source-clean, and frame-audited.
- Use `era_1980s_broadcast_crt_v1` at `visible_but_premium` as the Challenger-calibrated house clip texture.
- Use Challenger-style randomized signal interruption only at eligible story-clip cuts; do not use full-frame static cards.
- Do not select alternate texture profiles by episode era, source medium, or beat family.
- TV frames, mattes, borders, rounded masks, reduced image area, and audio streams are hard rejects for texture outputs.
- Invisible, non-reviewable texture is a reject; it is not a successful “subtle” pass.
