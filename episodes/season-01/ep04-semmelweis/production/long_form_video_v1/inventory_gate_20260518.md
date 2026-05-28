# Semmelweis Long-Form Video Inventory Gate

Date: 2026-05-18

Workflow: `long_form_video_production_v1`

Gate: `inventory`

Disposition: `keep_opened_by_user_selection`

Human selection signal: after reviewing the first-eight order, the user said, "oh, let's do semelweis next".

## Episode Identity

- Episode id: `semmelweis`
- Canonical episode number: `04`
- Title: `Semmelweis and the Rejection of Handwashing`
- Lane: `One Decision Changed Everything`
- Mechanism: `Evidence rejected because identity is threatened`
- Causal hook: `Ignaz Semmelweis found that handwashing reduced maternal deaths, but accepting the result meant admitting doctors themselves had been causing harm.`
- Tiny detail: the data was visible before the institution could accept it.

## Source Inventory

| Asset | Status | Path | SHA-256 |
| --- | --- | --- | --- |
| Locked long-form script | present | `/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/Ep4_Semmelweis.txt` | `2bca08c0899da81a909d550a76dc0e2cb6ddccaa764b8c45ad9298c918276d68` |
| Long-form fact check | present | `/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/fact_check.md` | `e4adaa25f8b09b96c5f6c58c0758e7c476fc64b5b90b830e960fd71ee3663ace` |
| Long-form audio master | missing | `/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/final/Ep4_Semmelweis.wav` | `missing` |
| Long-form transcript/timing source | missing | not set in `episodes/semmelweis.toml` | `missing` |
| Long-form visual research package | missing | `/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/visual_research/` | `missing` |
| Brand design contract | present | `/Users/mike/Web_CascadeEffects/brand/contracts/design-system.contract.md` | `9d7d8870a63cd6ee0e95112abce451b9a792c4a135dedff18b9fae90aaf057ba` |
| Brand illustration contract | present | `/Users/mike/Web_CascadeEffects/brand/contracts/illustration.contract.md` | `42d324ad268170875d6499a856a007788dd11636964fd0a6f7a5eed9010aaaa0` |
| Living Cover system spec | present | `/Users/mike/Agents_CascadeEffects/references/skills/long_form_video_production_v1/references/living_cover_system_spec_v1.md` | `43cc34cfb9606c26ef1e6e6c0cbe7f04873e5059a90c5bc824167392c4269886` |
| Existing Short bridge | review candidate available | `/Users/mike/Viz_CascadeEffects/references/episodes/semmelweis/shorts/semmelweis_short_scoped_v1/motion_video_proof/pass_01d_head_in_hands_ending/final_exports/semmelweis_house_crt_clean_source_lineage_visible_scanline_first8_pass_07/20260429T_house_crt_visible_scanline_first8_pass07_y24/final/semmelweis__house_crt_visible_scanline_signal_interruption_captioned_final.mp4` | `6cebb48f70c77212868bd2bf49389ec4e8464541100350bf3d0c9b0213295876` |

## Inventory Reads

- `canonical_order_read`: `pass_episode_04_after_hyatt`
- `long_form_script_read`: `pass_locked_script_present`
- `long_form_fact_check_read`: `pass_fact_check_present`
- `long_form_audio_status`: `missing`
- `frontier_model_script_critique_read`: `missing`
- `critique_integration_read`: `missing`
- `human_script_approval_for_audio_read`: `missing`
- `audio_source_integrity_read`: `missing`
- `caption_status`: `blocked_missing_long_form_audio_timing_source`
- `existing_short_bridge_status`: `review_candidate_available_publish_package_not_current`
- `brand_asset_status`: `brand_contracts_present`
- `source_art_status`: `not_started_imagegen_required_by_default`
- `rights_status`: `blocked_pending_long_form_source_inventory_rights_and_content_id_review`
- `publish_status`: `blocked_no_audio_no_rough_proof_no_final_no_publish_readiness_package`

## Active Constraints

- The long-form video is the canonical episode; the Short path is a bridge/discovery surface only.
- Do not treat prior Semmelweis Short assets, archival clips, proof renders, or old visual experiments as active long-form inputs unless an exact file is imported by a scoped, reviewed manifest.
- Use ImageGen-generated `1920x1080` source art as the default long-form Living Cover backplate source unless a human-approved non-ImageGen exception is recorded.
- Captions are required by default using locked-script text and timing-only transcript provenance.
- Do not render, promote, or keep long-form voice audio until the exact script revision has frontier-model critique, critique integration or explicit deferral, and human approval for audio.

## Next Gate

Next required gate: complete the script/audio authorization path for the locked script, render or promote a current long-form voice master, create transcript/timing provenance, then return to the Episode Package Gate.

`may_advance_to_episode_package`: `false`

`may_advance_to_visual_system`: `false`

`may_youtube_action`: `false`
