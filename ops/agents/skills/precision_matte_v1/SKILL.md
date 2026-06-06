---
name: "precision_matte_v1"
description: "Apply Cascade Effects precision matte approval rules for foreground, subject, object, occlusion, cutout, and compositing masks before viewer-facing output."
---

# Precision Matte v1

Use this skill whenever Cascade Effects creates, imports, repairs, approves, validates, or exports a foreground, subject, object, occlusion, cutout, or compositing mask for thumbnails, packaging, workbench/Vision masks, subject-reference plates, long-form ambient effects, Shorts motion, or any viewer-facing composite.

## Contract

- Raw/imported/generated masks are `proposal_only`.
- Approved masks must use `precision_matte_v1`: inward choke `2px`, feather `0.75px`, with a `1px` choke allowed only when a recorded thin-detail reason proves `2px` damages rails, cables, tower detail, or equivalent fine structure.
- Viewer-facing composites must reference the repaired matte path, never the raw mask.
- The repaired matte must contain intermediate alpha values; a binary-only approved mask fails.
- Diagnostic masks, debug overlays, route masks, matte previews, and QA masks may exist, but they must not be the final compositing alpha.

## Receipt Fields

Each approved matte needs a receipt with:

- raw mask path and SHA
- repaired mask path and SHA
- choke px, feather px, and fallback reason when not using `2px`
- alpha-level count before/after and intermediate-alpha QA
- before/after edge crop proof path and SHA
- final composite path and SHA for viewer-facing exports

## Validation

Run `bin/ce validate-precision-matte --receipt PATH` for approval receipts and `bin/ce validate-precision-matte --manifest PATH` for final/export manifests. Final manifests must carry a precision matte receipt path and must fail when they reference raw masks directly.

Historical archive artifacts remain audit-only unless rebuilt or repaired under this contract.
