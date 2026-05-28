# Titanic Rough Assembly Review Packet

Episode: `titanic`

Workflow: `long_form_video_production_v1`

Packet: `titanic_living_cover_html_rough_proof_candidate_e_boat_deck_weather_readiness_20260519T210834Z`

Status: `keep_end_screen_handoff_repair_approved_for_final_render`

Review URL: `http://127.0.0.1:8871/player.html`

Ambient review URL: `http://127.0.0.1:8871/player.html?ambientReview=1`

## Scope

This is the first rough assembly proof after Candidate E motion-readiness keep. It is an HTML review proof, not a final MP4, not upload prep, and not a publish-readiness package.

## Included

- Candidate E source-art backplate as a package-local asset.
- Browser-playable review audio mix with music-only intro, kept Titanic voice, and full outro using the kept music integration contract.
- Native player scrubber through the browser audio control.
- Script-locked rail captions from the offset VTT sidecar.
- Fixed `fixed_16x9_right_rail_v1` rail with the repaired punctuation rule: title, context, and rail-caption suppress terminal periods; `active-summary` may use sentence punctuation.
- Restrained ambient layer samples from the kept ambient/effects contract: practical lamp micro-life, wet deck shimmer, rope/fall tension, and sea/dawn air.
- Deck-light flicker now uses the ImageGen attempt 01 lights-off plate as the stable full-frame base, with the lights-on plate revealed only through a canvas compositor clipped by per-light hard-step cast masks and the packet-local ship/deck/people matte.
- `restrained_distress_v2` reduces the previous busy flicker into mostly steady lamps with sparse deterministic off-dropouts, a review-mode cap of two simultaneous off lamps, and a normal-playback cap of one.
- Ship-matte diagnostic proof: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/youtube/rough_assembly/titanic_living_cover_html_rough_proof_candidate_e_boat_deck_weather_readiness_20260519T210834Z/qa/ship_matte_light_cast/reference.html`
- Challenger/Therac titleless three-target end-screen geometry.
- End-screen handoff repair: the rail now fades out and the YouTube placeholders fade in from `748.818004s` to `753.318004s`, matching the VO/outro handoff instead of waiting until the final 20-second safe window at `759.613219s`.

## Ambient Keep

Human ambient disposition: `keep`

Receipt: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/youtube/rough_assembly/titanic_living_cover_html_rough_proof_candidate_e_boat_deck_weather_readiness_20260519T210834Z/review/human_ambient_keep_restrained_distress_v2_20260520.md`

Scope: ambient/light behavior only. Full rough-assembly keep is still pending.

## Ship-Matte Light-Cast Repair

- Compositor version: `ship_matte_canvas_light_cast_v1`
- Stable base: lights-off ImageGen attempt 01 plate
- Revealed source: lights-on ImageGen attempt 01 plate
- Clip matte: `ship_deck_people_matte_1920x1080.png`, covering ship structure, davits, rigging, lifeboats, people, wet deck, railings, and lamp-cast surfaces only
- Browser probe: open sky, ocean, horizon, and right-rail negative-space canvas alpha samples returned `0`; lamp-origin samples returned active overlay pixels
- Flicker behavior: deterministic sparse off-dropout schedules, independent hard-step on/off states, no CSS transition or slow fade, trimmed review-mode mask radius/alpha

## End Screen Handoff Repair

- Repair note: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/youtube/rough_assembly/titanic_living_cover_html_rough_proof_candidate_e_boat_deck_weather_readiness_20260519T210834Z/review/end_screen_handoff_repair_20260520.md`
- QA JSON: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/youtube/rough_assembly/titanic_living_cover_html_rough_proof_candidate_e_boat_deck_weather_readiness_20260519T210834Z/qa/end_screen_handoff_repair/end_screen_handoff_qa.json`
- Contact sheet: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/youtube/rough_assembly/titanic_living_cover_html_rough_proof_candidate_e_boat_deck_weather_readiness_20260519T210834Z/qa/end_screen_handoff_repair/end_screen_handoff_contact_sheet.png`
- Timing: rail fade-out and placeholder fade-in start at the outro prelap (`748.818004s`) and complete when the outro reaches target level (`753.318004s`). The final safe end-screen window remains `759.613219s` through `779.613219s`.
- Gate boundary: the repair itself was timing-only; the rough proof now has a separate human keep receipt.

## Rough Assembly Keep

- Human disposition: `keep`
- Receipt: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/youtube/rough_assembly/titanic_living_cover_html_rough_proof_candidate_e_boat_deck_weather_readiness_20260519T210834Z/review/human_rough_assembly_keep_end_screen_handoff_20260520.md`
- Scope: final MP4 render creation is opened from this kept HTML proof only.

## Gate Boundary

Human `keep` on this rough proof opens final assembly render work only. Publish readiness, upload prep, YouTube action, and public release remain blocked.
