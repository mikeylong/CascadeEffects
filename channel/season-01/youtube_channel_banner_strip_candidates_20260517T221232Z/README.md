# Cascade Effects YouTube Banner Strip Candidates

Status: `rejected_human_review`

This package was rejected by Mike after review. It solved the mechanical `2048 x 340` strip and `2048 x 1152` wrapper requirements, but the candidates are not acceptable creative directions and must not be promoted. The older banner package remains rejected as `rejected_research_mismatch` and is not used as a candidate source.

## Official Constraints Used

- Minimum upload canvas: `2048 x 1152`, `16:9`.
- Recommended upload canvas: `2560 x 1440` for TV/full-canvas preview.
- Minimum-size text/logo safe area: `1235 x 338`, centered.
- File size limit: `6 MB` or smaller.
- Same banner is cropped differently across computer, mobile, and TV displays.

## Candidates

### A - Minimal Identity Field

- Lane: `minimal_identity_field`
- Strip: `assets/candidate_a_minimal_identity_field_visible_strip_2048x340.png`
- Upload wrapper: `assets/candidate_a_minimal_identity_field_upload_wrapper_2048x1152.png`
- Safe overlay preview: `previews/candidate_a_minimal_identity_field_upload_wrapper_safe_overlay_2048x1152.png`
- Notes: No title; relies on the approved circular CE profile icon outside the banner asset.

### B - Title Bearing Safe Area

- Lane: `title_bearing_safe_area`
- Strip: `assets/candidate_b_title_bearing_safe_area_visible_strip_2048x340.png`
- Upload wrapper: `assets/candidate_b_title_bearing_safe_area_upload_wrapper_2048x1152.png`
- Safe overlay preview: `previews/candidate_b_title_bearing_safe_area_upload_wrapper_safe_overlay_2048x1152.png`
- Notes: Exact title is composed locally with the installed Inter display font; no generated title text.

### C - Folded Cascade World

- Lane: `folded_cascade_world`
- Strip: `assets/candidate_c_folded_cascade_world_visible_strip_2048x340.png`
- Upload wrapper: `assets/candidate_c_folded_cascade_world_upload_wrapper_2048x1152.png`
- Safe overlay preview: `previews/candidate_c_folded_cascade_world_upload_wrapper_safe_overlay_2048x1152.png`
- Notes: Broad channel-world identity; no title and no episode-specific public anchor.

## QA

- Contact sheet: `qa/youtube-channel-banner-strip-candidates-contact-sheet.png`
- QA notes: `qa/qa_notes.md`
- Manifest: `manifest.json`

No YouTube Studio update was performed. No candidate is marked `keep`; Mike must explicitly approve one before promotion.
