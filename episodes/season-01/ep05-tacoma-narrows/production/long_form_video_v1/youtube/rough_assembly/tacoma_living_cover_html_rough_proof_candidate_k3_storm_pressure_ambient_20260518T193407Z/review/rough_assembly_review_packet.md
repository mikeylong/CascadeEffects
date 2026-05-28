# Tacoma K3 Living Cover Rough Proof Storm-Pressure Ambient Successor

Status: review_ready_human_keep_pending

This packet supersedes the K3 chapter-transition smoothing proof as tighten. It preserves the kept K3 source art, repaired `wind tunnel` VO, script-locked captions, actual-outro prelap music mix, right-rail opacity repair, Challenger/Therac titleless end screen, and `challenger_staged_visual_transition_v1`. It adds a source-integrated storm-pressure ambient layer only.

No final MP4, publish-readiness package, YouTube upload, or public release has been created or unlocked.

## Review URL

http://127.0.0.1:8858/player.html

## Ambient Repair Included

- `wind_rain_shear_layer`: seeded diagonal wet-air streaks over open air, water, and roadway, excluded from the right rail.
- `roadway_wet_sheen`: low-opacity moving specular streaks on the wet deck surface, without independently animating people, faces, or cars.
- `torsion_pressure_envelope`: stronger source-safe roll/drift during `Galloping Became Normal` and `The Air Fed The Twist`, with no mesh warp or new bridge geometry.
- `background_haze_pressure`: subtle wet-air contrast/haze over water and forest.

## Browser QA

- QA pass: true
- Browser QA JSON: /Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma_living_cover_html_rough_proof_candidate_k3_storm_pressure_ambient_20260518T193407Z/qa/browser_qa_1920x1080.json
- Browser QA SHA-256: a2bd86db630bada6dab7cf2a1d482a6255573522322ffecc10d312299a8c50cc
- Storm-pressure ambient strip PNG: /Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma_living_cover_html_rough_proof_candidate_k3_storm_pressure_ambient_20260518T193407Z/qa/storm_pressure_ambient_review_strip.png
- Storm-pressure ambient strip PNG SHA-256: 2a3d43d9ba53cb89470d87abf223d35cdf373ca49d22791e96b6696eb5948423
- Storm-pressure ambient strip HTML: /Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma_living_cover_html_rough_proof_candidate_k3_storm_pressure_ambient_20260518T193407Z/qa/storm_pressure_ambient_review_strip.html
- Storm-pressure ambient strip HTML SHA-256: de3e6b909f5da751de92956e6a151c8e5ecf3a5542de74df249f8e2bb8ef05d1
- Ambient samples captured: 7
- Focused transition strip PNG: /Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma_living_cover_html_rough_proof_candidate_k3_storm_pressure_ambient_20260518T193407Z/qa/focused_transition_review_strip.png
- Focused transition strip PNG SHA-256: 10b5b898e8bd415544dcd1567e4d2fff13419afde660af4712248a231108eb53

## Passing Ambient Reads

- ambient_effects_plan_read: pass_storm_pressure_ambient_layer_declared_and_exposed
- ambient_effect_lane_decision_read: pass_storm_pressure_source_integrated_ambient_v1
- source_plate_matte_registration_read: pass_fixed_1920x1080_canvas_with_right_rail_exclusion_mask
- foreground_occlusion_read: pass_no_independent_people_car_face_or_debris_motion
- effect_layer_source_safety_read: pass_preserves_k3_plate_no_new_geometry_or_diagnostic_overlay
- deterministic_ambient_read: pass_seeded_storm_pressure_parameters_declared
- additive_effect_integration_read: pass_storm_pressure_added_without_removing_prior_source_drift_or_roll
- debug_overlay_absence_read: pass_no_diagnostic_overlay_in_player_samples
- ambient_effect_browser_sample_read: pass_ambient_canvas_nonblank_and_changes_across_story_samples
- range_scrub_effect_review_read: pass_range_server_and_late_episode_ambient_samples_available
- localized_particle_density_read: pass_restrained_density_with_visible_storm_pressure
- particle_foreground_leak_read: pass_ambient_excluded_from_right_rail_and_no_independent_foreground_motion

## Preserved Passing Reads

- K3 source art loaded; Candidate G runtime reference absent.
- Captions are active as a media-player text track and visible in the right rail.
- Distinct eyebrow/title pairs remain in place.
- No opaque lower rail column below current scene text.
- Final-20s Challenger/Therac titleless end-screen window remains intact.
- Actual-outro prelap mix remains intact.
- Chapter boundaries use the staged Challenger transition model.
- Byte-range media server returns 206 Partial Content.

## Gate State

- Rough proof: human keep pending.
- Final assembly: blocked pending human keep.
- Final MP4: blocked.
- Publish readiness: blocked.
- YouTube upload: blocked.
- Public release: manual YouTube Studio only.
