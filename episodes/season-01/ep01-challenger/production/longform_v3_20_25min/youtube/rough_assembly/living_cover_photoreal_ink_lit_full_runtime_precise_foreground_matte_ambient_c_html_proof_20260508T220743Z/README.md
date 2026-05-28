# Challenger Living Cover Precise Foreground Matte Ambient C HTML Proof

Status: `tighten`.

Review-only full-runtime HTML proof repairing the ambient foreground occlusion mask.

This packet preserves the approved lights-on backplate, fixed `1920x1080` canvas, 760px right rail, native 40px WebVTT rail captions, staged rail transitions, approved audio/caption/transcript references, and range-capable review controls.

## What Changed

- Replaces the broad image-derived sky mask with a precise backplate foreground matte.
- Keeps the right rail out of the matte asset; rail/caption occlusion remains a render-layer concern.
- Uses the matte only for ambient aircraft and dust occlusion; it is not a visible video layer.
- Keeps aircraft as distant point lights and clips them behind the tower, shuttle, launch pad, crew, ground, and foreground structures.

Mask QA:

- `qa/foreground_matte_black_white.png`: white means open sky where ambient effects may render; black means foreground occluder.
- `qa/open_sky_allowed_overlay.png`: cyan indicates open sky.
- `qa/foreground_occlusion_overlay.png`: red indicates blocked foreground.
- `qa/foreground_matte_edge_registration.png`: matte edge over the source plate.

Open:

- `http://127.0.0.1:8796/player.html`

No MP4 render, final assembly, Shorts work, publish readiness, or YouTube action is authorized by this packet.

## Tighten Note

Human review: an airplane should enter sooner, within roughly the first 20 seconds. This packet is superseded by the early-aircraft timing repair.

## Disposition Update

- Human disposition: `tighten`.
- Human feedback: aircraft still pass in front of the shuttle foreground. Root cause recorded as coordinate mismatch: the visible source plate was scaled/drifted while the foreground matte and ambient canvas were evaluated in raw 1920x1080 coordinates.
- Downstream render/final/Shorts/publish/YouTube gates remain locked.
