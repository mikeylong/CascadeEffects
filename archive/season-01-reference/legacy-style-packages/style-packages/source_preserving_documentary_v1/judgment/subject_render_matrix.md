# Subject Render Matrix

This matrix sits between generic source-preserving prompt grammar and episode-specific prompt writing.

Use it before rendering. Then use `judgment/promotion_workflow.md` to decide whether a still can advance to motion or a clip can advance to a reel.

Restart note: during the Challenger-first restart, this matrix is a `legacy_reference` source by default. It may inform visual research proposals, but it cannot control prompt writing or promotion unless imported and activated by the current DP-approved episode constraint ledger.

Use it to decide:

- what must remain canonical for the subject class
- what recognizable research anchor must remain inferable
- what kind of anomaly can carry the image
- what kind of anomaly will collapse into AI slop
- what camera logic can actually expose the failure mechanism

If a prompt violates this matrix, rewrite the image problem before rendering.

## Universal Rules

- Preserve canonical subject identity before surreal effect.
- Preserve the named source anchor before any abstraction or reduction.
- Use only these dispositions when reviewing downstream results: `keep`, `tighten`, `diagnostic only`, `reject`.
- Prefer localized wrong-state cues over macro-shape deformation.
- Reject anomalies that read as sampler corruption, warped geometry, or damaged anatomy unless literal damage is the subject.
- Reject generic trays, folders, blank paperwork piles, or anonymous props when they erase the researched subject family. That failure mode is `anonymous evidence-room drift`.
- If motion reveals deformed anatomy or other source-baked defects, treat it as a source-still failure and rerender the still first.
- Do not try to repair inherited hand, face, body, or body-adjacent object corruption with motion-only prompting.
- No motion clip may be treated as `keep` if its source still is unresolved.
- Reject camera choices that cannot show the claimed mechanism of failure.
- If the anomaly does not read, change camera or anomaly carrier before changing style.

## single_object_or_device

- Canonical must remain:
  - recognizable device silhouette
  - core functional geometry
  - major interfaces and housings
- Preferred anomaly carriers:
  - wrong seam or internal glow
  - missing or extra component
  - contradictory physical condition at one subsystem
  - duplicated state cue in one local zone
- Allowed but riskier:
  - impossible reflection
  - blank signal area
- Banned:
  - melted or warped full-body geometry
  - unexplained duplication of the entire device
  - decorative abstract overlays
- Preferred camera:
  - object portrait
  - subsystem close view
  - machine-in-room view when the machine still dominates
- Common AI-slop failures:
  - warped housing
  - unreadable pseudo-controls
  - text leakage on device body
- Fallback move:
  - tighten to the subsystem carrying the contradiction

### single_object_or_device exception: medical machine

- Keep the machine body canonical and clinical.
- Carry the wrongness in beam path, head glow, wrong-state cue, or room relationship.
- Do not morph the machine into menace; it should look trustworthy first.

### single_object_or_device exception: industrial machine

- Let seams, valves, gauges, or interlocks carry the anomaly.
- Avoid overcomplicated mechanical spaghetti that obscures the machine read.

## single_human_figure

- Canonical must remain:
  - intact anatomy
  - believable posture
  - one readable human role
- Preferred anomaly carriers:
  - impossible shadow
  - contradictory reflection
  - one wrong object relationship
  - one absent or duplicated environmental cue
- Allowed but riskier:
  - minor limb or garment state mismatch
- Banned:
  - distorted face or body
  - extra fingers or limb corruption used as “surrealism”
  - expression so stylized the figure stops being readable
- Preferred camera:
  - mid shot
  - seated or standing portrait with visible context
- Common AI-slop failures:
  - hand corruption
  - facial asymmetry that reads as model error
  - overdramatized cinema lighting
- Fallback move:
  - move the contradiction out of the body and into light, shadow, or a prop
  - if motion inherits bad hands, bad anatomy, or other body-adjacent corruption from the still, fix the still upstream and then reanimate

## small_human_group

- Canonical must remain:
  - one readable group unit
  - believable anatomy and spacing
  - clear relational action
- Preferred anomaly carriers:
  - one empty or wrong-facing chair
  - one contradictory shared object
  - one impossible reflection or missing participant cue
- Allowed but riskier:
  - duplicated gesture in one subordinate figure
- Banned:
  - crowd complexity
  - multiple body distortions
  - more than one competing anomaly
- Preferred camera:
  - conference-table distance
  - grouped mid-wide frame
- Common AI-slop failures:
  - hand clutter
  - too many faces
  - loss of group read
- Fallback move:
  - simplify the group or demote one or more people into incidental background
- Motion caveat:
  - in still prompts, an empty or wrong-facing chair can be a valid group anomaly carrier
  - in Apple-native LTX 2.3 motion prompts, chair or seat-negation language is high-risk when the goal is stable human blocking
  - for human/tableau motion, describe concrete roles and fixed positions instead, and lock the room state with clauses such as all furniture and fixtures stay fixed and no objects enter or leave frame
  - reject motion that invents furniture, adds props, or turns a stable meeting tableau into sit/stand action

