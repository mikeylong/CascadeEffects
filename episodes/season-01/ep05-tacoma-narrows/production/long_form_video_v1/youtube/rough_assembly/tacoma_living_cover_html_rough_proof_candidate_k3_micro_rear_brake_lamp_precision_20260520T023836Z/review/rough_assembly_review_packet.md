# Tacoma K3 Micro Rear Brake-Lamp Precision Rough Proof

Status: review_ready_human_keep_pending

Active packet: /Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma_living_cover_html_rough_proof_candidate_k3_micro_rear_brake_lamp_precision_20260520T023836Z

Player: /Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma_living_cover_html_rough_proof_candidate_k3_micro_rear_brake_lamp_precision_20260520T023836Z/player.html
Review URL: http://127.0.0.1:8858/player.html

## What Changed

This successor preserves the flipped K3 backplate, protected bottom-refraction full-surface glass rain, repaired narration, captions, actual-outro mix, right-rail behavior, staged chapter transitions, Challenger/Therac titleless end screen, and rapid brake-lamp pulse timing.

The only intended repair is brake-lamp source precision. The broad rear-surface masks are no longer sufficient. The proof now uses a packet-local `vehicle_rear_light_pixel_map.json` with tiny rear-light micro masks for the far uphill sedan, mid-lane sedan, and near dark truck / third visible distant vehicle. Paired red lamp cores are centered on declared rear-corner pixels with roughly 1-2px cores, minimal bloom, and subordinate wet-deck reflections.

## QA Reads

- vehicle_rear_light_pixel_map_read: pass
- lamp_core_centroid_within_2px_read: pass
- micro_mask_area_read: pass
- no_broad_vehicle_mask_read: pass
- no_large_alignment_dot_occlusion_read: pass
- all_three_micro_lamps_active_read: pass
- all_three_visible_distant_vehicle_lamps_read: pass
- no_free_floating_brake_lamp_read: pass
- brake_lamp_alignment_overlay_absence_read: pass
- browser_qa_1920x1080: pass

## Review Artifacts

- Vehicle rear light pixel map: /Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma_living_cover_html_rough_proof_candidate_k3_micro_rear_brake_lamp_precision_20260520T023836Z/references/vehicle_rear_light_pixel_map.json
- Micro calibration sheet: /Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma_living_cover_html_rough_proof_candidate_k3_micro_rear_brake_lamp_precision_20260520T023836Z/qa/micro_rear_lamp_precision_calibration_sheet.png
- Micro precision contact sheet: /Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma_living_cover_html_rough_proof_candidate_k3_micro_rear_brake_lamp_precision_20260520T023836Z/qa/micro_rear_lamp_precision_contact_sheet.png
- Visible rear-lamp origin strip: /Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma_living_cover_html_rough_proof_candidate_k3_micro_rear_brake_lamp_precision_20260520T023836Z/qa/visible_rear_brake_lamp_origin_strip.png
- Rapid pulse strip: /Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma_living_cover_html_rough_proof_candidate_k3_micro_rear_brake_lamp_precision_20260520T023836Z/qa/brake_lamp_rapid_pulse_contact_strip.png
- Browser QA JSON: /Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma_living_cover_html_rough_proof_candidate_k3_micro_rear_brake_lamp_precision_20260520T023836Z/qa/browser_qa_1920x1080.json

## Downstream Locks

Final assembly, final MP4, publish readiness, YouTube upload, and public release remain blocked pending human rough-proof review.

Review ask: keep, tighten, or reject this micro rear brake-lamp precision proof.
