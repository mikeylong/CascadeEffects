# Receipts-Legend Sign-Off Repair - Titanic

Date: 2026-05-19

## Disposition

`pass_script_repair_requires_full_audio_rerender`

The prior terminal line was too vague for a repeatable VO sign-off:

```text
[calm] You already know the disaster. The record shows the mechanism.
```

Titanic now uses the long-form receipts/legend sign-off:

```text
[calm] The legend fades. The receipts remain.
```

This preserves the preceding series motif:

```text
[sorrowful] The failure was real. The cause chain was longer.
```

## Scope

- Change type: cadence and series-signature repair.
- New factual claims: none.
- Fact-check update required: no.
- Source pull sheet update required: no.
- Audio impact: current rendered audio is stale because it contains the old terminal line.
- Required audio action: full rerender with `longform_mike_v1`.

## Script Revision

- Script path: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/Ep8_Titanic.txt`
- Previous script SHA-256: `38056564c66cb5249d02f37dffaf98c4acdea680465e1d9b93d01d06102e38cc`
- Revised script SHA-256: `a5fb122223052b820f7dd832a7f9227db4780f9d4ffd810915e579bef1249dc3`
- Revised word count: `1845`

## Workflow Rule Added

- Sign-off family: `long_form_receipts_legend_signoff_v1`
- Sign-off text: `The legend fades. The receipts remain.`
- Series-bible skill SHA-256 after rule: `95d4c882aba0dd09ce7cb6ce0c72d204801a2ff86ba09c70183880ba7548f4e4`
- First-eight bible SHA-256 after rule: `989d2b9d74d7f3018c5f504fb42f0b53858766e9364ccb372c45de98f399eb51`
- Long-form video skill SHA-256 after rule: `71f29f7c96a479b4816b609bbf995068665aac01445a465d0e4e0f754b884fb6`

## Gate Effect

The package remains at `human_audio_review`. Source-art, visual-system planning, rough assembly, final MP4 render, upload prep, YouTube actions, and public release remain blocked until the rerendered audio receives explicit human `keep`.
