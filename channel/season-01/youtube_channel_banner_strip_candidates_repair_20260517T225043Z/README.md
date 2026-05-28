# Cascade Effects YouTube Banner Repair Candidates

Status: `superseded_title_not_paper_architecture`

This package is superseded. It kept the researched YouTube constraints and rebuilt the creative direction from shallow-strip source art, but Mike clarified that the title should be in the banner and should be styled natively as Paper Architecture.

## Which Files Are Usable

- YouTube Studio upload candidates: `upload_candidates_2048x1152/*.png`
- Viewer-facing strip review assets: `visible_strips_2048x340/*.png`
- Do not use `qa/`, `previews/`, or `source/` files as final banners. Those are review, overlay, TV-preview, or provenance artifacts.

## Constraints

- Primary creative asset: `2048 x 340` visible strip.
- Upload wrapper: `2048 x 1152` for YouTube Studio compatibility.
- Optional TV preview wrappers: `2560 x 1440`, under `previews/` only.
- File-size limit: final upload wrappers under `6 MB`.
- No generated title text; Candidate B title is exact local text.
- No YouTube Studio update.

## Candidates

### A - Quiet Signal Band

- Lane: `minimal_identity_field`
- Strip: `assets/candidate_a_quiet_signal_band_visible_strip_2048x340.png`
- Upload wrapper: `assets/candidate_a_quiet_signal_band_upload_wrapper_2048x1152.png`
- Overlay preview: `previews/candidate_a_quiet_signal_band_upload_safe_overlay_2048x1152.png`
- Notes: Purpose-built shallow strip; quiet center, low folded signal band, no title.

### B - Exact Title Center

- Lane: `title_bearing_safe_area`
- Strip: `assets/candidate_b_exact_title_center_visible_strip_2048x340.png`
- Upload wrapper: `assets/candidate_b_exact_title_center_upload_wrapper_2048x1152.png`
- Overlay preview: `previews/candidate_b_exact_title_center_upload_safe_overlay_2048x1152.png`
- Notes: Exact deterministic local title over a quieter strip; no generated text.

### C - Channel World Edges

- Lane: `folded_cascade_world`
- Strip: `assets/candidate_c_channel_world_edges_visible_strip_2048x340.png`
- Upload wrapper: `assets/candidate_c_channel_world_edges_upload_wrapper_2048x1152.png`
- Overlay preview: `previews/candidate_c_channel_world_edges_upload_safe_overlay_2048x1152.png`
- Notes: Channel-world edge architecture with a large clean center; no title.

## Review

- Contact sheet: `qa/youtube-channel-banner-repair-candidates-contact-sheet.png`
- QA notes: `qa/qa_notes.md`
- Manifest: `manifest.json`

No candidate is `keep`; status remains `review_required`.
