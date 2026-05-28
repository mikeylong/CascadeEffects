# 737 MAX Clean Source Scout Pass 02

- `stage`: `external footage scout`
- `scout_focus`: `clean_text_graphics_free_sources`
- `episode_id`: `Ep7_737-MAX`
- `short_id`: `737_max_short_scoped_v1`
- `created_at_utc`: `2026-05-20T040002Z`
- `local_review_only`: `true`
- `footage_downloaded_or_imported`: `false`
- `youtube_upload_publish_delete_replace_schedule_touched`: `false`
- `strict_clean_rule`: reject spans with lower-thirds, burned captions, channel bugs, watermarks, title cards, logos used as overlays, split screens, end cards, or explanatory graphics.

## Clean-Likely Sources To Audit First

| priority | source_id | source / URL | why it is worth auditing | clean risk | intended 737 proof use |
| --- | --- | --- | --- | --- | --- |
| 1 | `boeing_first_flight_media_portal` | Boeing press release: https://boeing.mediaroom.com/2016-01-29-Boeing-Completes-Successful-737-MAX-First-Flight?asPDF=1, video download link redirects to `http://bcacom.navigon.net/data/public/62c142352472a576a5efccbf05d3ad14.php?lang=en` | Official first-flight video package from Boeing; likely has air-to-air, takeoff, and landing material that is more subject/event-led than engine close-ups. | May include intro/end branding or embedded PR title cards; exact span audit required. | Best candidate for a new opening hook or final tail if clean windows exist. |
| 2 | `boeing_first_flight_youtube` | Boeing: https://www.youtube.com/watch?v=k82e08kdKyw | Official Boeing first-flight video, short enough to audit quickly. | Possible title card/logo at head/tail; use only raw flight windows. | Backup to the Boeing media portal if portal asset is awkward to retrieve. |
| 3 | `faa_dickson_737max_broll` | FAA page: https://www.faa.gov/newsroom/faa-administrator-completes-boeing-737-max-flight, video: https://www.youtube.com/watch?v=eozVpyoYaLM | Official FAA B-roll; strongest path for cockpit/test-flight/certification context without news graphics. | `yt-dlp` returned unavailable locally; access still needs manual/browser or alternate retrieval check. | Flight deck/body variety, not engine repetition. |
| 4 | `pexels_3678391_montreal_taxi` | https://www.pexels.com/video/passenger-planes-taxiing-on-the-airport-runway-3678391/ | Stock footage page describes a Boeing 737 taxiing at sunset; no editorial graphics in source page preview/description. | Airline markings may appear; exact frame audit required for strict-clean branding policy. | Exterior airport/taxi bridge, useful before/after narration body rather than hook. |
| 5 | `pexels_16954669_newark_rain_gate` | https://www.pexels.com/video/as-thunder-and-lightning-rumble-through-the-skies-a-torrential-downpour-engulfs-a-gate-at-newark-airport-causing-airplanes-including-a-united-airlines-boeing-737-max-to-patiently-await-16954669/ | Atmospheric stock clip explicitly identifies a United 737 MAX in storm/rain; visually different from engine close-ups. | Airline branding likely visible; maybe too moody/generic if aircraft is small. | Tail or transition texture if exact clean span works. |
| 6 | `pixabay_47339_airport_departure` | https://pixabay.com/videos/airport-planes-departure-traffic-47339/ | Free 4K MP4, 0:44, airport departure/runway traffic with no page-level sign of graphics overlay. | Generic airport; aircraft logos may be visible; not guaranteed MAX. | Clean exterior motion filler only if exact MAX specificity is not required for that slot. |
| 7 | `pixabay_283_airport_runway_rain` | https://pixabay.com/videos/airport-runway-airplanes-283/ | Free MP4, rainy runway/airliner motion; no graphics source type. | Generic and old 1080p; not MAX-specific. | Weather/pressure texture or bridge, not hero source. |
| 8 | `pixabay_144323_engine_mechanism` | https://pixabay.com/videos/engine-airplane-aircraft-motor-144323/ | Free 4K MP4, rotating Boeing 737 engine, clean stock-style mechanism insert. | This is still an engine close-up, so it should be used sparingly or not at all unless a mechanism slot needs it. | Low-priority mechanism insert only. |

## Conditional YouTube Candidates

These are not first-choice because creator/trip-report videos often include title cards, intros, channel marks, or in-cabin clutter. They may still contain clean raw windows after audit.

| source_id | source / URL | reason to keep in reserve | clean risk | verdict |
| --- | --- | --- | --- | --- |
| `pilot_view_737max_departure_toronto` | https://www.youtube.com/watch?v=TTc66BPgdpQ | Real 737 MAX cockpit/departure POV with strong motion variety. | Creator video; cockpit displays/overlays/channel marks need dense audit. | `reserve_exact_span_audit` |
| `first_we_fly_737max9_dulles_landing` | https://www.youtube.com/watch?v=t7bf0vamHAg | Short, direct landing sequence on a MAX 9. | Creator source; likely cleaner than trip reports but still needs overlay check. | `reserve_exact_span_audit` |
| `ninemilesup_737max_cold_dark_startup` | https://www.youtube.com/watch?v=FOxC09IZmDE | Cockpit startup texture without relying on engine exterior. | Must verify real aircraft, no overlays, and not simulator/training abstraction. | `reserve_exact_span_audit` |
| `boeing_chief_pilot_flying_display` | https://www.youtube.com/watch?v=aFYmY3j0dKU | Official Boeing flight-display perspective; more dynamic than static engine shots. | Likely interview/editorial framing; only raw aircraft windows are eligible. | `reserve_official_raw_windows_only` |
| `airboyd_737max_flight_demonstration` | https://www.youtube.com/watch?v=jzScMM-ka44 | Long upload of Boeing flight demonstration material. | Repost/source-chain risk and possible channel branding. | `backup_if_official_source_unavailable` |

## Reject For This Request

- Trip reports with title cards or on-screen route labels unless an exact clean window is proven.
- News packages and explainer videos, including Vox-style explainers, because they are graphics/text led.
- Simulator/MSFS videos.
- Crash compilations or disaster spectacle.
- More LEAP-engine-only close-ups as hook/tail material.

## Recommended Audit Order

1. Try the Boeing media portal video from the press release and pull a frame strip before any import.
2. If that is not clean enough, audit Boeing official YouTube first-flight and FAA B-roll.
3. Use Pexels/Pixabay stock only for bridge/tail variety, not as the main causal hook unless the aircraft is clearly readable.
4. Keep one cockpit/departure creator video in reserve, preferably Pilot View or First We Fly, but only after exact-span strict-clean proof.

## Handoff

- `may_inform_next_local_hook_rebuild`: `true`
- `may_download_or_import_without_clip_audit`: `false`
- `recommended_next_action`: audit Boeing first-flight media portal and FAA B-roll with frame strips, then choose one official hook source plus one clean exterior/tail source.
- `disposition`: `diagnostic only`
