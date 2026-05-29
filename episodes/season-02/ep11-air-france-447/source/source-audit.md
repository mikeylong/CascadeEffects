# Source Audit: Air France Flight 447

status: review_ready
may_advance: false
human_gate_required: true
advisory_review_route: agent_mike

## Canonical Row

- Row: 11 in `cascade_effects_full_episode_table_1_186.md`.
- Source row status: reconstructed starter backlog; original 1-31 source row is still missing.
- Mechanism: automation surprise / human-machine handoff.
- Promise: Pitot icing, autopilot disconnect, cockpit indications, and crew interpretation created an aerodynamic state the pilots could not diagnose quickly enough.

## Authority Stack

Primary / official:

- [BEA official investigation hub](https://bea.aero/en/investigation-reports/notified-events/detail/accident-to-the-airbus-a330-203-registered-f-gzcp-and-operated-by-air-france-occured-on-06-01-2009-in-the-atlantic-ocean/) - official record and report hub.
- [BEA final report PDF](https://bea.aero/fileadmin/documents/docspa/2009/f-cp090601.en/pdf/f-cp090601.en.pdf) - core technical report.
- [BEA CVR transcript appendix](https://bea.aero/fileadmin/uploads/tx_elyextendttnews/annexe.01.en_03.pdf) - cockpit timeline, to be used sparingly.
- [BEA FDR chronology](https://bea.aero/fileadmin/uploads/tx_elyextendttnews/annexe.02_07.pdf) - timing evidence.
- [BEA parameter graphs](https://bea.aero/fileadmin/uploads/tx_elyextendttnews/annexe.03_07.pdf) - visual flight-data evidence.
- [Metron search analysis](https://bea.aero/fileadmin/uploads/tx_elyextendttnews/metron.search.analysis_01.pdf) - wreckage-location and search reconstruction.

Strong secondary / context:

- [SKYbrary AF447 summary](https://skybrary.aero/accidents-and-incidents/a332-en-route-atlantic-ocean-2009) - aviation-safety summary.

## Writer-Packet Claims Supported

- AF447 was an Air France A330-203, F-GZCP, Rio to Paris, lost over the Atlantic on June 1, 2009; all 228 aboard died.
- BEA frames the initiating technical chain around Pitot icing, erroneous speed indications, autopilot disconnect, stall, and ocean impact.
- The episode should center the handoff problem: automation left the crew with degraded cues, high workload, and a stall state that was not formally diagnosed in time.

## Cautions / Open Questions

- Do not flatten the story into "pilot error" or "weather did it."
- Treat legal-context updates separately from BEA safety findings.
- Use CVR fragments sparingly and avoid over-reading tone or psychology from transcripts.

## Visual / Evidence Candidates

- Pitot probe diagram, flight-path trace, FDR parameter graphs, stall-warning/angle-of-attack timeline, cockpit display reconstruction, ACARS message cascade, ocean-search probability map.

## Gate Result

disposition: review_ready
may_advance: false
next_action: Mike/human source-audit disposition before writer-packet production.
