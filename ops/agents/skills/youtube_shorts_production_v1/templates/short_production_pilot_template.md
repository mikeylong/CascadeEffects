# Short Production Pilot Template

## Short

- `episode_id`:
- `short_id`:
- `canonical_flow`: `fact-checked long-form script -> derived 60-second Short script -> audio -> narration map -> DP scope/research brief -> visual research packet -> production model decision -> visual beatmap -> shot_plan_v2 -> episode constraint ledger -> render authorization check -> stills/keyframe contact sheet -> stills video proof when needed -> motion contact sheet -> shot_timing_edl -> motion video proof -> video final -> publish package -> unlisted review upload -> platform checks -> public release decision -> keeper lesson capsule`
- `governing_skill_path`: `/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_production_v1/SKILL.md`
- `dp_skill_path`: `/Users/mike/Agents_CascadeEffects/references/skills/director_of_photography_v1/SKILL.md`
- `final_export_skill_path`: `/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_final_export_v1/SKILL.md`
- `audio_skill_path`: `/Users/mike/Audio_CascadeEffects/references/skills/youtube_shorts_audio_elevenlabs_v1/SKILL.md`
- `style_skill_path`: `/Users/mike/Viz_CascadeEffects/references/style_packages/source_preserving_documentary_v1/SKILL.md`
- `promotion_workflow_path`: `/Users/mike/Viz_CascadeEffects/references/style_packages/source_preserving_documentary_v1/judgment/promotion_workflow.md`
- `keeper_registry_path`:
- `proof_review_template_path`: `/Users/mike/FluxLab_CascadeEffects/proofs/suites/_proof_review_template.md`
- `restart_scope`: `challenger_first`
- `legacy_constraints_inactive_by_default`: `true`

## Stage Ledger

- `current_stage`:
- `last_completed_stage`:
- `next_required_gate`:
- `may_advance`: `true|false`
- `coordinator_decision_note_path`:

## Script Stage

- `source_writer_packet_path`:
- `source_longform_script_path`:
- `longform_fact_check_report_path`:
- `short_script_path`:
- `narration_map_path`:
- `cue_ranges_path`:
- `source_is_short_specific`: `true|false`
- `script_disposition`: `keep|tighten|diagnostic only|reject`
- `brand_motif_status`: `present|variant|waived|missing`
- `motif_family`:
- `motif_text`:
- `motif_waiver_reason`:
- `script_blockers`:

## Audio Stage

- `short_audio_pipeline_dir`:
- `short_audio_package_path`:
- `expected_voice_profile_id`:
- `audio_package_sha256`:
- `packaged_audio_sha256`:
- `audio_disposition`: `keep|tighten|diagnostic only|reject`
- `short_audio_wav_path`:
- `short_audio_transcript_path`:
- `transcript_sha256`:
- `short_audio_review_disposition`:
- `caption_model`: `script_locked_canonical_text_timing_from_asr_v1`
- `caption_text_source_path`:
- `caption_timing_source_path`:
- `caption_text_source_policy`: `script_locked_canonical_text_only`
- `caption_timing_source_policy`: `asr_whisperx_timing_only`
- `audio_package_provenance_checked`: `true|false`
- `brand_motif_status`: `present|variant|waived|missing`
- `motif_family`:
- `motif_text`:
- `motif_waiver_reason`:
- `ending_cadence_read`: `pass|tighten|reject`
- `ending_cadence_reference_package`:
- `audio_lane_registry_path`: `/Users/mike/Agents_CascadeEffects/references/shorts/audio_lane_registry.json`
- `voice_profile_registry_path`: `/Users/mike/Audio_CascadeEffects/references/voice_profiles/youtube_shorts_voice_profiles.json`
- `audio_blockers`:

## DP Scope And Constraint Stages

- `workflow_scope_manifest_path`:
- `workflow_scope_dp_approved`: `true|false`
- `dp_research_brief_path`:
- `visual_beatmap_path`:
- `dp_shot_packet_path`:
- `visual_research_evidence_path`:
- `episode_constraint_ledger_path`:
- `episode_constraint_ledger_status`: `draft|active|superseded|retired`
- `active_constraint_ids`:
- `conditional_constraint_ids`:
- `legacy_reference_ids`:
- `retired_constraint_ids`:
- `exact_dp_imports`:
- `scope_or_constraint_blockers`:

## Visual Research Packet Stage

- `visual_research_packet_path`:
- `visual_research_review_note_path`:
- `reference_sources_path`:
- `beat_zone_total`:
- `artifact_selection_thesis`: `engaging and visually stimulating`
- `artifact_rankings_complete`: `true|false`
- `minimum_candidate_artifacts_met`: `true|false`
- `canonical_constraints_recorded`: `true|false`
- `allowed_anomaly_carriers_recorded`: `true|false`
- `banned_anomaly_carriers_recorded`: `true|false`
- `camera_logic_recorded`: `true|false`
- `source_anchor_map_complete`: `true|false`
- `nonliteral_exception_count`:
- `sourced_or_hybrid_carrier_candidates`:
- `visual_research_disposition`: `keep|tighten|diagnostic only|reject`
- `visual_research_blockers`:
- `may_request_constraint_ledger_approval`: `true|false`
- `may_enter_stills_contact_sheet`: `true|false`

## Production Model Decision Stage

- `production_model_decision_path`:
- `production_model_lane`: `source_led_motion|source_derived_reanimation|sourced_stills|generated_stills|hybrid`
- `hero_source_family_ids`:
- `source_family_budget`:
- `generated_stills_policy`: `exception_only|expected|blocked`
- `production_model_decision_disposition`: `keep|tighten|diagnostic only|reject`
- `production_model_decision_blockers`:

## Visual Beatmap Stage

- `visual_beatmap_path`:
- `visual_beat_count`:
- `short_prebeat_present`: `true|false`
- `preferred_artifact_map_complete`: `true|false`
- `backup_artifact_map_complete`: `true|false`
- `visual_beatmap_disposition`: `keep|tighten|diagnostic only|reject`
- `visual_beatmap_blockers`:

## Render Authorization Stage

- `render_authorization_path`:
- `render_authorization_read`: `pass|tighten|reject`
- `shots_authorized_for_sourced_clip_or_still`:
- `shots_authorized_for_source_derived_reanimation`:
- `shots_authorized_for_generated_still`:
- `render_authorization_blockers`:

## Stills/Keyframe Contact Sheet Stage

- `short_manifest_path`:
- `stills_contact_sheet_path`:
- `stills_contact_sheet_review_note_path`:
- `selected_still_total`:
- `carrier_modes_used`:
- `anchor_match_status`: `pass|tighten|reject`
- `coverage_read_status`: `pass|tighten|reject`
- `variety_read_status`: `pass|tighten|reject`
- `engagement_read_status`: `pass|tighten|reject`
- `anchor_drift_cases`:
- `stills_contact_sheet_disposition`:
- `stills_contact_sheet_blockers`:

## Stills Video Proof Stage

- `stills_video_proof_path`:
- `stills_video_proof_manifest_path`:
- `stills_video_proof_review_note_path`:
- `stills_video_proof_disposition`:
- `stills_video_proof_blockers`:

## Motion Contact Sheet Stage

- `motion_contact_sheet_path`:
- `motion_contact_sheet_review_note_path`:
- `shot_timing_edl_path`:
- `shot_timing_edl_disposition`: `keep|tighten|diagnostic only|reject`
- `hidden_cut_read`: `pass|tighten|reject`
- `story_shot_duration_read`: `pass|tighten|reject`
- `selected_motion_total`:
- `motion_contact_sheet_disposition`:
- `motion_contact_sheet_blockers`:
- `frame_sampling_density_note`:

## Motion Video Proof Stage

- `motion_video_proof_path`:
- `motion_video_proof_manifest_path`:
- `motion_video_proof_review_note_path`:
- `beat_sheet_path`:
- `proof_assembled_from_shot_timing_edl`: `true|false`
- `contact_sheet_to_proof_parity_read`: `pass|tighten|reject`
- `hidden_cut_read`: `pass|tighten|reject`
- `story_shot_duration_read`: `pass|tighten|reject`
- `motion_video_proof_disposition`:
- `brand_motif_status`: `present|variant|waived|missing`
- `motif_family`:
- `ending_cadence_read`: `pass|tighten|reject`
- `reel_class`: `keeper short|mixed review short`
- `motion_video_proof_blockers`:

## First-Second Hook Retrofit Stage

