# Tacoma Living Cover Cue Map

Status: `review_ready_human_keep_pending`
Human disposition: `pending`
Source art: `candidate_g_higher_wave_downshot` kept for Living Cover prereqs.

## Chapter/Cue Spine
- `bridge_already_moving` `00:00:00.000` story / `00:00:09.601` proof: The Bridge Was Already Moving - A collapse that began as ordinary motion turned into a feedback problem.
- `redesign_removed_stiffness` `00:01:44.521` story / `00:01:54.122` proof: The Redesign Removed Stiffness - The bridge became slender, elegant, cheaper, and more flexible.
- `galloping_became_normal` `00:03:26.901` story / `00:03:36.502` proof: Galloping Became Normal - Drivers watched the roadway rise and fall until motion became part of the bridge identity.
- `five_conditions` `00:05:06.841` story / `00:05:16.442` proof: Five Conditions Before The Cable - The failure chain was already being assembled before the bridge opened.
- `air_fed_the_twist` `00:08:34.515` story / `00:08:44.116` proof: The Air Fed The Twist - Torsion changed the airflow, and the airflow added energy back into torsion.
- `profession_changed` `00:09:59.145` story / `00:10:08.746` proof: The Profession Changed - The bridge fell, and bridge engineering changed its questions.
- `model_boundary` `00:11:16.229` story / `00:11:25.830` proof: The Model Had An Edge - The equations were not useless. They were incomplete outside their domain.
- `engineering_learns` `00:12:52.836` story / `00:13:02.437` proof: How Engineering Learns - Engineering learns by finding the edge of a model and rebuilding around it.

## Source-Safe Cue Rules
- Cue map is internal only; cue IDs and implementation labels must not render in viewer-facing proof.
- Viewer-facing text stays inside `fixed_16x9_right_rail_v1`.
- Do not add cyan vectors, diagnostic lines, out-of-rail chapter cards, or generated bridge geometry.
- Captions use locked script text and the offset VTT/SRT sidecars created for the 9.601451s music lead-in.

## Reads
- `living_cover_cue_map_read`: `pass_review_ready_packet_local_artifact_created`
- `chapter_cue_coverage_read`: `pass_8_semantic_sections_plus_outro_handoff`
- `typography_cue_read`: `pass_right_rail_only_semantic_episode_copy`
- `effect_map_cue_read`: `pass_6_source_safe_moments_no_diagnostic_overlay`
- `source_safe_motion_read`: `pass_planned_transform_opacity_crop_only_over_kept_plate`
- `cue_no_diagnostic_overlay_read`: `pass_no_cue_ids_or_overlay_marks_in_viewer_proof_plan`
- `cue_map_internal_artifact_read`: `pass_internal_json_md_only`
- `visible_cue_overlay_read`: `pass_blocked_for_viewer_facing_output`
- `viewer_text_surface_inventory_read`: `pass_planned_right_rail_captions_chapters_only`
- `right_rail_text_boundary_read`: `pass_fixed_16x9_right_rail_v1_only`
- `out_of_rail_text_read`: `pass_blocked_except_review_diagnostics_not_viewer_proof`
- `ordinal_chapter_label_read`: `pass_no_ordinal_only_viewer_labels`
- `end_screen_text_boundary_read`: `pass_story_text_suppressed_before_end_screen`
