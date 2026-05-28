# Challenger Long-Form Continuous Ambient End-Screen Proof

Successor proof created `20260515T064720Z` from `challenger_longform_end_screen_overlay_script_locked_captions_html_approval_proof_20260515T062005Z`.

This packet keeps the script-locked caption fix and changes the end-screen clocking only: the story/rail/caption clock clamps at `1214.763537s`, while the ambient Living Cover clock continues through the full runtime so aircraft, dust, beacon, and practical-light motion remain active behind the static YouTube end-screen placeholder.

Review URL: <http://127.0.0.1:8818/player.html>

No MP4 was rendered from this successor. Publish/upload flags remain false until human review and final render QA pass.

# Challenger Long-Form Script-Locked Caption Successor

This review-only successor replaces only the caption assets and caption references. Audio, visuals, chapters, matte, dust pacing, aircraft, intro music fade, outro music, and transparent end-screen overlay behavior are preserved from the predecessor.

- Local review URL: `http://127.0.0.1:8818/player.html`
- Render-mode review URL: `http://127.0.0.1:8818/player.html?render=1`
- Review server: run `python3 scripts/range_review_server.py --host 127.0.0.1 --port 8818 --directory .` from this packet root.
- Predecessor proof: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/challenger_longform_end_screen_overlay_on_living_cover_html_approval_proof_20260512T190343Z`
- Locked script text source: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/audio/recording_20260511T204835Z_hybrid_attention_rewrite/scripts/challenger_longform_hybrid_attention_rewrite_20260511T204835Z.txt`
- Timing source: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/audio/recording_20260511T204835Z_hybrid_attention_rewrite/transcripts/recording_20260511T204835Z_hybrid_attention_rewrite.diarized.corrected.vtt`
- Script-locked rail VTT: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/challenger_longform_end_screen_overlay_script_locked_captions_html_approval_proof_20260515T062005Z/assets/captions/recording_20260511T204835Z_hybrid_attention_rewrite.script_locked_rail_safe.offset_intro_9s601.vtt`
- YouTube sidecar VTT: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/challenger_longform_end_screen_overlay_script_locked_captions_html_approval_proof_20260515T062005Z/references/recording_20260511T204835Z_hybrid_attention_rewrite.script_locked_rail_safe.vtt`
- Caption QA: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/challenger_longform_end_screen_overlay_script_locked_captions_html_approval_proof_20260515T062005Z/qa/captions/script_locked_caption_qa.json`
- Regression fixture: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/challenger_longform_end_screen_overlay_script_locked_captions_html_approval_proof_20260515T062005Z/qa/captions/challenger_too_weak_regression_fixture.json`

## What Changed

- Rebuilt rail-safe VTT/SRT and sidecar VTT/SRT from the locked narration script.
- Used the timed VTT only for timing; ASR words are not used as output caption text.
- Recorded script/timing path hashes, alignment coverage, and script/text match reads in the manifest.
- Verified the historical bug cue around `00:01:22.554` displays `too weak`, not `two weeks`.

No MP4 was rendered. Gates remain closed: `human_disposition: defer`, `may_create_full_runtime_mp4_render: false`, `may_advance_to_final_assembly: false`, `may_advance_to_publish_readiness: false`, `may_youtube_action: false`.

# Challenger Long-Form End-Screen Overlay On Living Cover

This review-only successor fixes the prior trailer-template end screen by removing the separate Paper Architecture outro plate. The YouTube end-screen template now fades in as a transparent overlay on top of the existing Challenger long-form screen while the right rail fades out.

- Local review URL: `http://127.0.0.1:8818/player.html`
- Render-mode review URL: `http://127.0.0.1:8818/player.html?render=1`
- Review server: run `python3 scripts/range_review_server.py --host 127.0.0.1 --port 8818 --directory .` from this packet root.
- Predecessor proof: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/challenger_longform_trailer_template_end_screen_html_approval_proof_20260512T182549Z`
- Correction: no separate `outro-plate`; the existing long-form `sourcePlate` and ambient canvas remain visible under the end-screen overlay.

Target geometry:

- Left video target: `[78, 382, 758, 765]`
- Right video target: `[1162, 382, 1842, 765]`
- Center subscribe target: center `[960, 575]`, radius `146`, bbox `[814, 429, 1106, 721]`

No MP4 was rendered. Gates remain closed: `human_disposition: defer`, `may_create_full_runtime_mp4_render: false`, `may_advance_to_final_assembly: false`, `may_advance_to_publish_readiness: false`, `may_youtube_action: false`.

# Challenger Long-Form Trailer-Template End Screen

This review-only successor preserves the intro music fade-tail proof and replaces only the outro/end-screen composition with the channel-trailer template approach: two video targets plus one centered subscribe target. The right rail still fades out as the end-screen template fades in.

- Local review URL: `http://127.0.0.1:8818/player.html`
- Render-mode review URL: `http://127.0.0.1:8818/player.html?render=1`
- Review server: run `python3 scripts/range_review_server.py --host 127.0.0.1 --port 8818 --directory .` from this packet root.
- Predecessor proof: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_shuttle_stack_reference_variant_a_full_runtime_hybrid_attention_rewrite_music_only_intro_outro_outro_screen_literal_rail_captions_precise_matte_visibility_repair_dust_pacing_tune_intro_music_fade_tail_html_approval_proof_20260512T175024Z`
- Trailer reference package: `/Users/mike/Episodes_CascadeEffects/Channel_Trailer/channel_trailer_v2_theme_song_no_vo_opening_montage_6s_near_camera_gallery_badges_corrected_bass_drum_breath_20260512T175730Z`
- Browser QA: `qa/browser/trailer_template_end_screen_browser_qa_20260512T182549Z.json`

Target geometry:

- Left video target: `[78, 382, 758, 765]`
- Right video target: `[1162, 382, 1842, 765]`
- Center subscribe target: center `[960, 575]`, radius `146`, bbox `[814, 429, 1106, 721]`

No MP4 was rendered. Gates remain closed: `human_disposition: defer`, `may_create_full_runtime_mp4_render: false`, `may_advance_to_final_assembly: false`, `may_advance_to_publish_readiness: false`, `may_youtube_action: false`.

# Challenger Long-Form Intro Music Fade Tail

This review-only successor preserves the dust-pacing visual proof and replaces only the browser review audio mix so the intro music fades under the first two seconds of VO instead of cutting at the voice start.

- Local review URL: `http://127.0.0.1:8818/player.html`
- Debug review URL: `http://127.0.0.1:8818/player.html?debug=1`
- Review server: run `python3 scripts/range_review_server.py --host 127.0.0.1 --port 8818 --directory .` from this packet root.
- Predecessor proof: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_shuttle_stack_reference_variant_a_full_runtime_hybrid_attention_rewrite_music_only_intro_outro_outro_screen_literal_rail_captions_precise_matte_visibility_repair_dust_pacing_tune_html_approval_proof_20260512T172711Z`
- New review WAV: `assets/audio/challenger_longform_hybrid_attention_rewrite_20260511T204835Z_intro_music_fade_tail_review_mix.wav`
- New browser MP3: `assets/audio/challenger_longform_hybrid_attention_rewrite_20260511T204835Z_intro_music_fade_tail_web_review.mp3`
- Audio transition: voice starts unchanged at `9.601451s`; intro music fades under VO until `11.601451s`.

No MP4 was rendered. Gates remain closed: `human_disposition: defer`, `may_create_full_runtime_mp4_render: false`, `may_advance_to_final_assembly: false`, `may_advance_to_publish_readiness: false`, `may_youtube_action: false`.

# Challenger Long-Form Dust Pacing Tune

This review-only successor keeps the precise matte, aircraft, audio, captions, chapters, outro, and shell unchanged while tuning the deterministic dust layer for lower quantity and faster movement.

- Local review URL: `http://127.0.0.1:8818/player.html`
- Debug review URL: `http://127.0.0.1:8818/player.html?debug=1`
- Review server: run `python3 scripts/range_review_server.py --host 127.0.0.1 --port 8818 --directory .` from this packet root. This serves MP3 byte ranges so the native audio timeline scrubber can seek reliably.
- Predecessor proof: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_shuttle_stack_reference_variant_a_full_runtime_hybrid_attention_rewrite_music_only_intro_outro_outro_screen_literal_rail_captions_precise_matte_visibility_repair_html_approval_proof_20260512T163537Z`
- Dust baseline: `92` generated motes, `59-66` visible in prior browser QA.
- Dust successor: `46` generated motes, movement speed multiplier `2.25x`, target `28-38` visible motes in browser QA.
- Dust pacing QA: `qa/browser/dust_pacing_tune_20260512T172711Z.json`

No MP4 was rendered. Gates remain closed: `human_disposition: defer`, `may_create_full_runtime_mp4_render: false`, `may_advance_to_final_assembly: false`, `may_advance_to_publish_readiness: false`, `may_youtube_action: false`.

# Challenger Long-Form Precise Matte Visibility Repair

This review-only successor replaces the broad tight matte with an image-derived precise foreground matte and restores aircraft/dust visibility for HTML review.

- Local review URL: `http://127.0.0.1:8818/player.html`
- Debug review URL: `http://127.0.0.1:8818/player.html?debug=1`
- Review server: run `python3 scripts/range_review_server.py --host 127.0.0.1 --port 8818 --directory .` from this packet root. This serves MP3 byte ranges so the native audio timeline scrubber can seek reliably.
- New mask: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_shuttle_stack_reference_variant_a_full_runtime_hybrid_attention_rewrite_music_only_intro_outro_outro_screen_literal_rail_captions_precise_matte_visibility_repair_html_approval_proof_20260512T163537Z/assets/masks/foreground_occlusion_matte.png`
- Matte QA: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_shuttle_stack_reference_variant_a_full_runtime_hybrid_attention_rewrite_music_only_intro_outro_outro_screen_literal_rail_captions_precise_matte_visibility_repair_html_approval_proof_20260512T163537Z/qa/matte/precise_matte_visibility_repair_qa.json`
- Overlay: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_shuttle_stack_reference_variant_a_full_runtime_hybrid_attention_rewrite_music_only_intro_outro_outro_screen_literal_rail_captions_precise_matte_visibility_repair_html_approval_proof_20260512T163537Z/qa/matte/precise_matte_overlay_for_review.png`

No MP4 was rendered. Gates remain closed: `human_disposition: defer`, `may_create_full_runtime_mp4_render: false`, `may_advance_to_final_assembly: false`, `may_advance_to_publish_readiness: false`, `may_youtube_action: false`.

# Challenger Long-Form Tight Matte Review Proof

This successor tightens the allowed-sky foreground matte used for aircraft and dust occlusion. It preserves the prior audio, captions, chapters, outro timing, and visual shell.

- Predecessor proof: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_shuttle_stack_reference_variant_a_full_runtime_hybrid_attention_rewrite_music_only_intro_outro_outro_screen_literal_rail_captions_html_approval_proof_20260511T232232Z`
- Predecessor MP4: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_shuttle_stack_reference_variant_a_full_runtime_hybrid_attention_rewrite_music_only_intro_outro_outro_screen_literal_rail_captions_html_approval_proof_20260511T232232Z/video_render/hybrid_attention_rewrite_outro_screen_literal_rail_captions_youtube_review_mp4_20260511T232232Z/challenger_hybrid_attention_rewrite_outro_screen_literal_rail_captions_youtube_review_1080p24.mp4`
- New matte: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_shuttle_stack_reference_variant_a_full_runtime_hybrid_attention_rewrite_music_only_intro_outro_outro_screen_literal_rail_captions_tight_matte_html_approval_proof_20260512T152647Z/assets/masks/foreground_occlusion_matte.png`
- QA overlay: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_shuttle_stack_reference_variant_a_full_runtime_hybrid_attention_rewrite_music_only_intro_outro_outro_screen_literal_rail_captions_tight_matte_html_approval_proof_20260512T152647Z/qa/matte/tight_matte_overlay_for_review.png`
- Route QA: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_shuttle_stack_reference_variant_a_full_runtime_hybrid_attention_rewrite_music_only_intro_outro_outro_screen_literal_rail_captions_tight_matte_html_approval_proof_20260512T152647Z/qa/matte/tight_matte_route_occlusion_qa.json`

