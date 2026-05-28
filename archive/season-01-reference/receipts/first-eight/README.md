# Episodes Cascade Effects

This repo holds episode source material and text provenance for Cascade Effects.

## Shorts Source-Control Policy

- Track text-only Shorts contracts, source scripts, manifests, production notes, review notes, and provenance.
- Do not track generated media, media sidecars, or model assets. WAV, image, video, and model-weight files stay local, generated, or archived outside Git.
- Active Shorts eligibility is controlled by the Agents audio lane registry and the Shorts coordinator gates.
- Diagnostic, comparison, and legacy Shorts lanes must live under `shorts/experiments/` and must not be treated as active production lanes.
- Generated outputs may be referenced by path in provenance notes, but the binary assets themselves are not source artifacts.