- `first_second_hook_manifest_path`:
- `local_review_set_path`:
- `current_latest_publish_mp4_path`:
- `current_latest_publish_mp4_sha256`:
- `revised_first_second_proof_path`:
- `comparison_proof_path`:
- `frame_strip_path`:
- `waveform_path`:
- `opening_impact_audio_asset_id`: `opening_impact_theme_hit_v1`
- `opening_impact_audio_path`:
- `opening_impact_audio_sha256`:
- `impact_hit_start_seconds`: `0.00`
- `cold_flash_prebeat_length_seconds`: `0.75`
- `hook_visual_source_time_seconds`:
- `hook_visual_note`:
- `first_second_hook_read`: `pass|tighten|reject`
- `human_review_disposition`: `keep|tighten|reject`
- `local_only_no_youtube_action`: `true|false`
- `final_rebuild_allowed_after_human_keep`: `true|false`
- `duration_repair_policy`: `trim_nonessential_visual_hold_or_tail_first`
- `never_trim_for_hook`: `spoken motif|voice cadence|required caption content`
- `first_second_hook_blockers`:

## Video Final Stage

- `final_export_request_path`:
- `caption_style_preset`: `minimal_surreal_editorial_v1`
- `caption_placement`:
- `caption_timing_path`:
- `caption_overlay_manifest_path`:
- `captioned_final_path`:
- `final_export_manifest_path`:
- `final_export_review_note_path`:
- `motif_family`:
- `closing_motif_caption_preserved`: `true|false`
- `ending_cadence_read`: `pass|tighten|reject`
- `music_track_registry_path`: `/Users/mike/Agents_CascadeEffects/references/shorts/music_track_registry.json`
- `music_track_id`:
- `music_policy`: `canonical_default|waived|alternate_approved`
- `music_waiver_reason`:
- `music_rights_check_status`: `pending_youtube_upload_check|cleared|claim_warning|waived|not_applicable`
- `motif_outro_mix_used`: `true|false`
- `body_loop_sha256`:
- `outro_sha256`:
- `motif_music_bed_read`: `pass|tighten|reject|not_applicable`
- `outro_completion_read`: `pass|tighten|reject|not_applicable`
- `visual_extension_mode`: `cloned_final_frame|source_motion_tail|none`
- `final_frame_hold_seconds`:
- `source_motion_tail_path`:
- `source_motion_tail_residual_hold_seconds`:
- `final_mix_peak_db`:
- `first_second_hook_manifest_path`:
- `first_second_hook_applied`: `true|false`
- `caption_offset_seconds`:
- `duration_trim_decision`:
- `final_export_disposition`:
- `final_export_blockers`:

## Publish Package Stage

- `publish_skill_path`: `/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_publish_v1/SKILL.md`
- `publish_package_manifest_path`:
- `publish_package_check_command`: `/Users/mike/Viz_CascadeEffects/bin/ce orchestrate publish-package-check <manifest_path>`
- `review_upload_command`: `/Users/mike/Viz_CascadeEffects/bin/ce orchestrate publish-package-upload <manifest_path> --privacy unlisted`
- `publish_package_check_status`: `not_run|pass|fail|pass_with_warnings`
- `review_upload_receipt_path`:
- `youtube_video_id`:
- `youtube_video_url`:
- `privacy_status`: `unlisted|private|public|missing`
- `processing_status`:
- `thumbnail_status`: `uploaded|failed_nonfatal|not_declared|manual_required`
- `delete_receipt_path`:
- `studio_checks_required`: `copyright_content_id|paper_architecture_music|altered_content_disclosure|captions|cover_frame|audience_metadata_visibility`
- `public_release_boundary`: `manual_youtube_studio_only`
- `public_release_note`: `public release remains manual in YouTube Studio`

## Keeper Inventory

- `keeper_still_total`:
- `keeper_motion_total`:
- `keeper_short_total`:
- `final_publishable_total`:
- `keeper_lesson_capsule_path`:
- `keeper_lesson_capsule_status`: `missing|draft|complete`

## Deferred Gaps

- `stage`:
- `beat_id`:
- `carrier`:
- `failure_mode`:
- `best_attempt_path`:
- `next_carrier`:
- `reopen_condition`:

## Next Production Queue

1. `stage`:
2. `stage`:
3. `stage`:

## Blocking Gap

- `next_blocking_gap`:
