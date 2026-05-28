# DP Shot Packet Template

## Shot Plan

- `stage`: `dp shot planning`
- `episode_id`:
- `short_id`:
- `shot_plan_id`: `shot_plan_v2`
- `coordinator_skill_path`: `/Users/mike/CascadeEffects/ops/agents/skills/youtube_shorts_production_v1/SKILL.md`
- `dp_skill_path`: `/Users/mike/CascadeEffects/ops/agents/skills/director_of_photography_v1/SKILL.md`
- `workflow_scope_manifest_path`:
- `dp_research_brief_path`:
- `narration_map_path`:
- `archival_footage_review_path`: `pending unless archival motion is in scope`
- `visual_beatmap_path`:
- `production_model_decision_path`:
- `production_model_lane`: `source_led_motion|source_derived_reanimation|sourced_stills|generated_stills|hybrid`
- `episode_constraint_ledger_path`:
- `canonical_flow`: `fact-checked long-form script -> derived 60-second Short script -> audio -> narration map -> DP scope/research brief -> visual research packet -> production model decision -> visual beatmap -> shot_plan_v2 -> episode constraint ledger -> render authorization check -> stills/keyframe contact sheet -> stills video proof when needed -> motion contact sheet -> shot_timing_edl -> motion video proof -> video final -> keeper lesson capsule`
- `source_writer_packet_path`:
- `source_longform_script_path`:
- `longform_fact_check_report_path`:
- `short_script_path`:
- `short_audio_wav_path`:
- `caption_source_path`:
- `caption_timing_path`:
- `approved_audio_duration_seconds`:
- `current_visual_research_packet_path`:
- `existing_approved_stills_source_path`:
- `existing_approved_motion_source_path`:
- `reason_for_dp_pass`:
- `exact_dp_imports_used`:
- `total_shot_count`:
- `longest_shot_duration_seconds`:
- `disposition`: `keep|tighten|diagnostic only|reject`

## DP Rules Applied

- `target_shot_duration_seconds`: `3-5`
- `max_motion_stretch`: `1.25x`
- `default_transition`: `straight cut`
- `archival_hygiene_rule`: `none|strict clean`
- `archival_source_breadth`: `none|1-3 primary archival videos plus up to 2 backups`
- `historical_signal_texture_policy`: `none|house_crt_default`
- `historical_signal_texture_registry_path`: `/Users/mike/CascadeEffects/archive/season-01-reference/legacy-style-packages/style-packages/source_preserving_documentary_v1/archival_signal_texture_recipes.json`
- `default_historical_signal_profile_id`: `none|era_1980s_broadcast_crt_v1`
- `inter_clip_static_policy`: `none|randomized_tv_static_between_story_clips`
- `source_derived_reanimation_allowed`: `true|false`
- `source_derived_reanimation_rule`: `same-camera clean source spans only; no cross-angle keyframes; strip all non-approved audio`
- `render_authorization_required`: `true`
- `shot_timing_edl_required_before_motion_proof`: `true`
- `captions_final_export_only`: `true`
- `generated_visual_text_allowed`: `false`
- `new_shot_families_require_visual_research_update`: `true|false`
- `physical_plausibility_gate`: `pass|tighten|required`
- `active_constraint_ledger_required`: `true`
- `legacy_constraints_inactive_by_default`: `true`
- `scope_hydration_gate`: `pass|tighten|required`
- `scale_custody_rule`: `large, hazardous, inaccessible, continuous, or one-off historical components must not be miniaturized into tabletop props unless explicitly documented as verified cut samples, test coupons, subscale articles, models, or non-literal carriers`

## Active Constraint Summary

- `active_constraint_ids`:
- `conditional_constraint_ids`:
- `legacy_reference_ids`:
- `retired_constraint_ids`:
- `constraints_requiring_DP_update`:
- `scope_or_import_blockers`:

## Editorial Spine Brief

- `editorial_spine_brief_path`:
- `hero_source_family_ids`: `2-4 source or scene families expected to carry the Short`
- `source_family_budget`: `brief note on which family carries opening|middle|ending and max room/admin/process coverage`
- `maximum_room_admin_process_seconds`:
- `continuity_vector`: `how the edit should progress visually; e.g. routine -> event escalation -> consequence`
- `subject_event_over_literal_coverage`: `shots or beat zones where subject/event imagery should beat literal narration coverage`
- `scroll_stop_exceptions_approved`:
- `editorial_spine_disposition`: `keep|tighten|diagnostic only|reject`

## Shots

