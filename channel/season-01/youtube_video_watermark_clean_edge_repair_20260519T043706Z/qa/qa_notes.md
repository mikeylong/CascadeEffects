# QA Notes

Status: `review_required`.

- `official_requirements_read`: pass
- `skill_workflow_read`: pass
- `watermark_dimensions_read`: pass; output is 800 x 800
- `minimum_watermark_dimension_read`: pass; output exceeds 150 x 150
- `watermark_file_size_read`: pass; output is under 1 MB
- `alpha_channel_read`: pass; output is RGBA
- `corner_alpha_read`: pass; corners are transparent
- `center_alpha_read`: pass; center is opaque
- `smooth_edge_alpha_read`: pass; partial alpha edge pixels present
- `baked_circle_ring_read`: pass for review; no visible guide ring intended
- `youtube_studio_updated`: false

Before/after: `qa/video-watermark-clean-edge-before-after.png`
Contact sheet: `qa/video-watermark-clean-edge-contact-sheet.png`