## room_or_interior

- Canonical must remain:
  - legible room type
  - one dominant subject or scene state inside the room
  - spatial coherence
- Preferred anomaly carriers:
  - one wrong subsystem state
  - one contradictory connection or load path
  - one impossible blank zone
  - one localized glow, seam, or missing element
- Allowed but riskier:
  - boundary/reflection contradictions
- Banned:
  - mood-only wrongness with no physical cue
  - impossible architecture that breaks room identity
  - collage-like insertion of foreign elements
- Preferred camera:
  - the distance required to show the actual mechanism
  - not wider than necessary
- Common AI-slop failures:
  - elegant but generic room
  - overdecorated interior noise
  - contradiction too small to read
- Fallback move:
  - crop tighter toward the failure-bearing zone

### room_or_interior exception: machine room

- The room is supporting context; the machine or failure-bearing subsystem must still dominate.
- Use machine-state contradictions, not generic ominous lighting.

### room_or_interior exception: structural interior / architecture-led interior

- The connection, rod, beam, walkway, or load path must be visible.
- If the structural issue cannot be pointed to in the frame, the prompt is too wide or too vague.

## structure_or_exterior

- Canonical must remain:
  - readable built form
  - stable silhouette
  - believable exterior context
- Preferred anomaly carriers:
  - one wrong light or signal
  - one seam condition
  - one missing component
  - one local physical contradiction
- Allowed but riskier:
  - scale mismatch if highly controlled
- Banned:
  - bent or broken whole-building geometry unless literal collapse is the subject
  - atmosphere-only wrongness
- Preferred camera:
  - frontal or three-quarter exterior
  - distance that preserves silhouette
- Common AI-slop failures:
  - mushy facade detail
  - structure becomes generic
  - overdramatized ruin language
- Fallback move:
  - move from full exterior to failure-bearing section or detail

## vehicle_vessel_or_aircraft

- Canonical must remain:
  - correct transport silhouette
  - believable body geometry
  - recognizable subtype identity
- Preferred anomaly carriers:
  - localized breach
  - one control-surface or subsystem contradiction
  - one wrong navigation or status cue
  - one engine-placement or mechanism-bearing detail
- Allowed but riskier:
  - contradictory trim or attitude state if the camera can show it cleanly
- Banned:
  - warped fuselage
  - broken tail or wing geometry used as shorthand for hidden system failure
  - readable brand text leakage
- Preferred camera:
  - whichever angle best exposes the subsystem carrying the contradiction
  - not automatically a whole-vehicle hero shot
- Common AI-slop failures:
  - model corruption mistaken for wrong state
  - text leakage on tail/body
  - impossible aero surfaces
- Fallback move:
  - tighten to subsystem or shift to a more orthographic/canonical angle

### vehicle_vessel_or_aircraft exception: passenger aircraft

- Full-aircraft contradiction prompts are high-risk.
- Favor:
  - side profile with one readable stabilizer or trim cue
  - tailplane / control-surface detail
  - engine-placement / nose-attitude relationship only if physically legible
- Avoid:
  - underside hero view if it hides the control problem
  - asking the whole aircraft body to look “wrong”

### vehicle_vessel_or_aircraft exception: launch stack / shuttle

- Launch vehicles can tolerate a wider full-subject view because a small localized breach can still read.
- Keep the stack canonical and let smoke, flame leak, or joint breach carry the wrongness.

## site_or_landscape

- Canonical must remain:
  - readable place type
  - stable geography
  - one dominant site condition
- Preferred anomaly carriers:
  - one wrong waterline
  - one bent infrastructure line
  - one absent or duplicated boundary cue
  - one impossible ground-state condition
- Allowed but riskier:
  - scale mismatch
- Banned:
  - total landscape surrealization
  - multiple site contradictions at once
- Preferred camera:
  - wide enough to keep place identity
  - tight enough that the contradiction is still visible
- Common AI-slop failures:
  - generic atmosphere with no site read
  - painterly abstraction
- Fallback move:
  - move from site-wide view to one decisive infrastructure relationship

## fragment_or_detail

- Canonical must remain:
  - one readable clue
  - identifiable material and mechanism
  - clean edge hierarchy
- Preferred anomaly carriers:
  - misalignment
  - wrong seam
  - contradictory closed/open state
  - one missing or duplicated small component
- Allowed but riskier:
  - impossible reflection
- Banned:
  - overcropping until the thing is no longer identifiable
  - decorative texture noise standing in for information
- Preferred camera:
  - close crop with enough context to name the thing
- Common AI-slop failures:
  - meaningless macro texture
  - unreadable metal/plastic ambiguity
- Fallback move:
  - widen slightly until the clue belongs to an identifiable mechanism
