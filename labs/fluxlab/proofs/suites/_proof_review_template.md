# Proof Review Template

Use this note shape for every still, motion, and reel review.

Keep field names unchanged so future automation can parse them.

Shared disposition vocabulary:

- `keep`
- `tighten`
- `diagnostic only`
- `reject`

## Still Review Block

### `<case_id>`

- `review_type`: `still`
- `gate_level`: `still`
- `episode_id`:
- `case_id`:
- `archetype`:
- `source_asset`:
- `report_path`:
- `artifact_path`:
- `motion_carrier`:
- `source_baked_issue`: `false`
- `disposition`:
- `failure_reason`:
- `next_action`:
- `review_note`:

## Motion Review Block

### `<case_id>`

- `review_type`: `motion`
- `gate_level`: `motion`
- `episode_id`:
- `case_id`:
- `archetype`:
- `source_asset`:
- `staged_asset`:
- `video_manifest`:
- `artifact_path`:
- `motion_carrier`:
- `source_baked_issue`: `true|false`
- `disposition`:
- `failure_reason`:
- `next_action`:
- `review_note`:

## Reel Review Block

### `<reel_id>`

- `review_type`: `reel`
- `gate_level`: `reel`
- `episode_id`: `multi`
- `case_id`: `multi`
- `archetype`: `multi`
- `source_asset`:
- `artifact_path`:
- `motion_carrier`: `multi`
- `source_baked_issue`: `mixed|false`
- `disposition`:
- `failure_reason`:
- `next_action`:
- `review_note`:

Included clip record:

- `clip_case_id`:
- `clip_disposition`:
- `clip_path`:
- `clip_note`:
