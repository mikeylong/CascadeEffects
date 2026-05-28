# Hyatt Audited Flash-Origin Ambient Layer

- Profile: `hyatt_audited_person_pixel_flash_origins_v1`
- Camera flashes: 180, from audited fixed person-pixel hotspots only.
- Balloons: 28, preserved from the prior kept table-bouquet origin clusters.
- Broad strip sampling: disabled.
- Flash rendering: small bright core plus soft bounded halo; the core remains the origin.
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
