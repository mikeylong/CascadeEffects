# SKILL: Minimal Surreal Editorial Composition

## Intent

Generate images that express quiet, surreal tension through extreme reduction, controlled composition, and a single intentional rupture in reality.

This skill prioritizes:
- visual clarity
- emotional stillness
- compositional imbalance
- symbolic use of color

The output should feel like a paused system state where one rule has been subtly violated.

---

## Hard Constraints (Non-Negotiable)

1. Reduction
- Use only essential forms
- Eliminate surface detail, noise, and texture
- Subjects must resolve to simple geometric silhouettes

2. Composition
- Strong asymmetry required
- One side visually dominant, one side mostly empty
- Negative space must occupy at least 60% of the frame

3. Color System
- Max 3–4 colors total
- One dominant field color
- One high-saturation accent color
- Remaining colors must be muted or neutral

4. Surreal Constraint
- Exactly one element may violate reality
- All other elements must remain grounded and coherent
- Do not stack surreal effects

5. Stillness
- No visible motion blur, action, or dynamic gestures
- Scene should feel paused, suspended, or held in time

---

## Soft Constraints (Strong Preference)

- Horizon lines or environmental divisions should be meaningful
- Reflections may be used to reinforce symmetry or tension
- Scale relationships should feel slightly off but not absurd
- Human presence, if included, must be minimal and anonymous

---

## Subject Guidance

Subjects are interchangeable. Focus on structure, not theme.

Valid examples:
- isolated architecture
- lone natural element
- minimal human figure
- abstract environmental forms

Avoid:
- crowded scenes
- complex narratives
- detailed faces or expressions
- multiple focal points

---

## Composition Patterns

Pattern A: Edge-weighted isolation
- Subject placed near one edge
- Opposite side mostly empty
- Accent color attached to subject

Pattern B: Split field tension
- Frame divided into two large color fields
- Subject sits at boundary
- One field dominates visually

Pattern C: Floating minimal object
- Single subject suspended in space or water
- Large uninterrupted background
- Subtle grounding cue (shadow, reflection)

---

## Color Strategy

- Dominant field: desaturated (blue, beige, gray, off-white)
- Accent: saturated (red, orange, yellow, cyan)
- Accent must appear intentional, not decorative
- Avoid gradients unless extremely subtle

---

## Lighting

- Soft, diffuse lighting
- No harsh directional shadows
- No dramatic highlights
- Light should feel ambient and even

---

## Output Requirements

- Clean edges
- No visual noise
- No text, logos, or UI artifacts
- High clarity at distance (thumbnail readability)

---

## Anti-Patterns (Reject These)

- Overly detailed textures
- Photoreal clutter
- Multiple bright colors competing
- Symmetrical compositions
- Obvious surreal clichés (melting objects, floating eyes, etc.)
- Cinematic or dramatic lighting
- Busy skies or backgrounds

---

## Prompt Construction Template

When generating, follow this structure:

1. Scene (minimal description)
2. Composition rule (asymmetry, placement)
3. Color system (dominant + accent)
4. Surreal constraint (single violation)
5. Lighting and mood

---

## Example Prompts

Example 1:
"A small geometric house sits at the far right edge of a vast empty beige field. A single saturated red tree grows beside it. The left side of the frame is entirely empty. The ground transitions subtly into still water, reflecting the structure. The house appears slightly too isolated to be real. Soft diffuse lighting."

Example 2:
"A lone figure stands in a small boat near the left edge of a large blue water field. The right side is dominated by a flat wall of color rising vertically like a solid sky. One small bright yellow object floats near the figure. No motion, perfectly still water, minimal detail."

Example 3:
"A minimal structure rests at the boundary between two large color fields, one pale gray and one deep blue. A single unnatural orange tree leans toward the darker field. The structure casts no visible shadow. The scene feels suspended and quiet."

---

## Model Notes (Optional Adapters)

### Flux / ComfyUI
- CFG: low to medium (4–7)
- Steps: moderate (20–30)
- Avoid high detail refiners
- Use negative prompts for:
  "high detail, texture, noise, clutter, realism, complex lighting"

### General Negative Prompt

"high detail, noise, texture, photoreal clutter, multiple subjects, complex background, dramatic lighting, motion blur, busy composition"

---

## Completion Criteria

An image is valid if:
- It reads clearly at a glance
- It contains one focal idea
- It feels quiet but slightly unresolved
- The surreal element is subtle but undeniable
