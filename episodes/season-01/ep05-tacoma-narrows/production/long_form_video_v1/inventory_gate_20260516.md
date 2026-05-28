# Tacoma Narrows Long-Form Video Inventory Gate

Date: 2026-05-16

Workflow: `long_form_video_production_v1`

Gate: `inventory`

Disposition: `keep_opened_by_user_approval`

Human selection signal: after reviewing the embedded pass-07 Tacoma Short candidate, the user said, "i approve - continue to long-form video production".

## Episode Identity

- Episode id: `tacoma-narrows`
- Canonical episode number: `05`
- Title: `Tacoma Narrows Bridge`
- Lane: `Design Failures / System Failures`
- Mechanism: `Unknown force domain / margin removed`
- Causal hook: `A slender bridge optimized for known forces met aeroelastic behavior the design had no language for.`
- Tiny detail: visible motion became spectacle before it became warning.

## Source Inventory

| Asset | Status | Path | SHA-256 |
| --- | --- | --- | --- |
| Locked long-form script | present | `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/Ep5_Tacoma-Narrows.txt` | `60c949d26a3abbd95ece31e9dc27ebb33fd967d4c9704e72fe23ad26ee938a84` |
| Long-form fact check | present | `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/fact_check.md` | `9b772a9420e0f9609e6eaf98c4840351ce94fb17c0466eb51db402a3e7fe09b4` |
| Long-form audio master | missing | `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/final/Ep5_Tacoma-Narrows.wav` | `missing` |
| Long-form transcript/timing source | missing | not set in `episodes/tacoma-narrows.toml` | `missing` |
| Visual research package | missing | `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/visual_research/` | `missing` |
| Brand design contract | present | `/Users/mike/Web_CascadeEffects/brand/contracts/design-system.contract.md` | `9d7d8870a63cd6ee0e95112abce451b9a792c4a135dedff18b9fae90aaf057ba` |
| Brand illustration contract | present | `/Users/mike/Web_CascadeEffects/brand/contracts/illustration.contract.md` | `42d324ad268170875d6499a856a007788dd11636964fd0a6f7a5eed9010aaaa0` |
| Living Cover system spec | present | `/Users/mike/Agents_CascadeEffects/references/skills/long_form_video_production_v1/references/living_cover_system_spec_v1.md` | `05c97e449dc97cffc13562ba581ff14ba3b85ea739882b2c327ee160774eb64e` |
| Approved Short bridge | keep | `/Users/mike/Viz_CascadeEffects/references/episodes/tacoma-narrows/shorts/tacoma_short_scoped_v1/motion_video_proof/pass_01_source_led/final_exports/tacoma-narrows_house_crt_clean_source_lineage_visible_scanline_first8_pass_07/20260429T_house_crt_visible_scanline_first8_pass07_y24/final/tacoma-narrows__house_crt_visible_scanline_signal_interruption_captioned_final.mp4` | `ebecebef84bde5e915d4b4927f655128712f17545d89a36ca19a260e992c9ded` |

## Inventory Reads

- `long_form_audio_status`: `missing`
- `existing_short_bridge_status`: `keep_pass07_crt_visible_scanline_publish_package_not_rebuilt`
- `outro_music_status`: `available_for_short; long_form_rights_and_mix_not_yet_packaged`
- `brand_asset_status`: `brand_contracts_present; episode_specific_long_form_source_art_not_yet_selected`
- `caption_status`: `blocked_missing_long_form_audio_timing_source`
- `chapter_status`: `draftable_from_locked_script; not timed`
- `thumbnail_status`: `todo`
- `rights_status`: `blocked_pending_long_form_source_inventory_rights_and_content_id_review`
- `publish_status`: `blocked_no_long_form_rough_proof_no_final_no_publish_readiness_package`

## Active Constraints

- The long-form video is the canonical episode; the kept Short is a bridge/discovery asset only.
- Do not treat archived, legacy, diagnostic, or old proof assets as active long-form visual inputs without an explicit reviewed import.
- Use the brand contracts and `living_cover_system_v1` before any visual-system plan.
- Captions are required by default using script-locked text and timing-only ASR/VTT/SRT provenance.
- The first long-form blocker is the missing long-form audio master and transcript/timing source.

## Next Gate

Next required gate: create or promote a current long-form voice master from the locked script, create transcript/timing provenance, then return to the Episode Package Gate for human review.

`may_advance_to_visual_system`: `false`
