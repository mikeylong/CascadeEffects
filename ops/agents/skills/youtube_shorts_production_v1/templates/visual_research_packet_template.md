# Visual Research Packet Template

## Packet

- `episode_id`:
- `short_id`:
- `workflow_scope_manifest_path`:
- `dp_research_brief_path`:
- `narration_map_path`:
- `archival_footage_review_path`: `pending unless archival motion is in scope`
- `production_model_decision_path`: `pending until coordinator chooses source/generation lane after research`
- `visual_beatmap_path`: `pending until DP derives after visual research`
- `dp_shot_packet_path`: `pending until visual beatmap is approved`
- `episode_constraint_ledger_path`: `pending until DP approval`
- `short_script_path`:
- `visual_spine_target`: `9 beats + short pre-beat`
- `cue_ranges_path`:
- `caption_text_source_path`:
- `caption_timing_source_path`:
- `audio_package_sha256`:
- `transcript_sha256`:
- `style_skill_path`: `/Users/mike/CascadeEffects/archive/season-01-reference/legacy-style-packages/style-packages/source_preserving_documentary_v1/SKILL.md`
- `subject_render_matrix_path`: `/Users/mike/CascadeEffects/archive/season-01-reference/legacy-style-packages/style-packages/source_preserving_documentary_v1/judgment/subject_render_matrix.md`
- `exact_dp_imports_used`:
- `disposition`: `keep|tighten|diagnostic only|reject`
- `blockers`:

## Scope Compliance

- `active_episode_short_root`:
- `active_episode_production_root`:
- `active_viz_short_root`:
- `used_only_scoped_paths`: `true|false`
- `unapproved_legacy_paths_found`:
- `dp_import_requests`:

## Research Rules

- Use references as constraints for subject identity, mechanism clarity, materials, setting, camera logic, and palette.
- Do not copy a reference image, artist style, logo, readable archival text, UI, poster, or caption design into generated stills.
- Keep research mechanism-led; a mood note alone is not enough to authorize still generation.
- Apply the `engaging and visually stimulating` thesis during artifact selection itself because the chosen artifacts drive downstream still and motion choices.
- When archival motion is in scope, complete the archival footage review before the visual beatmap is locked.
- Prefer scene-led research artifacts first, mechanism inserts second, and low-energy admin-detail props only as explicit exceptions.
- Keep archival source breadth narrow: `1-3` primary videos plus at most `2` backups.
- Under `strict clean`, any visible logo, stinger, lower-third, watermark, burned caption, end card, split screen, or channel bug is an automatic reject.
- Every beat or shot must map to a recognizable source anchor or record a DP-approved `nonliteral_exception_approved`.
- Approved sourced carriers are allowed when they are explicitly recorded as `carrier_mode: sourced` or `hybrid` with provenance.
- When archival motion has the best visual language, prefer source-derived reanimation over AI-generated still replacement: select clean source spans and keyframes that can produce beat-length motion handles while preserving archival fidelity.
- One strong archival footage family may satisfy multiple narration lines; do not force one literal visual per script clause.
- Do not inherit constraints from old Challenger/Hyatt/Therac/737 artifacts, old manifests, old renders, model experiments, keeper registries, casebooks, or packaging rules.
- Treat all proposed constraints as inactive until the DP places them in the active episode constraint ledger.
- Do not read `/archive/`, `/archives/`, `/experiments/`, `/legacy/`, `/retired/`, `/midjourney/`, `/proof_stills/`, diagnostic outputs, mixed-review outputs, old renders, or old manifests unless the workflow scope manifest lists the exact DP-approved import.
- Name missing evidence as a deferred gap instead of inventing visual certainty.

## Beat-Zone Research

### `visual_beat_id`

