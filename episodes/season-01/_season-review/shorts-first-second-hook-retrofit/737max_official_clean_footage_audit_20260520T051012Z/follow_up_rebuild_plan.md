# Follow-Up Rebuild Plan: 737 MAX Official-Source Hook/Tail Repair

## Summary

Rebuild a new local-only 737 MAX theme-hook proof using the two kept official Boeing first-flight spans from this audit. The goal is to remove the engine-closeup-heavy feel without changing voice timing, theme timing, final captions, or YouTube state.

## Key Changes

- Replace the current 3.0s engine hook with a 3.0s slice from `bff_span_27_55_takeoff_roll_rotation_no_audio.mp4`, starting on aircraft motion rather than engine detail.
- Replace the current engine-close tail with a computed source-motion tail from `bff_span_75_110_air_to_air_landing_exact_no_audio.mp4`.
- Preserve the existing 737 proof structure: theme punch at `t=0.00`, 3.0s voice delay, loop crossfade under narration, signal-interruption handoff, full-picture CRT pass, final duration, and no final caption rebuild.
- Keep `bff_span_115_132_taxi_wing_detail_no_audio.mp4` out of hook/tail unless human review explicitly wants a backup detail insert.

## Test Plan

- Compile the shared and 737 proof builders if the wrapper is changed.
- Rebuild only a local proof package and update the 737 latest symlink.
- Validate manifest JSON, proof/comparison decode, final-8s `freezedetect`, peak below `-1 dBFS`, and no YouTube/upload/publish/delete/replace/schedule action.
- Generate opening, hook/body seam, signal-tail handoff, and end-frame strips showing the engine repetition is gone.

## Assumptions

- The two kept official Boeing spans are approved only for local review proof repair until human `keep`.
- Source-native Boeing aircraft livery is acceptable in this audit; non-source-native overlays remain blocked.
- Stock footage remains deferred.
