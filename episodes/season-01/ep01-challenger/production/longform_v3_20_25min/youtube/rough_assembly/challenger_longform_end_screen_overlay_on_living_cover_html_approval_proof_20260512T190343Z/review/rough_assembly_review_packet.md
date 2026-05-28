# Challenger End-Screen Overlay Review

Player: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/challenger_longform_end_screen_overlay_on_living_cover_html_approval_proof_20260512T190343Z/player.html`

Local review URL: `http://127.0.0.1:8818/player.html`

Manifest: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/challenger_longform_end_screen_overlay_on_living_cover_html_approval_proof_20260512T190343Z/rough_assembly_manifest.json`

## What Changed

- Removed the separate Paper Architecture outro plate from the end-screen layer.
- Made the end-screen layer transparent so the Challenger long-form `sourcePlate` and ambient canvas stay visible.
- Kept the right rail fade: the rail fades out as the YouTube template fades in.
- Kept captions suppressed once the outro transition begins at `1214.763537s`.
- Kept the existing trailer-template target geometry:
  - left video: `[78, 382, 758, 765]`
  - right video: `[1162, 382, 1842, 765]`
  - center subscribe: center `[960, 575]`, radius `146`, bbox `[814, 429, 1106, 721]`
- Froze the Living Cover background at the story end for stable final safe-window review.
- Preserved audio, captions, chapters, matte, dust pacing, aircraft, intro music fade, and outro music.
- No MP4 was rendered.

## QA Reads

- Browser QA: `pass`
- Right rail fade: `pass`
- Transparent overlay fade: `pass`
- Separate outro plate: `pass_removed`
- Challenger long-form background visible: `pass`
- Background freeze for safe window: `pass`
- Caption suppression during outro: `pass`
- YouTube target bounds/aspect: `pass`
- Final 20s stability: `pass`
- Audio scrubber seek: `pass`
- Byte-range server: `pass`

QA file: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/challenger_longform_end_screen_overlay_on_living_cover_html_approval_proof_20260512T190343Z/qa/browser/end_screen_overlay_on_living_cover_browser_qa_20260512T190343Z.json`

## Review Focus

- Does the end screen now feel like an overlay on the existing Challenger long-form screen?
- Does the right rail disappear cleanly without swapping to the old Paper Architecture outro scene?
- Do the video targets, subscribe target, and title feel balanced on the Challenger long-form background?
- Do captions stay suppressed during the music-only outro?
- Do playback and timeline scrubbing still work?

Please review the HTML proof and reply with exactly one disposition: `keep`, `tighten`, or `reject`.
