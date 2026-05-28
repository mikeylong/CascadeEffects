# 737 MAX Screen Recording Feedback - Candidate J Retry Mullion Artifacts

Date: 2026-05-19

Recorded at UTC: 2026-05-19T18:40:07Z

Workflow: `long_form_video_production_v1`

Gate: `source_art_generation`

Source recording: `/var/folders/gt/lzhcg8wj3f19j78b3g444s1c0000gn/T/TemporaryItems/NSIRD_screencaptureui_fe52Bf/Screen Recording 2026-05-19 at 10.18.23.mov`

Transcript status: local `transcribe` completed before thread disconnect; temporary transcript files expired before persistent copy. Timecoded findings below are copied from the completed local transcript output visible in the session.

## Timecoded Feedback

| Timecode | Spoken Feedback | Production Read |
|---|---|---|
| `00:00:01.381-00:00:17.516` | The gray wall is gone, but the repair looks like it tried to draw a vertical support bar over the window. | Repair solved the gray-block issue but introduced a new window-mullion artifact. |
| `00:00:18.306-00:00:24.897` | Another bar does not look like the other ones and is spaced inconsistently. | Right-side mullions must be physically consistent with the existing terminal glass geometry. |
| `00:00:24.939-00:00:41.326` | The support beam comes down in front of a person who should be behind the glass; it is weird for the beam to cut in front of this person. | New candidate must preserve depth ordering: interior foreground people are on the terminal side of the glass; no generated mullion may cut through a foreground viewer. |
| `00:00:52.805-00:00:55.637` | There are too many artifacts; it is not looking good. | The failed retry cannot advance. Regenerate again with cleaner window geometry. |

## Acceptance Criteria For Next Candidate

- Same overall Candidate J composition: terminal viewers in foreground, rain glass, aircraft left/center, ramp worker near lower center-right, right third rail-safe.
- No new inconsistent vertical support bars on the right side.
- No window mullion or support beam crossing through a human silhouette.
- Foreground viewers remain clearly inside the terminal, on the viewer side of the glass.
- Right side remains scene-integrated with rain glass, reflections, ramp lights, and airport depth rather than a flat wall.
- No Paper Architecture, no readable text/logos, no identifiable faces, no crash spectacle, no admin/evidence props.

## Gate Effect

- Failed retry: `tighten_reference_only`
- Next legal candidate: `candidate_k_terminal_glass_depth`
- Downstream cue map, ambient/effects layer, music integration contract, rough assembly, final render, YouTube action, and public release remain blocked.
