# QA Notes

Status: `review_required`
May advance: `false`
YouTube Studio updated: `false`

## Reads

- Official YouTube requirements: pass.
- Channel-branding skill workflow: pass.
- Banner visible strip target: pass.
- Upload wrapper dimensions: pass.
- Banner safe-area/title crop: pass.
- Profile clean-edge/no-alpha source: pass.
- Watermark size and alpha mode: pass.
- Generated title text: pass, no generated title text used.
- Waterfall/liquid read: pass, dry signal traces only.
- Texture-noise read: pass for deterministic review mockup; generated replacement must be re-reviewed.
- JudgmentKit implementation review: pending until the `/brand` page is rendered and reviewed.

## Manual YouTube Studio Checklist

1. Review the banner, profile derivative, and watermark package.
2. Mike explicitly marks selected assets `keep`.
3. Upload channel banner manually in YouTube Studio.
4. Upload profile image manually in YouTube Studio.
5. Upload video watermark manually in YouTube Studio.
6. Record receipts and leave public release/manual visibility decisions outside automation.


## JudgmentKit Review

JudgmentKit MCP was used as requested. The final implementation review remained `deferred_non_pass` because `review_ui_implementation_candidate` did not accept static-enforcement evidence even after explicit candidate packets. The useful checks passed: raw controls, approved primitives, browser QA, modal actions, and static-contract state coverage. This package therefore remains `review_required`, `may_advance: false`, and blocked from any `keep` or YouTube Studio action until Mike reviews it.


## Web Publish Attempt

The `/brand` route builds locally and browser QA passes. Production deployment to Vercel was attempted through normal, archive, and prebuilt flows. All deploy upload attempts failed with Vercel/network `EPIPE` or socket upload errors before a deployment was created. No production deployment was confirmed.
