# Hyatt Immediate Balloons And Subtle Full-Frame Flash Pulse Ambient Layer

- Profile: `hyatt_audited_flash_fullscreen_pulse_balloon_immediate_v1`
- Camera flashes: 180, unchanged from the audited person-pixel flash-origin profile.
- Full-frame pulse: enabled as a secondary exposure reaction only, capped at 0.070 alpha and drawn below the rail.
- Balloons: 28, with the first three prewarmed by negative start times so balloons are visible at `t=0`.
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