Review question: `keep`, `tighten`, or `reject` the tightened matte before any new MP4 render or YouTube publish-readiness step.

Current gates remain closed: `human_disposition: defer`, `may_create_full_runtime_mp4_render: false`, `may_advance_to_final_assembly: false`, `may_advance_to_publish_readiness: false`, `may_youtube_action: false`.

# Challenger Literal Rail Caption Successor Proof

This is a successor proof, not an overwrite of the current YouTube outro-screen package.

- Predecessor proof: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_shuttle_stack_reference_variant_a_full_runtime_hybrid_attention_rewrite_music_only_intro_outro_outro_screen_html_approval_proof_20260511T225637Z`
- Predecessor MP4: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_shuttle_stack_reference_variant_a_full_runtime_hybrid_attention_rewrite_music_only_intro_outro_outro_screen_html_approval_proof_20260511T225637Z/video_render/hybrid_attention_rewrite_outro_screen_youtube_review_mp4_20260511T225637Z/challenger_hybrid_attention_rewrite_outro_screen_youtube_review_1080p24.mp4`
- Successor player: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_shuttle_stack_reference_variant_a_full_runtime_hybrid_attention_rewrite_music_only_intro_outro_outro_screen_literal_rail_captions_html_approval_proof_20260511T232232Z/player.html`
- Literal rail-safe VTT: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_shuttle_stack_reference_variant_a_full_runtime_hybrid_attention_rewrite_music_only_intro_outro_outro_screen_literal_rail_captions_html_approval_proof_20260511T232232Z/assets/captions/recording_20260511T204835Z_hybrid_attention_rewrite.diarized.corrected.literal_rail_safe.offset_intro_9s601.vtt`
- Manifest: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_shuttle_stack_reference_variant_a_full_runtime_hybrid_attention_rewrite_music_only_intro_outro_outro_screen_literal_rail_captions_html_approval_proof_20260511T232232Z/rough_assembly_manifest.json`

## What Changed

- Replaced the lower-right rail captions with literal spoken/script words.
- Re-chunked captions into shorter cue spans so the existing two-line 40px rail can show every word.
- Removed diarization speaker prefixes from displayed captions.
- Preserved no-karaoke browser-native TextTrack behavior.
- Preserved audio, chapters, visual shell, outro timing, and review-only gates.

Human disposition remains `defer`. Final assembly, publish readiness, and YouTube actions remain false.
