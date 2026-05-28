# Titanic End Screen Handoff Repair

Date: 2026-05-20

## Issue

The rough-review player treated `end_screen_start_seconds = 759.613219` as the start of the visual fade. That value is the YouTube-safe final 20-second hold window, not the VO-to-outro music handoff. The result was a late end-screen entrance after the voice had already ended and the outro music had already risen.

## Repair

- Preserve the existing titleless YouTube placeholder layout.
- Keep the final 20-second safe window at `759.613219s`.
- Start the rail fade-out and end-screen fade-in at the actual outro prelap, `748.818004s`.
- Complete the handoff at the outro target level, `753.318004s`.
- Disable CSS opacity transitions on the end-screen layer so the fade is deterministic from the scripted timing state.

## QA Reads

- `end_screen_fade_start_read`: pass, fade begins at the actual outro prelap instead of the late safe-window boundary.
- `rail_fade_out_read`: pass, rail reaches zero opacity by the outro target level.
- `youtube_placeholder_fade_read`: pass, placeholders fade in during the VO/outro handoff and are fully visible before the final safe window.
- `youtube_safe_window_read`: pass, placeholders hold through the final 20-second window.
- `caption_fade_coupling_read`: pass, captions fade with the rail until voice end.

## Gate

This is a rough-review timing repair only. Ambient keep remains recorded, but rough assembly still requires explicit human `keep`. Final render, upload prep, YouTube action, and public release remain blocked.
