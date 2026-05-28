# QA Notes

Status: `rejected_human_review`.

## Checks

- `official_requirements_read`: pass
- `skill_workflow_read`: pass
- `display_strip_target_read`: pass (`2048 x 340` strips are primary)
- `dimensions_read`: pass
- `upload_canvas_read`: pass (`2048 x 1152` wrappers included)
- `file_size_read`: pass (all final banner assets under `6 MB`)
- `safe_area_read`: pass (title/logos constrained to centered safe area; only Candidate B has title)
- `crop_resilience_read`: reject
- `profile_icon_alignment_read`: pass (profile icon not duplicated)
- `final_embellishment_read`: pass (no safe-zone boxes, frames, borders, or guide overlays in final assets)
- `generated_text_read`: pass (no generated title text; Candidate B title is local deterministic composition)
- `waterfall_read`: pass (cyan elements are treated as dry vellum signal/ribbon, not liquid)
- `texture_noise_read`: pass for review (clean paper planes; no high-frequency texture blocker observed at strip size)

## Review Artifacts

- Overlay previews are review artifacts only and must not be uploaded as final banner assets.
- Mike rejected this package after review; `may_advance` remains false.
