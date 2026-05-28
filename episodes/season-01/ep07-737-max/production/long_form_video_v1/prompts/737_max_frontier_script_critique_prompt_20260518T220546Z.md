You are the frontier-model critic for Cascade Effects long_form_video_production_v1.

Task: Critique the exact 737 MAX compact long-form script for audio-render authorization. Do not rewrite the full script. Return a concise Markdown critique packet with a clear verdict and gate reads.

Workflow constraints:
- Episode: 737 MAX / Ep7_737-MAX
- Workflow: long_form_video_production_v1
- Gate: frontier_model_script_critique_before_audio
- Audio render is blocked unless the exact script revision has frontier critique, critique integration or explicit deferral, and human approval for audio.
- Target is compact existing script, not 30-40 minute expansion.
- Evaluate as a watchable audio essay that can later become a Living Cover video.
- Existing 737 Short/private upload is separate and must not authorize long-form publishing.

Required critique focus:
1. Factual/sourcing risk against the supplied fact-check memo.
2. Script structure and mechanism clarity: what changed, who failed to recognize it, and how the system converted blindness into consequence.
3. Audio-readiness: cadence, TTS risk, duplicate/awkward phrasing, bracketed performance tags, hard-to-read quotes or acronyms.
4. Stale next-episode or CTA language.
5. Any required changes before audio, with exact line/phrase-level recommendations.

Verdict vocabulary:
- `pass_no_script_changes`
- `pass_with_tightening`
- `tighten_before_audio`
- `reject`

Output format:
# 737 MAX Frontier Script Critique

## Verdict
`...`

## Summary
...

## Required Changes Before Audio
- ... or `None`.

## Suggested Tightening
- ... or `None`.

## Audio/TTS Notes
...

## Fact-Check Alignment
...

## Gate Reads
- `frontier_model_script_critique_read`: `...`
- `required_changes_read`: `...`
- `audio_render_recommendation`: `...`

Reviewed script path: /Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/Ep7_737-MAX.txt
Reviewed script SHA-256: 3f95aaf72b3144f0c33ee85e77d18140a888ba97c46eb89b0cfaad5c61a7c718
Reviewed script word count: 2166
Fact-check path: /Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/fact_check.md
Fact-check SHA-256: b779727882ff6a09a6dd6d4d0a088980b010d5a40dc0d69a88d1f5dcfdd493e5

--- SCRIPT START ---
[calm] In October 2018, Lion Air Flight 610 departed Jakarta and crashed into the Java Sea thirteen minutes after takeoff. All 189 people on board were killed.

[measured] Five months later, in March 2019, Ethiopian Airlines Flight 302 departed Addis Ababa and crashed six minutes after takeoff. All 157 people on board were killed.

[deliberate] Both aircraft were Boeing 737 MAX 8s. Both crews had fought the same automated system. Both had lost.

[measured] In the months that followed, investigators, regulators, and a congressional committee examined how two brand-new aircraft from the world's most experienced commercial aviation manufacturer had been delivered to airlines with a flight control system that could overpower the pilots, that depended on a single sensor for its inputs, and that had not been fully described in the flight manuals the pilots were trained on.

[deliberate] This episode is not about one faulty sensor. It is about what happens when a company tries to preserve the appearance of the old system while redesigning around a new physical reality — and resolves the contradiction in software the pilot cannot clearly see.

[calm] The Boeing 737 first flew in 1967. Over the following five decades it became the world's bestselling jetliner, accumulated an enormous global maintenance and training infrastructure, and underwent continuous revision and modernization while retaining enough commonality across variants that pilots could transition between versions with limited additional training.

[measured] That commonality was not incidental. It was commercially valuable. Airlines operating mixed fleets of 737 variants could schedule pilots across aircraft types, reduce training costs, and avoid the expense of full type rating transitions. The 737's longevity was inseparable from its reputation for consistency.

[calm] In December 2010, Boeing's primary competitor launched the A320neo program, featuring more fuel-efficient engines. The announcement was a significant competitive event. Airlines responded with interest. Boeing faced a choice: develop an entirely new aircraft, which would take years and cost billions, or modernize the 737 again.

