# Hyatt More Pronounced Flash-Core Ambient Layer

- Profile: `hyatt_audited_flash_more_pronounced_core_v1`
- Camera flashes: 180, with audited person-pixel origins preserved.
- Local core: retuned to 3-3.8px, 0.74-0.92 strength, 0.46-0.62s duration.
- Full-frame pulse: unchanged cap, coupled to visible local cores only.
- Balloons: preserved from predecessor.
- Gate state: pending human review; video render, publish readiness, and upload stay locked.

## Required Reads

- `audited_person_pixel_origin_read`: `pass_180_of_180_flash_origins_reference_audited_visible_person_hotspots`
- `slab_face_origin_rejection_read`: `pass_zero_flash_origins_inside_slab_face_exclusions`
- `walkway_fascia_origin_rejection_read`: `pass_zero_flash_origins_inside_walkway_fascia_exclusions`
- `flash_core_on_person_surface_read`: `pass_all_flash_cores_on_audited_visible_person_surfaces`
- `flash_halo_not_origin_read`: `pass_small_core_soft_halo_spill_not_origin`
- `audited_hotspot_contact_sheet_read`: `pass`
- `ambient_density_preservation_read`: `pass_180_flashes_28_balloons`
- `debug_overlay_absence_read`: `pass_debug_artifacts_separate_from_viewer_player_html`
- `broad_region_sampling_rejection_read`: `pass_no_broad_line_band_or_strip_sampling_in_active_flash_layer`
- `flash_jitter_limit_read`: `pass_all_flash_jitter_within_audited_hotspot_allowance`
- `source_locked_ambient_transform_read`: `pass`
- `audited_flash_origin_browser_read`: `pass_no_active_flash_origin_outside_audited_hotspots_or_inside_exclusions`
- `browser_flash_density_read`: `pass_180_flashes_reported`
- `browser_balloon_density_read`: `pass_28_balloons_reported`
- `browser_broad_mask_rejection_read`: `pass_no_broad_mask_flashes_reported`
- `balloon_effect_initial_frame_read`: `pass_3_balloons_visible_at_t0`
- `balloon_prewarm_origin_read`: `pass_first_three_balloons_prewarmed_from_existing_table_bouquet_clusters`
- `balloon_count_preservation_read`: `pass_28_balloons`
- `fullscreen_flash_pulse_read`: `pass_subtle_full_frame_exposure_pulse_present`
- `flash_pulse_subtlety_read`: `pass_max_alpha_0.0700_under_0.070`
- `flash_core_origin_preservation_read`: `pass_all_flash_cores_preserved_on_audited_person_pixels`
- `audited_flash_origin_preservation_read`: `pass_180_audited_flash_events_preserved_unchanged`
- `end_screen_flash_pulse_suppression_read`: `pass_end_screen_pulse_capped`
- `browser_page_load_read`: `pass`
- `opening_frame_balloon_browser_read`: `pass_3_active_balloons_at_t0`
- `flash_pulse_browser_sample_read`: `pass_flash_pulse_samples_recorded`
- `browser_screenshot_qa_read`: `pass_opening_flash_transition_end_samples_captured`
- `range_request_media_read`: `pass_206_partial_content_audio_mpeg`
- `flash_core_visibility_read`: `pass_more_pronounced_core_visible_for_multiple_frames`
- `flash_duration_visibility_read`: `pass_0p46_to_0p62_second_flash_duration`
- `flash_origin_precision_preservation_read`: `pass_all_180_audited_origins_preserved`
- `flash_halo_boundary_read`: `pass_halo_bounded_22_to_26px`
- `global_pulse_local_core_coupling_read`: `pass_no_global_pulse_without_visible_local_flash_core`
- `flash_not_strobe_read`: `pass_more_pronounced_without_strobe_or_washout`