- `source_narration_range`:
- `narration_excerpt_or_transcript_range`:
- `mechanism_claim`:
- `primary_subject`:
- `candidate_artifact_total`:
- `composition_mode`: `single_subject|multi_object_tableau|split_panel_tableau`
- `lead_artifact_id`:
- `supporting_artifact_ids`:
- `optional_accent_artifact_ids`:
- `preferred_artifact_ids`:
- `backup_artifact_ids`:
- `preferred_clip_ids`:
- `backup_clip_ids`:
- `footage_family_id`:
- `archive_reference_mode`: `reference_only|sourced_candidate|hybrid`
- `texture_influence`: `none|house_crt`
- `canonical_subject_constraints`:
- `source_anchor_id`:
- `recognizable_source_anchor`:
- `source_anchor_paths_or_urls`:
- `anchor_preservation_rule`:
- `carrier_mode`: `generated|sourced|hybrid`
- `recommended_motion_strategy`: `direct_source_clip|source_derived_reanimation|direct_source_still|still_driven_i2v|generated_still|hybrid_generated`
- `source_or_generation_reason`:
- `source_derived_reanimation_suitability`: `none|low|medium|high`
- `candidate_keyframe_pair_ids`:
- `anchor_drift_fail_conditions`:
- `nonliteral_exception_approved`: `true|false`
- `coverage_class`: `room_or_interior|structure_or_exterior|vehicle_vessel_or_aircraft|small_human_group|technical_insert|admin_detail`
- `object_cluster_rule`: `required only when coverage_class is object_cluster; at least two approved artifacts must remain visible in-frame`
- `engagement_goal`:
- `mechanism_visibility_rule`:
- `coverage_exception_approved`: `true|false`
- `constraint_hypotheses_from_research`:
- `historical_or_domain_reference_notes`:
- `reference_source_paths_or_urls`:
- `reference_source_quality`:
- `known_physical_scale_or_dimensions`:
- `literal_vs_representational_use`: `literal object|cut sample/coupon|subscale test article|administrative carrier|metaphor|composite`
- `scene_custody_or_access_logic`:
- `scale_source_paths_or_urls`:
- `physical_plausibility_check`: `pass|tighten|reject`
- `scale_or_custody_blockers`:
- `palette_material_constraints`:
- `camera_logic`:
- `allowed_anomaly_carriers`:
- `banned_anomaly_carriers`:
- `text_logo_ui_risks`:
- `deformation_or_model_risks`:
- `still_prompt_hypothesis`:
- `motion_risk_note`:
- `open_visual_questions`:
- `recommended_ledger_entries`:
- `research_disposition`: `keep|tighten|diagnostic only|reject`

#### Candidate Artifacts

| artifact_id | artifact_priority_rank | artifact_engagement_score | mechanism_visibility_score | motion_potential_score | downstream_coverage_role | scene_family | artifact_selection_rationale |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  | `1|2|3` | `1-5` | `1-5` | `1-5` |  |  |  |

#### Candidate Clips

| clip_id | timecode_in | timecode_out | source_family | clip_role | hygiene_status | reanimation_suitability_score | selected_for_visual_beat | clip_selection_rationale |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  | `reference_only|sourced_candidate|texture_reference|reanimation_candidate` | `pass|reject` | `1-5` | `true|false` |  |

#### Candidate Keyframe Pairs

| keyframe_pair_id | clip_id | start_timecode | end_timecode | start_keyframe_path | end_keyframe_path | same_camera_span_confirmed | crop_consistency_read | reanimation_use_case |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  | `true|false` | `pass|tighten|reject` |  |

## Constraint Proposal Summary

These proposals are not active until the DP approves them in the episode constraint ledger.

| proposal_id | beat_or_shot_id | proposed_constraint | evidence_paths_or_urls | recommended_status | reason |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  | `active|conditional|legacy_reference|retired` |  |

## Handoff

- `may_enter_stills_contact_sheet`: `true|false`
- `may_enter_production_model_decision`: `true|false`
- `may_request_DP_ledger_approval`: `true|false`
- `source_anchor_map_complete`: `true|false`
- `artifact_rankings_complete`: `true|false`
- `selected_research_gaps`:
- `next_action`:
