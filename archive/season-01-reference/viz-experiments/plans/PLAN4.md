## Pipeline-Agnostic Controlled Typography Refinement

### Summary
- Reframe controlled typography as a production-layer capability for Cascade Effects, not as a feature of any one still-image workflow.
- The typography system should attach to any pipeline that emits a visual artifact plus metadata: still render, packaged plate, video frame sequence, handoff asset, or future generator.
- Keep the core rule unchanged: generative image/video stages remain zero-letter by default; readable text is introduced only through an explicit controlled-typography layer with validation.

### Key Changes
- Define a shared typography intent contract that is independent of the upstream producer. It should describe:
  - target artifact type: `still`, `image_sequence`, `video`, or `handoff_asset`
  - application phase: `post_generate`, `post_refine`, `post_upscale`, `post_handoff`, or `post_encode`
  - zone list with readable text, geometry, styling, fit behavior, and validation policy
  - optional per-zone surface behavior such as underlay, neutralization, shadow, and blend
- Split the implementation into three layers:
  - `intent layer`: declarative typography manifests and validation
  - `apply layer`: renderer/compositor adapters for stills, frame sequences, and encoded video
  - `audit layer`: OCR/leak detection, manifest recording, and debug artifacts
- Keep the current still compositor as the first adapter, but specify the system so additional adapters can implement the same contract without changing the manifest shape.
- Introduce stage-agnostic zone behavior so fitting and realism controls are not tied to one preset:
  - text fit modes
  - padding and alignment
  - surface neutralization modes
  - reusable underlay and shadow primitives
  - per-zone debug outputs
- Define frame-stable behavior for temporal pipelines:
  - video and image-sequence adapters must treat zones as either fixed-frame quads or tracked surfaces
  - readable text must remain temporally stable across frames
  - leak detection must support per-frame sampling plus sequence-level failure reporting
- Define artifact-agnostic outputs:
  - original base artifact path
  - typography-applied artifact path
  - typography intent manifest path
  - validation results
  - debug artifact paths when requested
- Keep manual-first as the default operational policy across pipelines. Auto-application should remain an adapter-level opt-in, not a global assumption.

### Interfaces
- Introduce one shared conceptual command surface, regardless of backend:
  - `typography apply <target> --artifact <path> --intent <path>`
  - `typography validate <target> --artifact <path> --intent <path>`
- Existing `bin/ce render typography ...` can remain as the still adapter, but it should be treated as one implementation of the shared contract, not the contract itself.
- The shared intent manifest should be producer-agnostic and must not require knowledge of Comfy-specific stages like `final_upscale`.
- Adapter-specific orchestration may map local stages into the shared application phases, but that mapping stays outside the shared manifest.

### Test Plan
- Shared manifest validation passes independently of the producing pipeline.
- Still adapter smoke tests:
  - apply readable text to a final still
  - enforce OCR match inside approved zones
  - fail on readable text outside approved zones
- Handoff-asset smoke tests:
  - apply typography to a staged artifact without requiring regeneration
  - preserve provenance and validation metadata
- Video/image-sequence adapter acceptance criteria:
  - approved text remains stable across sampled frames
  - no uncontrolled readable text appears outside approved zones
  - sequence-level reporting identifies failing frames and zones
- Backward compatibility:
  - existing still-only manifests can be migrated or interpreted without losing current functionality
  - still-only workflows continue to work even before video adapters exist

### Assumptions
- This refinement is a shared systems spec, not a Challenger-only tuning plan.
- Zero-letter generation remains the default across Cascade Effects production.
- The first concrete implementation remains the current still adapter, but the spec must not encode still-only assumptions into the shared contract.
- Tracking and temporal compositing for video may be introduced later behind the same manifest model rather than through a separate typography system.
