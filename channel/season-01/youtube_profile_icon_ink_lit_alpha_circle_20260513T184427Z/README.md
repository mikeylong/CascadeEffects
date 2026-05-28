# YouTube Profile Icon Ink-Lit Alpha-Circle Repair

Status: `superseded_for_profile_upload`

Superseded by: `youtube_profile_icon_clean_edge_repair_20260519T002930Z`

This package supersedes `youtube_profile_icon_ink_lit_20260512T201730Z` for the Cascade Effects YouTube channel avatar. It keeps the visible artwork unchanged and repairs only the upload packaging so the primary file is a true circular `RGBA` PNG with transparent corners and an antialiased circular edge.

As of `2026-05-19T04:35:27Z`, this package is no longer the current profile-upload source because the alpha-circle edge can produce visible artifacts in YouTube's avatar UI. It remains archived for traceability and legacy watermark-source evidence.

## Primary File

- `assets/profile-icon-800x800.png`

## Reference File

- `source/reference-profile-icon-square-rgb-20260512T201730Z.png`

## Review Files

- `previews/profile-icon-alpha-checkerboard-800.png`
- `previews/profile-icon-alpha-dark-800.png`
- `previews/profile-icon-alpha-white-800.png`
- `previews/profile-icon-circle-98px.png`
- `previews/profile-icon-circle-176px.png`
- `previews/profile-icon-circle-320px.png`
- `qa/profile-icon-alpha-circle-contact-sheet.png`

## QA Reads

- `alpha_channel_read: pass`
- `corner_transparency_read: pass`
- `circle_edge_antialias_read: pass`
- `profile_icon_circle_crop_read: pass`
- `small_size_recognition_read: pass`
- `homepage_contract_alignment_read: pass`

## Rollout

No YouTube channel profile, YouTube draft, MP4, or channel asset has been updated automatically.


## Approval

- `human_disposition: superseded_for_profile_upload`
- `human_disposition_reason: clean-edge square/no-alpha successor approved for YouTube profile upload`
- `used_by_package: youtube_channel_brand_assets_20260513T190642Z`


## Channel Asset Use

- `preferred_channel_asset_package: youtube_channel_brand_assets_repair_20260513T193457Z`
