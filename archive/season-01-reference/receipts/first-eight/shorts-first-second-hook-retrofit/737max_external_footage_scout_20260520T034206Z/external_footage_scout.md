# 737 MAX External Footage Scout

- `stage`: `external footage scout`
- `episode_id`: `Ep7_737-MAX`
- `short_id`: `737_max_short_scoped_v1`
- `created_at_utc`: `2026-05-20T034206Z`
- `local_review_only`: `true`
- `footage_downloaded_or_imported`: `false`
- `youtube_upload_publish_delete_replace_schedule_touched`: `false`
- `current_theme_hook_proof_read`: `tighten`
- `tighten_reason`: current hook proof leans too hard on repeated LEAP engine close-ups and needs stronger visual variety before another local proof rebuild.

## Scout Policy

- `archival_role`: `hybrid`
- `hygiene_rule`: `strict clean`
- `analog_look`: `selective`
- `source_breadth`: `1-3 primary archival videos plus up to 2 backups`
- `paper_architecture_visual_style_read`: `blocked_for_shorts`
- `caption_layer_policy`: `local_review_no_final_caption_rebuild`

Strict-clean means any visible logo, stinger, lower-third, watermark, burned caption, end card, split screen, or channel bug rejects that span. Crop or cleanup is not a fallback for this scout.

## Recommended Direction

Use a three-family pool instead of more engine close-ups:

1. Official FAA return-to-service/test-flight material for flight deck and certification context.
2. Cockpit or pilot-view flight material for runway roll, climb, and pilot workload.
3. Stock or clean exterior airport material only when the frame is actually clean and not generic plane wallpaper.

The next 737 proof should replace the opening hook and tail with a more varied subject/event span, then swap a few body slots away from engine repetition. Do not rebuild the whole short until these external candidates pass a clip-level audit.

## Primary Scout Pool

| source_id | title | source / URL | visual family | intended use | hygiene / rights read | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| `faa_dickson_737max_broll` | FAA Administrator Steve Dickson piloting the Boeing 737 MAX (B-ROLL) | FAA page with video link: https://www.faa.gov/newsroom/faa-administrator-completes-boeing-737-max-flight / video: https://www.youtube.com/watch?v=eozVpyoYaLM | Official test flight, flight deck, certification context | Best first candidate for varied hook or early body shots | Official source, but direct downloader returned unavailable in this environment; access and clean spans still need verification | `primary_scout_pending_access` |
| `pilot_view_737max_departure_toronto` | B737 MAX Turbulent Departure out of Toronto (FULL ATC) | Pilot View: https://www.youtube.com/watch?v=TTc66BPgdpQ | Cockpit departure, runway roll, climb, pilot POV | Strongest non-official motion variety if clean | Creator-rights risk high; cockpit overlays, channel marks, and instruments need strict-clean audit | `primary_scout_if_clean` |
| `pixabay_737max_stock_pool` | Pixabay Boeing 737 MAX video pool | https://pixabay.com/videos/search/boeing%20737%20max/ | Exterior aircraft, airport, ramp, approach, weather | Backup clean exterior texture or tail if exact clip is visually specific | License lane is friendlier, but many clips may be generic or logo-heavy; exact video must be selected and audited | `primary_scout_pool_refine_to_exact_clip` |

## Backup Pool

| source_id | title | source / URL | visual family | intended use | hygiene / rights read | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| `dfw_aviation_aa_737max_mia_takeoff` | American Airlines Boeing 737 MAX 8 takeoff from Miami | DFW Aviation: https://www.youtube.com/watch?v=07yx-aUvN_4 | Passenger/window or exterior takeoff | Exterior subject motion, possible brief bridge away from cockpit | Creator-rights risk high; airline branding/tails likely need rejection by span | `backup_scout` |
| `dfw_aviation_southwest_lga_engine_view` | Southwest Airlines 737 MAX 8 takeoff from LaGuardia | DFW Aviation: https://www.youtube.com/watch?v=HsNDNXFXFys | Passenger-window engine and departure | Only use if it solves a transition or tail without repeating the current engine lane | Still engine-led, so use sparingly; logos and cabin marks need audit | `backup_scout_limited` |
| `just_planes_lhr_pilot_briefing` | Boeing 737MAX into London Heathrow + Pilot Landing Briefing | Just Planes: https://www.youtube.com/watch?v=SSz9E4mDRjw | Cockpit briefing, landing, flight deck | Strong cockpit variety if rights and clean spans pass | Rights risk high; likely branding/production marks; audit before any import | `backup_scout` |
| `pexels_newark_737max_rain_gate` | United 737 MAX at Newark gate in thunderstorm | Pexels: https://www.pexels.com/video/as-thunder-and-lightning-rumble-through-the-skies-a-torrential-downpour-engulfs-a-gate-at-newark-airport-causing-airplanes-including-a-united-airlines-boeing-737-max-to-patiently-await-16954669/ | Rainy gate, aircraft waiting, airport atmosphere | Possible texture/tail option if clean and not too generic | Stock-license lane, but visible airline branding likely makes many spans strict-clean rejects | `backup_scout_exact_span_required` |
| `boeing_demo_flight_2016` | Boeing 737 MAX flight demonstration video | Boeing/news references: https://www.sfgate.com/business/boeing/article/Watch-Boeing-shows-off-737-MAX-in-new-demo-8425451.php | High-energy exterior flight display | Possible high-impact subject footage if original source is found | Manufacturer promotional source; original URL and rights/clean spans need separate audit | `backup_research_reference` |
| `flightdeck2sim_stab_trim_override` | Boeing 737 stab trim override demonstration | flightdeck2sim: https://www.youtube.com/watch?v=1RrLEl00HTM | Mechanism demonstration, stabilizer trim controls | Support-only mechanism insert if MAX-specific footage fails | Not exact MAX subject footage; use as teaching reference only unless DP approves nonliteral support | `backup_reference_only` |

## Reject / Avoid

| source_id | source / URL | reject reason |
| --- | --- | --- |
| `vox_real_reason_737max` | https://www.youtube.com/watch?v=H2tuKiiznsY | Explainer/editing/text graphics; useful for research context, not clean source motion. |
| `news_package_family` | KING 5, NBC, PBS, Reuters, Global, CNBC returns from the scout | Lower-thirds, anchors, studio graphics, channel bugs, and edited news framing are too risky for strict-clean source motion. |
| `simulator_msfs_family` | Multiple search returns | Simulator/MSFS footage is not the real aircraft/event lane and should not replace source-led footage. |
| `crash_spectacle_family` | Any accident wreckage or sensational crash compilation | Wrong tone for this proof and likely hygiene/rights failures. |

## Search Notes

Searches covered YouTube, official FAA/Boeing references, Pixabay, Pexels, and generic web search for cockpit, test-flight, takeoff, stabilizer/MCAS, angle-of-attack, and b-roll terms. `yt-dlp` metadata lookup confirmed usable metadata for the creator candidates above; the official FAA YouTube video is still linked from the FAA page but returned unavailable to `yt-dlp` in this environment, so it stays pending access.

## Handoff

- `may_inform_next_local_hook_rebuild`: `true`
- `may_lock_visual_beatmap`: `false`
- `may_download_or_import_without_clip_audit`: `false`
- `next_action`: exact-span audit for the FAA B-roll first; if unavailable, audit Pilot View cockpit/departure plus one exact stock/exterior clip. Then rebuild a local-only 737 proof with fewer engine repeats.
