# 737 MAX Frontier Script Critique

## Verdict
`pass_with_tightening`

## Summary
The script is a tight, audio-ready compact long-form essay that delivers a coherent systems-causation thesis without leaning on individual-villain narrative. Factual content aligns with the fact-check memo's revisions (December 2010 A320neo launch, 2017 "clowns" message attributed to a Boeing employee, the revised ET302 framing, and the qualified pilot-knowledge language). Structure is strong: cold open, commonality setup, MCAS introduction and authority creep, two-crash chain, five-condition mechanism analysis, return-to-service, and a closing thesis. Mechanism clarity is the script's strongest asset — the five-condition section explicitly traces *what changed*, *who failed to recognize it*, and *how the system converted blindness into consequence*. Recommended for audio after a small set of pre-render tightenings, primarily around TTS pronunciation aids, the next-episode tease, and one or two cadence smoothings. No factual rewrites are required.

## Required Changes Before Audio
- **Bracketed performance tags must be stripped (or routed to SSML/style cues) before TTS.** Confirm the audio pipeline treats `[calm]`, `[measured]`, `[deliberate]`, `[grave]`, `[somber]` as out-of-band direction. If they are not stripped, TTS will read them aloud verbatim and the render will be unusable.
- **Confirm pronunciation handling for in-line acronyms/foreign terms** before render: `MCAS` (em-cass, one word, not M-C-A-S), `CFM LEAP` (C-F-M LEAP), `A320neo` ("A three-twenty neo"), `FAA` (F-A-A), `Addis Ababa`, `Jakarta`, `Java Sea`. If the voice model defaults to letter-spelling on `MCAS`, that single mispronunciation will recur ~12 times and degrade the entire essay.
- **Verify the closing CTA against the actual next episode.** The line `Next time: another design failure. Another system that taught itself to ignore what it already knew.` is intentionally abstract, but it frames Ep8 as a *system that learned to ignore data*. Confirm Ep8's subject matches that frame; if Ep8 has shifted, replace with a neutral closer (e.g. `Next time: another cascade.`) or remove the tease entirely before audio.

## Suggested Tightening
- Line: `[deliberate] A single sensor. On an aircraft where the system that read that sensor could push the nose toward the ground with enough authority to overpower a crew that did not know what was happening, or was not clearly prepared for the precise sequence of actions needed to stop it.` — the second sentence runs ~45 words and stacks two qualifying clauses. Consider a soft break: `...with enough authority to overpower a crew. A crew that did not know what was happening, or was not clearly prepared for the precise sequence of actions needed to stop it.`
- Line: `[somber] The system was hidden from pilots not through malice, but because its visibility would have cost too much.` — strong line, but consider `because making it visible would have cost too much` to avoid the abstract noun "visibility" reading as flat in TTS.
- Line: `[measured] The congressional investigation that followed produced some of the most direct documentation of the failure mode.` — "documentation of the failure mode" is the most clinical phrase in the script. Consider `produced some of the most direct evidence of how the failure happened` for warmer cadence.
- Line: `[deliberate] The aircraft that returned to service was meaningfully different from the one that had been certified. Which meant the one that had been certified had been meaningfully different from what pilots had been told it was.` — the rhetorical inversion lands, but `Which meant` as a sentence opener is a fragment that some TTS voices will swallow. Optional rephrase: `And that meant the one that had been certified had been meaningfully different from what pilots had been told it was.`
- The `[deliberate]` tag is used ~14 times; consider whether at least two could shift to `[measured]` to avoid uniform delivery in long stretches of the five-conditions section.
- Optional: the phrase `Boeing's primary competitor launched the A320neo program` deliberately avoids naming Airbus. If editorial intent allows naming, `Airbus launched the A320neo program` reads more cleanly and matches the fact-check source. If the omission is deliberate (house style), leave as-is.

## Audio/TTS Notes
- **Performance tags:** five-tag vocabulary is consistent and disciplined. No stray tags, no malformed brackets, no nested tags. Safe for a tag-stripping preprocessor.
- **Numerals:** `189`, `157`, `346`, `2.5`, `0.6`, `1967`, `2018`, `2019`, `2020`, `2010`, `2017` — all in formats most TTS engines handle correctly. The arithmetic `189 + 157 = 346` is correct.
- **Quote handling:** only one direct quotation (`designed by clowns supervised by monkeys`). It is set up cleanly and does not require quotation marks read aloud. Confirm the voice does not insert an audible "quote / unquote."
- **Sentence-final fragments:** several deliberate one-line beats (`So Boeing designed a software system to make it fly like one.`, `Then the design changed.`, `It did not name MCAS.`, `It was not sufficient.`). These read well as written; preserve them.
- **Acronym density:** moderate. `MCAS` is the dominant repeated acronym and must be locked to "em-cass" via lexicon entry.
- **Duplicate/awkward phrasing scan:** no problematic duplicates detected. Repetitions of `What pilots knew` / `What could be disclosed` in the closing paragraph are intentional anaphora and should be preserved.

## Fact-Check Alignment
- All six material wording changes from the fact-check memo are reflected in the script: tightened `world's bestselling jetliner` wording, December 2010 A320neo launch, MCAS authority growth (0.6 → 2.5 degrees), `attempted the runaway-stabilizer response described after Lion Air` for ET302, 2017 date and `Boeing employee` attribution for the "clowns" message, and the qualified `had not been given a full, explicit account of the failure mode` closing.
- The script's `entered service, pilots were not told MCAS existed by name` is correctly anchored to entry into service (not post-Lion Air), matching the memo's required qualification.
- The script avoids overclaiming on certification-delegation specifics; framing aligns with JATR and House report findings.
- No factual claims in the script appear to exceed what the fact-check memo supports. No new claims have been introduced that the memo did not vet.
- One soft note: the line `Internal Boeing communications showed employees expressing concern about MCAS, about pressure to limit simulator training, about the distance between what pilots knew and what the aircraft could do.` is a paraphrase summary rather than a discrete claim — defensible against the House report record, but worth tracking as a paraphrase rather than a sourced quote.

## Gate Reads
- `frontier_model_script_critique_read`: `pass_with_tightening — compact long-form script is structurally and factually sound; aligns with fact-check memo revisions; tightening recommended for TTS robustness and next-episode tease verification, not for accuracy.`
- `required_changes_read`: `three pre-render confirmations required — (1) bracketed performance tags must be stripped or routed to style cues, not spoken; (2) MCAS / CFM LEAP / A320neo / Addis Ababa pronunciations must be locked in the TTS lexicon; (3) the "Next time" closing line must be verified against the actual Ep8 subject or replaced with a neutral closer.`
- `audio_render_recommendation`: `authorize audio render after the three required pre-render confirmations are completed and human approval is recorded against this exact script SHA-256 (3f95aaf72b3144f0c33ee85e77d18140a888ba97c46eb89b0cfaad5c61a7c718). Suggested tightenings are optional and may be deferred to a post-audio pickup pass if any are adopted.`