[measured] Boeing chose to modernize. The result was the 737 MAX.

[deliberate] The MAX used a new engine — the CFM LEAP — that was larger and more fuel-efficient than its predecessor. The engine's size required it to be mounted differently on the wing: further forward and higher up than on earlier 737 variants. That repositioning changed the aircraft's aerodynamic behavior at high angles of attack. Specifically, under certain conditions, the new engine placement caused the nose to pitch up more than it had on previous variants.

[measured] This was a handling difference that could, in principle, require pilots to learn new procedures or require a new type rating. Either outcome would erode the commonality argument. The training cost advantage — one of the central commercial justifications for the MAX program — depended on the MAX flying like a 737.

[grave] So Boeing designed a software system to make it fly like one.

[deliberate] The Maneuvering Characteristics Augmentation System — MCAS — was introduced to compensate for the MAX's changed pitch behavior at high angles of attack. When the system detected conditions that could lead to a nose-high attitude, it automatically pushed the nose down by trimming the horizontal stabilizer.

[measured] In its original design, MCAS was a relatively limited system. It operated in a narrow flight envelope, moved the stabilizer a modest amount, and was not considered significant enough to require prominent disclosure in the flight crew operations manual. The FAA's certification process, which delegated substantial technical review authority to Boeing's own engineers, did not flag it as a major new system requiring special pilot awareness.

[calm] Then the design changed.

[measured] As flight testing proceeded, the parameters of MCAS were expanded. The system was authorized to move the stabilizer more — up to 2.5 degrees per activation, compared to the original 0.6 degrees. It was authorized to activate repeatedly if the triggering conditions persisted. And it continued to rely on input from a single angle-of-attack sensor.

[deliberate] A single sensor. On an aircraft where the system that read that sensor could push the nose toward the ground with enough authority to overpower a crew that did not know what was happening, or was not clearly prepared for the precise sequence of actions needed to stop it.

[calm] When the 737 MAX entered service, pilots were not told MCAS existed by name. The system was not described in the standard flight crew operations manual. The training materials that accompanied the MAX's entry into service were designed around the commonality argument — the MAX was presented as a familiar aircraft with improved engines, not as an aircraft with a new automated flight control system that behaved in ways previous 737s had not.

[measured] The rationale was coherent within its own logic. MCAS was designed to make the MAX handle like a 737. If it worked as intended, pilots would never know it was there. Describing a transparent background system in detail would raise questions about why it was needed, which would raise questions about how different the MAX actually was, which would undermine the commonality argument that justified the limited training program.

[somber] The system was hidden from pilots not through malice, but because its visibility would have cost too much.

[deliberate] On October 29, 2018, the crew of Lion Air 610 encountered repeated uncommanded nose-down inputs beginning shortly after takeoff. The aircraft's angle-of-attack sensor — the left one, which fed MCAS — had been providing erroneous readings since a previous flight. The crew fought the inputs. The aircraft pitched down. It entered the Java Sea at high speed.

[measured] The flight data recorder from Lion Air 610 showed clearly what had happened. Boeing and the FAA were informed. An emergency airworthiness directive was issued. It described a runaway stabilizer condition and directed pilots to follow existing procedures for handling it.

[deliberate] It did not name MCAS.

[somber] Ethiopian Airlines Flight 302 departed Addis Ababa on March 10, 2019, four months after Lion Air 610. The crew encountered the same system, the same failure mode, the same inputs. They had been issued the directive. They attempted the runaway-stabilizer response described after Lion Air. It was not sufficient to save the aircraft.

[grave] 157 people died. The 737 MAX was grounded worldwide two days later.

[calm] To understand how this happened, you have to trace five conditions that were present long before either aircraft took off.

[deliberate] The first: a competitive business pressure became a design requirement.