### `shot_id`

- `source_beat_id`:
- `visual_beat_id`:
- `start_seconds`:
- `end_seconds`:
- `duration_seconds`:
- `narration_phrase`:
- `editorial_purpose`:
- `composition_mode`: `single_subject|multi_object_tableau|split_panel_tableau`
- `lead_artifact_id`:
- `supporting_artifact_ids`:
- `composition`:
- `lens_and_framing`:
- `lighting_palette`:
- `camera_logic`:
- `coverage_class`: `room_or_interior|structure_or_exterior|vehicle_vessel_or_aircraft|small_human_group|technical_insert|admin_detail`
- `object_cluster_rule`: `required only when coverage_class is object_cluster; at least two approved artifacts must remain visible in-frame`
- `engagement_goal`:
- `mechanism_visibility_rule`:
- `coverage_exception_approved`: `true|false`
- `scroll_stop_priority`: `subject_event|room_process|mechanism_insert|admin_detail|balanced`
- `continuity_vector`:
- `coverage_budget_role`: `hero_source_family|brief_context|support_insert|exception`
- `source_or_generation_reason`: `why this shot uses a sourced clip/still, source-derived reanimation, or generated still`
- `preferred_clip_ids`:
- `backup_clip_ids`:
- `footage_family_id`:
- `archive_reference_mode`: `reference_only|sourced_candidate|hybrid`
- `texture_influence`: `none|house_crt`
- `historical_context_year_or_range`:
- `source_media_era`: `none|analog_broadcast_crt|analog_institutional_video|late_analog_news_camcorder|early_digital_news_web|mobile_social_news`
- `historical_signal_profile_id`: `none|era_1980s_broadcast_crt_v1`
- `signal_texture_strength`: `none|low|low_to_visible|visible_but_premium|medium|diagnostic_only`
- `texture_application_scope`: `none|house_crt_story_clips|diagnostic_only`
- `youtube_survival_required`: `true|false`
- `inter_clip_static_policy`: `none|randomized_tv_static_between_story_clips`
- `texture_dp_override_reason`: `required only if texture is waived or deviates from house CRT`
- `literal_vs_representational_use`: `literal object|cut sample/coupon|subscale test article|administrative carrier|metaphor|composite`
- `known_physical_scale_or_dimensions`:
- `scale_source_paths_or_urls`:
- `scene_custody_or_access_logic`:
- `physical_plausibility_check`: `pass|tighten|reject`
- `scale_or_custody_blockers`:
- `movement`:
- `motion_source_preference`: `direct_source_clip|source_derived_reanimation|direct_source_still|still_driven_i2v|generated_still|hybrid_generated`
- `render_authorization_read`: `pass|tighten|reject`
- `render_authorization_note`: `can approved source solve this, does source-derived reanimation solve it better, or is generated still necessary`
- `reanimation_backend`: `none|apple-ltx23-keyframe-dev|other`
- `source_clip_id`:
- `source_clip_path`:
- `source_span_in`:
- `source_span_out`:
- `start_keyframe_path`:
- `end_keyframe_path`:
- `same_camera_span_required`: `true|false`
- `keyframe_crop_consistency_required`: `true|false`
- `reanimation_motion_boundaries`:
- `transition_in`:
- `transition_out`:
- `prompt_ready_still_concept`:
- `reuse_decision`: `reuse approved still|reuse with crop/timing|fresh scout pass|new full render`
- `reuse_source_path`:
- `fresh_scout_priority`: `none|low|medium|high`
- `fresh_scout_rationale`:
- `motion_strategy`:
- `native_motion_handle_target_seconds`:
- `maximum_allowed_stretch`:
- `allowed_motion_carriers`:
- `banned_elements`:
- `visual_research_update_needed`: `true|false`
- `notes`:

## Reuse And Scout Summary

- `shots_reusing_approved_stills`:
- `shots_reusing_with_crop_or_timing`:
- `shots_requiring_fresh_scout`:
- `shots_requiring_new_full_render`:
- `highest_priority_scouts`:

## Handoff

- `visual_research_packet_status`: `current|stale|missing`
- `archival_clip_alignment_status`: `current|stale|missing|not_in_scope`
- `physical_plausibility_summary`:
- `next_required_stage`: `visual research packet|production model decision|visual beatmap|episode constraint ledger|render authorization check|stills/keyframe contact sheet|stills video proof|motion contact sheet|shot_timing_edl|motion video proof`
- `blockers`:
- `deferred_gaps`:
- `may_advance`: `true|false`
