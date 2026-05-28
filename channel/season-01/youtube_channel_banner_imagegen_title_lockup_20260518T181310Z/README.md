# Cascade Effects YouTube Banner - ImageGen Title Lockup Repair

Status: `review_required`

This package implements the controlled ImageGen title-lockup experiment Mike requested. It uses Candidate B as the clean negative-space base, accepts one exact-spelling generated title lockup, removes the chroma background locally, and composites the title into the visible YouTube banner strip.

## Usable Files

- Visible strip: `visible_strips_2048x340/candidate_b_imagegen_title_lockup_visible_strip_2048x340.png`
- Upload wrapper: `upload_candidates_2048x1152/candidate_b_imagegen_title_lockup_upload_wrapper_2048x1152.png`

## Review Files

- Title candidates contact sheet: `qa/title-lockup-candidates-contact-sheet.png`
- Safe-area overlay: `previews/candidate_b_imagegen_title_lockup_strip_safe_overlay_2048x340.png`
- Upload overlay: `previews/candidate_b_imagegen_title_lockup_upload_safe_overlay_2048x1152.png`
- Website-title comparison: `qa/website-hero-title-comparison.png`
- QA notes: `qa/qa_notes.md`

## Decision State

- Previous procedural faceted-title repair is superseded and marked `rejected_title_render_mismatch`.
- This package is not `keep`.
- No YouTube Studio update was performed.