[measured] The decision to match the A320neo's timeline by extending the 737 rather than developing a new aircraft placed a specific constraint on the MAX program: the result had to be certifiable as a variant of an existing type, with training differences that airlines could manage within their existing 737 programs. That constraint was not an engineering requirement. It was a commercial one. But it shaped every subsequent engineering decision, because any outcome that threatened the commonality argument threatened the program's competitive rationale.

[deliberate] The second: MCAS grew in authority during development.

[measured] The system that entered service was not the system originally designed. The expansion of MCAS's authority — more stabilizer movement, repeated activations, the same single-sensor input — was driven by flight test results that required more compensation than the original design had provided. Each expansion was reviewed and accepted within the program. None triggered a reassessment of whether the system had become something qualitatively different from what had originally been certified.

[calm] A system that started as a background trim function had become, by the time it reached service, a powerful automated input capable of forcing the aircraft into a dive. The process that evaluated it was calibrated to the system's origin, not its final state.

[deliberate] The third: single-sensor dependency was accepted as sufficient.

[measured] MCAS relied on one angle-of-attack sensor. A single point of failure in a system with the authority to override pilot inputs. The rationale, as documented in the subsequent investigations, was that MCAS was intended as a supplement to existing protections — that other systems and procedures would catch a sensor failure before MCAS became dangerous.

[somber] That assumption required pilots to recognize a failure mode that had not been described to them, in an aircraft they had been told was like the one they already knew, under high workload conditions, in the seconds after takeoff.

[deliberate] The fourth: pilot knowledge and training were limited to preserve aircraft commonality.

[measured] The decision not to name or describe MCAS in standard training materials was a product of the same logic that drove the program from the beginning. Disclosing the system meant explaining why it existed. Explaining why it existed meant acknowledging that the MAX handled differently from previous 737s under certain conditions. Acknowledging that meant undermining the commonality claim.

[deliberate] The training omission was not the result of someone deciding that pilot knowledge was unimportant. It was the result of a system in which the commercial argument and the safety argument were never clearly separated — and in which the commercial argument had structural priority.

[deliberate] The fifth: after the first crash, the system was defended as procedure before it was admitted as architecture.

[measured] The response to Lion Air 610 was framed around pilot training and procedure: the existing runaway stabilizer procedure covered the scenario, pilots needed to know to apply it, the airworthiness directive would address the gap. That framing was technically defensible. The procedure did exist. It was theoretically applicable.

[somber] What the framing avoided was the architectural question: whether a system with MCAS's authority, fed by a single sensor, undisclosed to pilots, represented a design that should require a different response than a procedural reminder.

[grave] Ethiopian Airlines 302 answered that question.

[measured] The congressional investigation that followed produced some of the most direct documentation of the failure mode. Internal Boeing communications showed employees expressing concern about MCAS, about pressure to limit simulator training, about the distance between what pilots knew and what the aircraft could do.

[deliberate] One message, from 2017, described the aircraft as designed by clowns supervised by monkeys. It was written by a Boeing employee. It was not shared with the FAA during certification.

[somber] The investigations found systemic failures at Boeing and at the FAA's oversight structure. The delegation of certification authority to Boeing's own engineers, which had been standard practice for decades, had not been matched with sufficient independent review of systems whose scope and authority had changed during development.

[measured] The 737 MAX returned to service in November 2020, after extensive redesign of MCAS, new pilot training requirements that explicitly named and described the system, and revised sensor architecture requiring inputs from both angle-of-attack sensors before MCAS could activate.

[deliberate] The aircraft that returned to service was meaningfully different from the one that had been certified. Which meant the one that had been certified had been meaningfully different from what pilots had been told it was.

[measured] The standard telling of the 737 MAX story reaches for individual villains — executives who prioritized profit, engineers who stayed quiet, regulators who looked away. Those individuals exist in the record, and their choices matter.

[deliberate] But the mechanism that produced two crashes was not a conspiracy. It was a system.

[measured] A commercial constraint became a design requirement. A design requirement shaped what could be disclosed. What could be disclosed shaped what pilots knew. What pilots knew determined what they could do when the system activated. And the system that activated had grown, incrementally, into something that the process evaluating it had not been recalibrated to assess.

