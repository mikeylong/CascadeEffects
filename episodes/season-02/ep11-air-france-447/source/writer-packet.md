# Writer Packet: Air France Flight 447

status: review_ready
may_advance: false
source_audit_disposition: keep
human_gate_required: true
target_runtime: 12-18 minutes
canonical_row_status: reconstructed starter backlog; original 1-31 source row still missing

## Episode Brief

- Primary lane: Design Failures That Changed the World.
- Mechanism: automation surprise / human-machine handoff.
- Changed-first frame: the aircraft moved from managed cruise into a degraded manual-flight problem before the cockpit picture made that change easy to recognize.
- Public version: pilots stalled an Airbus over the Atlantic.
- Incomplete version: Pitot icing, unreliable speed data, automation disconnect, cockpit indications, workload, training expectations, and stall recognition interacted inside one handoff failure.
- Audience promise: AF447 is not a pilot-error recap. It is a forensic episode about what happens when automation gives the crisis back after the system has already changed the evidence humans need.

## Evidence Base

- Canonical row 11 frames the promise as: Pitot icing, autopilot disconnect, cockpit indications, and crew interpretation created an aerodynamic state the pilots could not diagnose quickly enough.
- Primary record: BEA investigation hub, final report, CVR appendix, FDR chronology, FDR parameter graphs, and Metron search analysis.
- Context source: SKYbrary aviation-safety summary.
- Legal context is production background only unless Mike wants a short end-note. It must stay separate from the BEA technical findings.

## Evidence / Interpretation Split

Evidence the packet can treat as factual:

- AF447 was Air France A330-203 F-GZCP, Rio to Paris, lost over the Atlantic on June 1, 2009; all 228 aboard died.
- The technical chain begins with high-altitude weather and Pitot icing leading to unreliable airspeed indications.
- Automation disconnected, cockpit indications changed, and the aircraft entered a stall state that was not formally diagnosed in time.
- FDR/CVR material supports sequence reconstruction, but CVR fragments are partial evidence and should not become character psychology.

Interpretation for Cascade Effects:

- The hidden mechanism is not "the pilots made a mistake." It is that the system returned control after it had already made the aircraft state harder to see.
- The episode should make the handoff itself visible: what changed, what became ambiguous, which cues were available, which cues were missing or misleading, and how recognition arrived too late.
- The systemic reading should stay focused on automation design, training assumptions, interface legibility, and degraded-mode handoff.

## Causal Layers

1. Normal state: cruise automation made the aircraft feel stable, managed, and routine.
2. Hidden change: Pitot icing corrupted the speed picture before the crew had a simple visible diagnosis.
3. Handoff: automation disconnected and returned the problem to humans in a degraded-cue state.
4. Information mismatch: displays, warnings, flight-path behavior, and crew interpretation no longer formed one obvious picture.
5. Recognition failure: the aircraft entered a stall state without the crew collectively naming the state in time.
6. Consequence: by the time the mechanism became recoverable in retrospect, altitude, coordination, and cognitive bandwidth had already narrowed.

## Point Of No Return

The decisive shift for the episode is the handoff, not the impact: automation left the crew with a crisis whose cues had already become ambiguous. The script should still be careful not to imply one instant made recovery impossible; the point of no return should be treated as a narrowing window after the stall state went unrecognized.

## Compact Thesis

Air France 447 shows how an automated system can fail by giving control back only after it has made the situation harder for humans to understand.

## 10-Part Spine

1. Cold open: the aircraft is still flying, but the system state has already changed.
2. Public version: the shorthand story says pilots stalled the aircraft.
3. Incomplete version: that shorthand skips the handoff, the missing cues, and the degraded cockpit picture.
4. Normal automation: establish what managed cruise usually hides from the crew because it is working.
5. Hidden trigger: Pitot icing and unreliable speed indications break the trust layer.
6. Handoff: autopilot disconnect turns a machine-managed abnormality into a human diagnosis problem.
7. Cue conflict: map pitch, speed, stall warning, angle-of-attack reality, and cockpit interpretation without turning the transcript into psychology.
8. Recognition window: show how the stall state persisted while the crew did not converge on the diagnosis.
9. Systemic reading: connect BEA findings to automation mode awareness, training, interface legibility, and degraded-mode design.
10. Close: the system gave the crisis back after clarity had already been lost.

## Visual Anchors

- Pitot probe diagram as the first hidden-change artifact.
- Automation handoff timeline: managed cruise to unreliable airspeed to disconnect to manual control.
- Flight-path, altitude, vertical-speed, and pitch trace from FDR material.
- Stall-warning / angle-of-attack timeline, with a visible caution that angle of attack was not the crew's clean public-facing cue.
- Cockpit display reconstruction that separates what the aircraft was doing from what the crew could easily infer.
- ACARS message cascade and ocean-search probability map as secondary proof visuals.

## Title Directions

- `Air France 447: What the System Hid`
- `AF447: The Handoff That Hid the Stall`
- `Air France 447: When Automation Gave Up Too Late`
- `AF447: The Crisis Automation Gave Back`

Preferred direction: `Air France 447: What the System Hid`. It matches the canonical thumbnail phrase, avoids blame framing, and leaves room for the mechanism reveal.

## Thumbnail Direction

- Object/artifact: cockpit display or Pitot probe, not wreckage.
- Hidden mechanism: the handoff happened after the state had become hard to read.
- Visual question: "what changed before anyone could see it?"
- Copy options, 2 to 4 words: `WHAT CHANGED`, `SYSTEM HID IT`, `HANDOFF TOO LATE`, `STALL UNSEEN`.
- Avoid: pilot portraits, panic faces, ocean tragedy imagery as the main hook, and any graphic that implies the CVR transcript is the episode's primary evidence.

## Research Needs

- Confirm the exact BEA-supported timing for unreliable airspeed, autopilot/autothrust disconnect, stall warnings, altitude loss, and final impact sequence.
- Pull only the minimum necessary CVR excerpts and pair each with FDR evidence so the script uses transcript as sequence support, not personality evidence.
- Verify how BEA describes training, stall-recognition, and procedure issues so the script does not invent an interface-design claim stronger than the report.
- Decide whether the 2026 legal-status update belongs in the episode. If used, keep it in a short, clearly separated legal-context note.
- Source-row provenance remains unresolved because the canonical table marks row 11 as reconstructed starter backlog with the original source row missing.

## Review Questions

- Is "what the system hid" specific enough, or should the packet name the handoff more directly in the title?
- Does the point-of-no-return framing make the recognition window clear without implying recovery was impossible too early?
- Should legal context be excluded from the final script unless it directly affects audience trust?
- Does the episode need a short automation-mode primer, or can that be handled visually inside the handoff timeline?
- Are the CVR guardrails strong enough to prevent pilot-error flattening and transcript-driven psychology?

## Source Guardrails

- Do not flatten the accident into pilot error or weather.
- Treat legal context separately from BEA technical findings.
- Use CVR excerpts sparingly and without psychological overreach.
- Keep evidence and interpretation visibly separate.
- Mark uncertain or disputed claims as research needs, not narration.

## Gate Result

disposition: review_ready
may_advance: false
next_action: human/Mike writer-packet disposition before longform script drafting.
