# Hyatt Long-Form Restart 2026-05-16

Active root for the restarted Hyatt long-form pipeline. The prior `production/longform_v1` package is reference-only and invalid for gate progression.

## Gate Order

1. Inventory: `/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/inventory/inventory_manifest.json`
2. Episode package: `/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/episode_package/episode_package_manifest.json`
3. Source art / visual system: `/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/source_art/hyatt_living_cover_restart_human_anonymous_imagegen_source_art_20260516T195611Z/source_art_manifest.json`
4. Motion readiness: `/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/motion_readiness/hyatt_living_cover_motion_readiness_blocked_20260516T194815Z/motion_readiness_manifest.json`
5. Rough assembly: blocked until motion readiness receives human `keep`
6. Final assembly: blocked until rough proof receives human `keep`
7. Publish readiness: blocked until final assembly receives human `keep`
8. Private upload: blocked until publish-readiness `keep` plus explicit upload approval

## Current Status

- Inventory: `review_ready`, human `defer`
- Episode package: `review_ready_pending_inventory_keep`, human `defer`
- Source art: `review_ready_pending_episode_package_keep`, human `defer`, anonymous human candidate active
- Motion readiness: `blocked_pending_upstream_keep`
- Rough proof: not created
- Final MP4: not created
- YouTube upload: not performed