[calm] Each step was taken inside a normal process by people who had reviewed the step before it. No single decision looks, in isolation, like the choice to put 346 people at fatal risk. The chain only becomes visible when you look at all of it.

[somber] That is always how these chains work. That is why they are so hard to stop.

[somber] The 737 MAX was certified as a familiar aircraft. It was sold as a familiar aircraft. It was trained as a familiar aircraft. The pilots who flew it in its first year of service had been told, implicitly and explicitly, that what they already knew would be sufficient.

[grave] It was not sufficient.

[measured] What failed was not the sensor, though the sensor failed. What failed was the architecture of a system in which a competitive argument had been allowed to function as a safety argument — in which the demonstration that training costs could be kept low had been allowed to stand in for the demonstration that pilots had been given what they needed.

[deliberate] The system pushed the nose down. The pilots fought it. They had not been given a full, explicit account of the failure mode they were fighting. They had been told there was little new to know.

[grave] The failure was real. The cause chain was longer.

[calm] Next time: another design failure. Another system that taught itself to ignore what it already knew.

--- SCRIPT END ---

--- FACT CHECK START ---
# Episode 7 Fact Check

This memo records the historical verification pass for [Ep7_737-MAX.txt](/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/Ep7_737-MAX.txt).

## Source Set

Primary and official anchors:

- FAA testimony to the Senate aviation subcommittee, April 2, 2019: [Senate Committee on Commerce, Science, & Transportation, Subcommittee on Aviation and Space](https://www.faa.gov/testimony/senate-committee-commerce-science-transportation-subcommittee-aviation-and-space)
- U.S. House Committee on Transportation and Infrastructure final report, September 2020: [The Design, Development & Certification of the Boeing 737 MAX](https://democrats-transportation.house.gov/imo/media/doc/2020.09.15%20FINAL%20737%20MAX%20Report%20for%20Public%20Release.pdf)
- FAA technical review of the return to service: [Preliminary Summary of the FAA’s Review of the Boeing 737 MAX](https://www.faa.gov/sites/faa.gov/files/2021-08/737-MAX-RTS-Preliminary-Summary-v-1.pdf)
- FAA-chartered international certification review: [Boeing 737 MAX Flight Control System: JATR Observations, Findings, and Recommendations](https://www.faa.gov/sites/faa.gov/files/2021-08/Final_JATR_Submittal_to_FAA_Oct_2019.pdf)
- FAA return-to-service update, November 18, 2020: [FAA Updates on Boeing 737 MAX](https://www.faa.gov/newsroom/faa-updates-boeing-737-max-0)
- NTSB comments on the Ethiopian final report, January 24, 2023: [NTSB Publishes Additional Comments on Ethiopia’s Final Report on 737 MAX 8 Accident](https://www.ntsb.gov/news/press-releases/Pages/NR20230124.aspx)
- Boeing chronology PDF: [Boeing History Chronology](https://www.boeing.com/content/dam/boeing/boeingdotcom/history/pdf/Boeing-Chronology.pdf)
- Airbus press release noting the A320neo launch date: [A320neo with CFM LEAP-1A engines receives joint EASA and FAA Airworthiness Type Certification](https://www.airbus.com/en/newsroom/press-releases/2016-05-a320neo-with-cfm-leap-1a-engines-receives-joint-easa-and-faa)

## Framing Note

- The script's core thesis is supported: the 737 MAX crashes were not a one-part story, but a systems story involving design decisions, certification assumptions, disclosure choices, and training economics.
- The factual pass focused on the highest-risk claims: crash chronology, the A320neo competitive timeline, MCAS redesign and authority growth, the single-sensor architecture, what pilots were and were not told before and after Lion Air, certification oversight, and the 2020 return-to-service changes.
- Several lines were tightened where the draft stated timing or pilot-knowledge claims more absolutely than the strongest available sourcing supports.

## Claim Review

### 1. Crash chronology and basic facts

- Claim: Lion Air Flight 610 crashed on October 29, 2018, about 13 minutes after takeoff, killing all 189 people on board.
  Status: supported as written.
  Evidence: [FAA testimony](https://www.faa.gov/testimony/senate-committee-commerce-science-transportation-subcommittee-aviation-and-space), [House report](https://democrats-transportation.house.gov/imo/media/doc/2020.09.15%20FINAL%20737%20MAX%20Report%20for%20Public%20Release.pdf)

- Claim: Ethiopian Airlines Flight 302 crashed on March 10, 2019, six minutes after takeoff, killing all 157 people on board.
  Status: supported as written.
  Evidence: [FAA testimony](https://www.faa.gov/testimony/senate-committee-commerce-science-transportation-subcommittee-aviation-and-space), [FAA return-to-service summary](https://www.faa.gov/sites/faa.gov/files/2021-08/737-MAX-RTS-Preliminary-Summary-v-1.pdf)

### 2. 737 background and competitive timeline

- Claim: the Boeing 737 first flew in 1967.
  Status: supported as written.
  Evidence: [Boeing History Chronology](https://www.boeing.com/content/dam/boeing/boeingdotcom/history/pdf/Boeing-Chronology.pdf)

- Claim: the 737 became the best-selling commercial aircraft in history.
  Status: revised for precision.
  Change: tightened to "the world's bestselling jetliner," which is the wording Boeing itself uses in its chronology. This avoids overstating beyond the source language and avoids the aircraft-family versus aircraft-model ambiguity.
  Evidence: [Boeing History Chronology](https://www.boeing.com/content/dam/boeing/boeingdotcom/history/pdf/Boeing-Chronology.pdf)

- Claim: Boeing's competitive trigger was the A320neo announcement in 2011.
  Status: revised.
  Change: corrected the draft to December 2010. Airbus states the A320neo Family launched on 1 December 2010.
  Evidence: [Airbus press release](https://www.airbus.com/en/newsroom/press-releases/2016-05-a320neo-with-cfm-leap-1a-engines-receives-joint-easa-and-faa)

### 3. MCAS design, redesign, and disclosure

- Claim: MCAS was initially limited, then expanded from 0.6 degrees to 2.5 degrees per activation, while still relying on a single angle-of-attack sensor.
  Status: supported as written.
  Evidence: [House report](https://democrats-transportation.house.gov/imo/media/doc/2020.09.15%20FINAL%20737%20MAX%20Report%20for%20Public%20Release.pdf), [FAA return-to-service summary](https://www.faa.gov/sites/faa.gov/files/2021-08/737-MAX-RTS-Preliminary-Summary-v-1.pdf)

- Claim: Boeing removed MCAS references from pilot-facing manuals and training materials to preserve the commonality story.
  Status: supported after qualification.
  Change: preserved the claim, but the script now anchors the strongest nondisclosure language to the MAX's entry into service. The House report supports removal of MCAS references from the FCOM and training materials, but later post-Lion Air communications did provide some MCAS information to operators.
  Evidence: [House report](https://democrats-transportation.house.gov/imo/media/doc/2020.09.15%20FINAL%20737%20MAX%20Report%20for%20Public%20Release.pdf), [NTSB comments on Ethiopia final report](https://www.ntsb.gov/news/press-releases/Pages/NR20230124.aspx)

### 4. Post-Lion Air response and Ethiopian Flight 302

- Claim: the post-Lion Air emergency directive described a runaway-stabilizer condition and did not name MCAS.
  Status: supported as written.
  Evidence: [House report](https://democrats-transportation.house.gov/imo/media/doc/2020.09.15%20FINAL%20737%20MAX%20Report%20for%20Public%20Release.pdf), [FAA return-to-service summary](https://www.faa.gov/sites/faa.gov/files/2021-08/737-MAX-RTS-Preliminary-Summary-v-1.pdf)

- Claim: the Ethiopian crew "followed the prescribed procedure."
  Status: too categorical as written and revised.
  Change: revised to "attempted the runaway-stabilizer response described after Lion Air." That keeps the substantive point while avoiding a stronger claim than the cleanest official sourcing supports in a short narration.
  Evidence: [FAA testimony](https://www.faa.gov/testimony/senate-committee-commerce-science-transportation-subcommittee-aviation-and-space), [House report](https://democrats-transportation.house.gov/imo/media/doc/2020.09.15%20FINAL%20737%20MAX%20Report%20for%20Public%20Release.pdf), [NTSB comments on Ethiopia final report](https://www.ntsb.gov/news/press-releases/Pages/NR20230124.aspx)

- Claim: pilots simply "did not know its name" and "had not been given the steps to stop it."
  Status: too absolute for a combined Lion Air plus Ethiopian framing and revised.
  Change: replaced with a more defensible formulation: the crews had not been given a full, explicit account of the failure mode they were fighting. That better fits the record after Lion Air, when some MCAS information and emergency guidance had in fact been distributed.
  Evidence: [House report](https://democrats-transportation.house.gov/imo/media/doc/2020.09.15%20FINAL%20737%20MAX%20Report%20for%20Public%20Release.pdf), [NTSB comments on Ethiopia final report](https://www.ntsb.gov/news/press-releases/Pages/NR20230124.aspx)

### 5. Oversight, internal messages, and system framing

- Claim: the "clowns supervised by monkeys" message was from 2016 and written by a Boeing test pilot.
  Status: revised.
  Change: corrected the year to 2017 and loosened the attribution from "test pilot" to "Boeing employee." The official record clearly supports the quote and the 2017 date; the narrower job-title claim is not necessary for the script's point.
  Evidence: [Senate hearing record](https://www.govinfo.gov/content/pkg/CHRG-116shrg52680/pdf/CHRG-116shrg52680.pdf)

- Claim: oversight failures involved both Boeing and the FAA's delegated-certification structure.
  Status: supported as written.
  Evidence: [House report](https://democrats-transportation.house.gov/imo/media/doc/2020.09.15%20FINAL%20737%20MAX%20Report%20for%20Public%20Release.pdf), [JATR report](https://www.faa.gov/sites/faa.gov/files/2021-08/Final_JATR_Submittal_to_FAA_Oct_2019.pdf)

- Claim: MCAS evolved from a relatively benign system into a much more aggressive one, while certification and training assumptions did not fully keep pace.
  Status: supported as written.
  Evidence: [JATR report](https://www.faa.gov/sites/faa.gov/files/2021-08/Final_JATR_Submittal_to_FAA_Oct_2019.pdf), [House report](https://democrats-transportation.house.gov/imo/media/doc/2020.09.15%20FINAL%20737%20MAX%20Report%20for%20Public%20Release.pdf)

### 6. Return to service

- Claim: the 737 MAX returned to service in November 2020 after MCAS redesign, new training, and revised sensor logic requiring both AOA inputs before MCAS can activate.
  Status: supported as written.
  Evidence: [FAA update, November 18, 2020](https://www.faa.gov/newsroom/faa-updates-boeing-737-max-0), [FAA return-to-service summary](https://www.faa.gov/sites/faa.gov/files/2021-08/737-MAX-RTS-Preliminary-Summary-v-1.pdf)

## Material Wording Changes Driven by Sourcing

- Replaced "best-selling commercial aircraft in history" with Boeing's tighter "world's bestselling jetliner" framing.
- Corrected the A320neo competitive trigger from 2011 to a December 2010 launch.
- Qualified the pre-crash pilot-knowledge language so it is explicitly anchored to the MAX's entry into service, not to the post-Lion Air period.
- Replaced the overly categorical ET302 "followed the prescribed procedure" line with "attempted the runaway-stabilizer response described after Lion Air."
- Corrected the "clowns supervised by monkeys" message from 2016 to 2017 and removed the unnecessary "test pilot" attribution.
- Rewrote the closing pilot-knowledge line so it no longer overclaims that no stopping procedure existed after Lion Air.

--- FACT CHECK END ---
