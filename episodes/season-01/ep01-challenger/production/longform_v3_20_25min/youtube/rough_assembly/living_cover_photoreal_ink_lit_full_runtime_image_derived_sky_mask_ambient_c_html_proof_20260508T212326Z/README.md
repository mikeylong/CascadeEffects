# Challenger Living Cover Image-Derived Sky Mask Ambient C HTML Proof

Status: `tighten`.

Review-only full-runtime HTML proof repairing the previous sky mask.

This packet preserves the single lights-on backplate, fixed `1920x1080` canvas, 760px right rail, native 40px WebVTT rail captions, staged rail transitions, approved audio/caption/transcript references, and range-capable review controls.

## What Changed

- Replaces the rough geometric sky mask with an image-derived visible-sky mask built from the source plate.
- Uses the mask only for ambient occlusion; it is not a visible video layer.
- Keeps aircraft as distant point lights and clips them to the actual visible-sky mask.
- Keeps sparse localized dust motion within the same visible-sky/light-falloff area.

Mask QA:

- `qa/sky_allowed_overlay.png`: cyan indicates visible sky where ambient effects may render.
- `qa/foreground_blocked_overlay.png`: red indicates blocked foreground/rail-safe area.
- `qa/sky_mask_edge_registration.png`: mask edge over the source plate.

## Tighten Note

Human review found this mask still behaves like a broad sky heuristic. The next packet replaces it with a precise foreground matte for the backplate only: tower, shuttle, launch pad, crawlerway, crew, ground, lights, and foreground details are occluders; the right rail is not part of the matte asset.

Open:

- `http://127.0.0.1:8795/player.html`

No MP4 render, final assembly, Shorts work, publish readiness, or YouTube action is authorized by this packet.
